"""
SENTINEL ENCRYPTION MODULE

AES-256-GCM envelope encryption for field-level data protection.

Envelope encryption pattern:
1. Generate unique DEK (Data Encryption Key) per field
2. Encrypt data with DEK using AES-256-GCM
3. Encrypt DEK with Master Key (from environment)
4. Store: ciphertext + encrypted_dek + nonce + tag

Reference: docs/SECURITY_PRACTICES.md §1.1
Reference: docs/IMPLEMENTATION_PLAN.md Phase 1, Step 1.7
"""

from __future__ import annotations

import os
import secrets
import hashlib
from typing import Optional
from datetime import datetime, timezone

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from src.contracts.interfaces import IEncryption
from src.contracts.security import EncryptedField, EncryptionConfig


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

# Environment variable for master key
MASTER_KEY_ENV_VAR = "SENTINEL_MASTER_KEY"

# Salt for key derivation (can be changed per deployment)
MASTER_KEY_SALT_ENV_VAR = "SENTINEL_KEY_SALT"

# Key sizes
AES_KEY_SIZE = 32  # 256 bits
NONCE_SIZE = 12    # 96 bits (recommended for GCM)
TAG_SIZE = 16      # 128 bits


# ═══════════════════════════════════════════════════════════════════════════
# ENCRYPTION SERVICE
# ═══════════════════════════════════════════════════════════════════════════

class EncryptionService(IEncryption):
    """
    AES-256-GCM envelope encryption service.

    SECURITY:
    - Master key loaded from environment only (never hardcoded)
    - Unique DEK per field (defense in depth)
    - GCM mode provides authenticated encryption
    - Nonce is randomly generated per encryption

    Usage:
        service = EncryptionService()
        encrypted = service.encrypt_field("sensitive data")
        plaintext = service.decrypt_field(encrypted)
    """

    def __init__(
        self,
        config: Optional[EncryptionConfig] = None,
        master_key: Optional[bytes] = None
    ):
        """
        Initialize encryption service.

        Args:
            config: Encryption configuration (uses defaults if not provided)
            master_key: Override master key (for testing only!)
                       In production, always use environment variable
        """
        self.config = config or EncryptionConfig()
        self._key_version = 1

        # Load master key from environment or use provided key
        if master_key is not None:
            self._master_key = master_key
        else:
            self._master_key = self._load_master_key()

    def _load_master_key(self) -> bytes:
        """
        Load and derive master key from environment.

        SECURITY: Master key is derived using PBKDF2-SHA256 for
        additional protection against brute force attacks.

        Raises:
            RuntimeError: If master key not configured
        """
        raw_key = os.environ.get(MASTER_KEY_ENV_VAR)

        if not raw_key:
            raise RuntimeError(
                f"Master encryption key not configured. "
                f"Set {MASTER_KEY_ENV_VAR} environment variable. "
                f"Generate a key with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )

        # Get salt from environment or use default
        salt = os.environ.get(MASTER_KEY_SALT_ENV_VAR, "sentinel-default-salt-v1")

        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=AES_KEY_SIZE,
            salt=salt.encode(),
            iterations=self.config.kdf_iterations,
            backend=default_backend()
        )

        return kdf.derive(raw_key.encode())

    def encrypt_field(self, plaintext: str) -> EncryptedField:
        """
        Encrypt a field using envelope encryption.

        Steps:
        1. Generate random DEK
        2. Generate random nonce
        3. Encrypt plaintext with DEK (AES-256-GCM)
        4. Encrypt DEK with master key

        Args:
            plaintext: String to encrypt

        Returns:
            EncryptedField containing ciphertext and encrypted DEK
        """
        # Generate unique DEK for this field
        dek = secrets.token_bytes(AES_KEY_SIZE)

        # Generate nonce
        nonce = secrets.token_bytes(NONCE_SIZE)

        # Encrypt plaintext with DEK
        aesgcm = AESGCM(dek)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

        # GCM mode appends tag to ciphertext
        # Split them for storage
        actual_ciphertext = ciphertext[:-TAG_SIZE]
        tag = ciphertext[-TAG_SIZE:]

        # Encrypt DEK with master key
        dek_nonce = secrets.token_bytes(NONCE_SIZE)
        master_aesgcm = AESGCM(self._master_key)
        encrypted_dek_with_tag = master_aesgcm.encrypt(dek_nonce, dek, None)

        # Prepend DEK nonce to encrypted DEK for decryption
        encrypted_dek = dek_nonce + encrypted_dek_with_tag

        return EncryptedField(
            ciphertext=actual_ciphertext,
            encrypted_dek=encrypted_dek,
            nonce=nonce,
            tag=tag,
            key_version=self._key_version
        )

    def decrypt_field(self, encrypted: EncryptedField) -> str:
        """
        Decrypt an envelope-encrypted field.

        Steps:
        1. Decrypt DEK with master key
        2. Reconstruct ciphertext + tag
        3. Decrypt with DEK (AES-256-GCM)

        Args:
            encrypted: EncryptedField to decrypt

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If decryption fails (tampered or wrong key)
        """
        # Extract DEK nonce from encrypted_dek
        dek_nonce = encrypted.encrypted_dek[:NONCE_SIZE]
        encrypted_dek_data = encrypted.encrypted_dek[NONCE_SIZE:]

        # Decrypt DEK with master key
        master_aesgcm = AESGCM(self._master_key)
        try:
            dek = master_aesgcm.decrypt(dek_nonce, encrypted_dek_data, None)
        except Exception as e:
            raise ValueError(f"Failed to decrypt DEK: {e}") from e

        # Reconstruct ciphertext + tag
        ciphertext_with_tag = encrypted.ciphertext + encrypted.tag

        # Decrypt plaintext with DEK
        aesgcm = AESGCM(dek)
        try:
            plaintext = aesgcm.decrypt(encrypted.nonce, ciphertext_with_tag, None)
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {e}") from e

        return plaintext.decode()

    def rotate_key(self, new_master_key: bytes) -> None:
        """
        Rotate master key.

        SECURITY: Key rotation should re-encrypt all existing data.
        This method only updates the service's key for new encryptions.

        Args:
            new_master_key: New 32-byte master key
        """
        if len(new_master_key) != AES_KEY_SIZE:
            raise ValueError(f"Master key must be {AES_KEY_SIZE} bytes")

        self._master_key = new_master_key
        self._key_version += 1

    def re_encrypt(
        self,
        encrypted: EncryptedField,
        new_service: "EncryptionService"
    ) -> EncryptedField:
        """
        Re-encrypt a field with a new master key.

        Used during key rotation to migrate existing data.

        Args:
            encrypted: Field encrypted with current key
            new_service: Service with new master key

        Returns:
            Field re-encrypted with new key
        """
        plaintext = self.decrypt_field(encrypted)
        return new_service.encrypt_field(plaintext)


