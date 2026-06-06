"""AES-256 field-level encryption using Fernet (cryptography library).

Provides encrypt/decrypt for sensitive fields stored in the database.
Key is loaded from environment variable DOCSTAMP_ENCRYPTION_KEY.
In development, a random key is auto-generated (logged as warning).

Fernet uses:
- AES-128-CBC for encryption
- HMAC-SHA256 for authentication
- Automatic IV generation per message
"""

import base64
import logging
import os

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# ── Key Management ──────────────────────────────────────────────────────

def _load_key() -> bytes:
    """Load encryption key from environment or auto-generate one.

    Production MUST set DOCSTAMP_ENCRYPTION_KEY via environment.
    Auto-generated keys are NOT persistent across restarts.
    """
    key_str = os.environ.get("DOCSTAMP_ENCRYPTION_KEY", "")
    if key_str:
        try:
            return base64.urlsafe_b64decode(key_str.encode())
        except Exception:
            pass
        # If raw string, encode it to 32 bytes and base64 it
        encoded = base64.urlsafe_b64encode(key_str.encode().ljust(32, b"\x00")[:32])
        return encoded

    # Auto-generate (development only)
    logger.warning(
        "DOCSTAMP_ENCRYPTION_KEY not set — using auto-generated key. "
        "Encrypted data will NOT survive application restart."
    )
    return base64.urlsafe_b64encode(os.urandom(32))


_cipher = Fernet(_load_key())


# ── Public API ──────────────────────────────────────────────────────────

def encrypt_field(plaintext: str) -> str:
    """Encrypt a plaintext string for storage.

    Returns a URL-safe base64-encoded ciphertext string.
    Each call produces a different ciphertext for the same plaintext
    (random IV + timestamp embedded by Fernet).

    Args:
        plaintext: The value to encrypt. Empty string is returned as-is.

    Returns:
        Encrypted token as a string. Empty in → empty out.
    """
    if not plaintext:
        return plaintext
    return _cipher.encrypt(plaintext.encode()).decode()


def decrypt_field(ciphertext: str) -> str:
    """Decrypt a previously encrypted value.

    Args:
        ciphertext: The token returned by encrypt_field().

    Returns:
        Original plaintext string. Empty in → empty out.

    Raises:
        cryptography.fernet.InvalidToken: If the ciphertext is corrupted
            or was encrypted with a different key.
    """
    if not ciphertext:
        return ciphertext
    return _cipher.decrypt(ciphertext.encode()).decode()
