"""
SENTINEL ENCRYPTION TESTS

Tests for AES-256-GCM envelope encryption.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 1, Security Tests
"""

import pytest
import os
import hashlib

from src.security.encryption import (
    EncryptionService,
    FieldEncryptor,
    create_test_service,
    generate_master_key,
    AES_KEY_SIZE,
    MASTER_KEY_ENV_VAR,
)
from src.contracts.security import EncryptedField


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def encryption_service():
    """Create encryption service with test key."""
    return create_test_service()


@pytest.fixture
def field_encryptor(encryption_service):
    """Create field encryptor for sensitive fields."""
    return FieldEncryptor(
        service=encryption_service,
        sensitive_fields=["ssn", "address", "phone", "email"]
    )


# ═══════════════════════════════════════════════════════════════════════════
# BASIC ENCRYPTION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestEncryptionRoundtrip:
    """Test encryption and decryption."""

    def test_roundtrip_simple_string(self, encryption_service):
        """Test encrypting and decrypting a simple string."""
        plaintext = "Hello, World!"
        encrypted = encryption_service.encrypt_field(plaintext)
        decrypted = encryption_service.decrypt_field(encrypted)
        assert decrypted == plaintext

    def test_roundtrip_unicode(self, encryption_service):
        """Test encrypting unicode content."""
        plaintext = "Unicode: 你好世界 🔐 مرحبا"
        encrypted = encryption_service.encrypt_field(plaintext)
        decrypted = encryption_service.decrypt_field(encrypted)
        assert decrypted == plaintext

    def test_roundtrip_long_string(self, encryption_service):
        """Test encrypting longer content."""
        plaintext = "A" * 10000  # 10KB of data
        encrypted = encryption_service.encrypt_field(plaintext)
        decrypted = encryption_service.decrypt_field(encrypted)
        assert decrypted == plaintext

    def test_roundtrip_special_characters(self, encryption_service):
        """Test encrypting special characters."""
        plaintext = "SSN: 123-45-6789\nAddress: 123 Main St.\n\"Quoted\""
        encrypted = encryption_service.encrypt_field(plaintext)
        decrypted = encryption_service.decrypt_field(encrypted)
        assert decrypted == plaintext

    def test_roundtrip_empty_string(self, encryption_service):
        """Test encrypting empty string."""
        plaintext = ""
        encrypted = encryption_service.encrypt_field(plaintext)
        decrypted = encryption_service.decrypt_field(encrypted)
        assert decrypted == plaintext


class TestEncryptedFieldStructure:
    """Test encrypted field structure."""

    def test_encrypted_field_has_all_components(self, encryption_service):
        """Test that encrypted field has all required components."""
        encrypted = encryption_service.encrypt_field("test data")

        assert isinstance(encrypted, EncryptedField)
        assert encrypted.ciphertext is not None
        assert encrypted.encrypted_dek is not None
        assert encrypted.nonce is not None
        assert encrypted.tag is not None
        assert encrypted.key_version >= 1

    def test_nonce_is_unique(self, encryption_service):
        """Test that each encryption uses a unique nonce."""
        plaintext = "same data"
        encrypted1 = encryption_service.encrypt_field(plaintext)
        encrypted2 = encryption_service.encrypt_field(plaintext)

        # Nonces should be different
        assert encrypted1.nonce != encrypted2.nonce
        # Ciphertext should also be different (due to unique nonce)
        assert encrypted1.ciphertext != encrypted2.ciphertext

    def test_dek_is_unique(self, encryption_service):
        """Test that each encryption uses a unique DEK."""
        plaintext = "same data"
        encrypted1 = encryption_service.encrypt_field(plaintext)
        encrypted2 = encryption_service.encrypt_field(plaintext)

        # Encrypted DEKs should be different
        assert encrypted1.encrypted_dek != encrypted2.encrypted_dek


# ═══════════════════════════════════════════════════════════════════════════
# SECURITY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestSecurityProperties:
    """Test security properties of encryption."""

    def test_wrong_key_fails_decryption(self):
        """Test that wrong key cannot decrypt."""
        # Create two services with different keys
        key1 = hashlib.sha256(b"key1").digest()
        key2 = hashlib.sha256(b"key2").digest()

        service1 = EncryptionService(master_key=key1)
        service2 = EncryptionService(master_key=key2)

        encrypted = service1.encrypt_field("secret data")

        # Service2 should not be able to decrypt
        with pytest.raises(ValueError, match="Failed to decrypt"):
            service2.decrypt_field(encrypted)

    def test_tampered_ciphertext_fails(self, encryption_service):
        """Test that tampered ciphertext is detected."""
        encrypted = encryption_service.encrypt_field("secret data")

        # Tamper with ciphertext
        tampered = EncryptedField(
            ciphertext=bytes([b ^ 0xFF for b in encrypted.ciphertext]),  # Flip bits
            encrypted_dek=encrypted.encrypted_dek,
            nonce=encrypted.nonce,
            tag=encrypted.tag,
            key_version=encrypted.key_version
        )

        with pytest.raises(ValueError, match="Failed to decrypt"):
            encryption_service.decrypt_field(tampered)

    def test_tampered_tag_fails(self, encryption_service):
        """Test that tampered authentication tag is detected."""
        encrypted = encryption_service.encrypt_field("secret data")

        # Tamper with tag
        tampered = EncryptedField(
            ciphertext=encrypted.ciphertext,
            encrypted_dek=encrypted.encrypted_dek,
            nonce=encrypted.nonce,
            tag=bytes([b ^ 0xFF for b in encrypted.tag]),  # Flip bits
            key_version=encrypted.key_version
        )

        with pytest.raises(ValueError, match="Failed to decrypt"):
            encryption_service.decrypt_field(tampered)

    def test_tampered_dek_fails(self, encryption_service):
        """Test that tampered DEK is detected."""
        encrypted = encryption_service.encrypt_field("secret data")

        # Tamper with encrypted DEK
        tampered = EncryptedField(
            ciphertext=encrypted.ciphertext,
            encrypted_dek=bytes([b ^ 0xFF for b in encrypted.encrypted_dek]),
            nonce=encrypted.nonce,
            tag=encrypted.tag,
            key_version=encrypted.key_version
        )

        with pytest.raises(ValueError, match="Failed to decrypt"):
            encryption_service.decrypt_field(tampered)


