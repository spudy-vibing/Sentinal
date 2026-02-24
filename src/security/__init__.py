"""
SENTINEL SECURITY PACKAGE

Security infrastructure including encryption, Merkle chain audit,
RBAC, and session management.

Usage:
    from src.security import EncryptionService, create_test_service
    from src.security import MerkleChain, get_merkle_chain
    from src.security import get_encryption_service
    from src.security import RBACService, get_rbac_service
    from src.security import SessionManager, get_session_manager
"""

from .encryption import (
    # Service
    EncryptionService,
    FieldEncryptor,
    # Functions
    get_encryption_service,
    create_test_service,
    generate_master_key,
    # Constants
    MASTER_KEY_ENV_VAR,
    MASTER_KEY_SALT_ENV_VAR,
    AES_KEY_SIZE,
    NONCE_SIZE,
    TAG_SIZE,
)

from .merkle import (
    # Classes
    MerkleBlock,
    MerkleChain,
    # Functions
    get_merkle_chain,
    get_persistent_chain,
    verify_chain_file,
)

from .rbac import (
    # Classes
    RBACService,
    AccessDecision,
    # Functions
    get_rbac_service,
    reset_rbac_service,
    # Decorators
    with_session,
    require_permissions,
)

from .sessions import (
    # Classes
    SessionManager,
    SessionMetrics,
    LocalSandbox,
    # Functions
    get_session_manager,
    reset_session_manager,
)

__all__ = [
    # Encryption
    "EncryptionService",
    "FieldEncryptor",
    "get_encryption_service",
    "create_test_service",
    "generate_master_key",
    "MASTER_KEY_ENV_VAR",
    "MASTER_KEY_SALT_ENV_VAR",
    "AES_KEY_SIZE",
    "NONCE_SIZE",
    "TAG_SIZE",
    # Merkle
    "MerkleBlock",
    "MerkleChain",
    "get_merkle_chain",
    "get_persistent_chain",
    "verify_chain_file",
    # RBAC
    "RBACService",
    "AccessDecision",
    "get_rbac_service",
    "reset_rbac_service",
    "with_session",
    "require_permissions",
    # Sessions
    "SessionManager",
    "SessionMetrics",
    "LocalSandbox",
    "get_session_manager",
    "reset_session_manager",
]