# ═══════════════════════════════════════════════════════════════════════════
# FIELD ENCRYPTOR UTILITY
# ═══════════════════════════════════════════════════════════════════════════

class FieldEncryptor:
    """
    Utility for encrypting/decrypting specific fields in dictionaries.

    Usage:
        encryptor = FieldEncryptor(service, ["ssn", "address", "phone"])
        encrypted_data = encryptor.encrypt_fields(client_data)
        decrypted_data = encryptor.decrypt_fields(encrypted_data)
    """

    def __init__(
        self,
        service: EncryptionService,
        sensitive_fields: list[str]
    ):
        """
        Initialize field encryptor.

        Args:
            service: Encryption service instance
            sensitive_fields: List of field names to encrypt
        """
        self.service = service
        self.sensitive_fields = set(sensitive_fields)

    def encrypt_fields(self, data: dict) -> dict:
        """
        Encrypt sensitive fields in a dictionary.

        Args:
            data: Dictionary with fields to encrypt

        Returns:
            Dictionary with sensitive fields encrypted
        """
        result = {}

        for key, value in data.items():
            if key in self.sensitive_fields and isinstance(value, str):
                encrypted = self.service.encrypt_field(value)
                result[key] = {
                    "_encrypted": True,
                    "ciphertext": encrypted.ciphertext.hex(),
                    "encrypted_dek": encrypted.encrypted_dek.hex(),
                    "nonce": encrypted.nonce.hex(),
                    "tag": encrypted.tag.hex(),
                    "key_version": encrypted.key_version
                }
            elif isinstance(value, dict):
                result[key] = self.encrypt_fields(value)
            else:
                result[key] = value

        return result

    def decrypt_fields(self, data: dict) -> dict:
        """
        Decrypt sensitive fields in a dictionary.

        Args:
            data: Dictionary with encrypted fields

        Returns:
            Dictionary with sensitive fields decrypted
        """
        result = {}

        for key, value in data.items():
            if isinstance(value, dict):
                if value.get("_encrypted"):
                    encrypted = EncryptedField(
                        ciphertext=bytes.fromhex(value["ciphertext"]),
                        encrypted_dek=bytes.fromhex(value["encrypted_dek"]),
                        nonce=bytes.fromhex(value["nonce"]),
                        tag=bytes.fromhex(value["tag"]),
                        key_version=value.get("key_version", 1)
                    )
                    result[key] = self.service.decrypt_field(encrypted)
                else:
                    result[key] = self.decrypt_fields(value)
            else:
                result[key] = value

        return result


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get or create default encryption service."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def create_test_service() -> EncryptionService:
    """
    Create encryption service for testing.

    SECURITY: Only use in tests! Uses a fixed test key.
    """
    test_key = hashlib.sha256(b"sentinel-test-key-do-not-use-in-production").digest()
    return EncryptionService(master_key=test_key)


def generate_master_key() -> str:
    """
    Generate a new master key for configuration.

    Returns:
        64-character hex string (32 bytes)
    """
    return secrets.token_hex(32)