# ═══════════════════════════════════════════════════════════════════════════
# FIELD ENCRYPTOR TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestFieldEncryptor:
    """Test field-level encryption utility."""

    def test_encrypts_sensitive_fields(self, field_encryptor):
        """Test that sensitive fields are encrypted."""
        data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "address": "123 Main St",
            "portfolio_id": "UHNW_001"
        }

        encrypted = field_encryptor.encrypt_fields(data)

        # Sensitive fields should be encrypted
        assert encrypted["ssn"]["_encrypted"] is True
        assert encrypted["address"]["_encrypted"] is True

        # Non-sensitive fields should be unchanged
        assert encrypted["name"] == "John Doe"
        assert encrypted["portfolio_id"] == "UHNW_001"

    def test_decrypts_sensitive_fields(self, field_encryptor):
        """Test that sensitive fields are decrypted."""
        data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "address": "123 Main St"
        }

        encrypted = field_encryptor.encrypt_fields(data)
        decrypted = field_encryptor.decrypt_fields(encrypted)

        assert decrypted["ssn"] == "123-45-6789"
        assert decrypted["address"] == "123 Main St"
        assert decrypted["name"] == "John Doe"

    def test_handles_nested_dicts(self, field_encryptor):
        """Test encryption of nested dictionaries."""
        data = {
            "client": {
                "name": "John Doe",
                "ssn": "123-45-6789"
            },
            "portfolio_id": "UHNW_001"
        }

        encrypted = field_encryptor.encrypt_fields(data)
        decrypted = field_encryptor.decrypt_fields(encrypted)

        assert decrypted["client"]["ssn"] == "123-45-6789"
        assert decrypted["client"]["name"] == "John Doe"

    def test_handles_non_string_values(self, field_encryptor):
        """Test that non-string values are not encrypted."""
        data = {
            "ssn": "123-45-6789",
            "age": 45,  # int, not a string
            "active": True  # bool
        }

        encrypted = field_encryptor.encrypt_fields(data)

        # SSN should be encrypted
        assert encrypted["ssn"]["_encrypted"] is True
        # Age and active should be unchanged (not strings)
        assert encrypted["age"] == 45
        assert encrypted["active"] is True


# ═══════════════════════════════════════════════════════════════════════════
# KEY GENERATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestKeyGeneration:
    """Test key generation utilities."""

    def test_generate_master_key_length(self):
        """Test that generated key has correct length."""
        key = generate_master_key()
        assert len(key) == 64  # 32 bytes as hex

    def test_generate_master_key_uniqueness(self):
        """Test that generated keys are unique."""
        keys = [generate_master_key() for _ in range(100)]
        assert len(set(keys)) == 100  # All unique

    def test_generate_master_key_is_hex(self):
        """Test that generated key is valid hex."""
        key = generate_master_key()
        bytes.fromhex(key)  # Should not raise


# ═══════════════════════════════════════════════════════════════════════════
# ENVIRONMENT KEY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestEnvironmentKey:
    """Test loading key from environment."""

    def test_missing_env_raises_error(self):
        """Test that missing environment key raises error."""
        # Ensure key is not set
        if MASTER_KEY_ENV_VAR in os.environ:
            del os.environ[MASTER_KEY_ENV_VAR]

        with pytest.raises(RuntimeError, match="Master encryption key not configured"):
            EncryptionService()

    def test_env_key_works(self):
        """Test that environment key is used correctly."""
        # Set test key
        os.environ[MASTER_KEY_ENV_VAR] = generate_master_key()

        try:
            service = EncryptionService()
            encrypted = service.encrypt_field("test")
            decrypted = service.decrypt_field(encrypted)
            assert decrypted == "test"
        finally:
            del os.environ[MASTER_KEY_ENV_VAR]


# ═══════════════════════════════════════════════════════════════════════════
# KEY ROTATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestKeyRotation:
    """Test key rotation functionality."""

    def test_re_encrypt_with_new_key(self):
        """Test re-encrypting data with a new key."""
        old_key = hashlib.sha256(b"old-key").digest()
        new_key = hashlib.sha256(b"new-key").digest()

        old_service = EncryptionService(master_key=old_key)
        new_service = EncryptionService(master_key=new_key)

        plaintext = "sensitive data"

        # Encrypt with old key
        encrypted_old = old_service.encrypt_field(plaintext)

        # Re-encrypt with new key
        encrypted_new = old_service.re_encrypt(encrypted_old, new_service)

        # New service can decrypt
        decrypted = new_service.decrypt_field(encrypted_new)
        assert decrypted == plaintext

        # Old service cannot decrypt new encryption
        with pytest.raises(ValueError):
            old_service.decrypt_field(encrypted_new)

    def test_rotate_key_updates_version(self):
        """Test that rotating key updates version."""
        service = create_test_service()
        initial_version = service._key_version

        new_key = hashlib.sha256(b"new-key").digest()
        service.rotate_key(new_key)

        assert service._key_version == initial_version + 1
