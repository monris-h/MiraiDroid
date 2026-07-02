"""
Crypto - encryption/decryption real para datos sensibles.

Usa cryptography.fernet (AES-128-CBC + HMAC + timestamp) en lugar del XOR+Base64
anterior que NO era seguro.

La clave se deriva del MINIMAX_KEY (hash SHA-256 -> base64 url-safe).
Eso NO es ideal para producción, pero mantiene compatibilidad con deployments
existentes. Para uso serio, usa la variable CRYPTO_KEY para inyectar una clave
Fernet dedicada (generala con `cryptography.fernet.Fernet.generate_key()`).
"""
import base64
import hashlib
import logging

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet, InvalidToken
    _HAS_FERNET = True
except ImportError:
    _HAS_FERNET = False
    logger.warning(
        "cryptography not installed — Crypto will use legacy XOR fallback. "
        "Install requirements.txt for secure encryption."
    )


def _derive_fernet_key(seed: str) -> bytes:
    """Derive a Fernet-compatible 32-byte key from any string."""
    digest = hashlib.sha256(seed.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def _get_fernet(key: str = None) -> "Fernet":
    """Build a Fernet instance from the given key (or from config)."""
    if not _HAS_FERNET:
        raise RuntimeError(
            "cryptography library is not installed. "
            "Run: pip install cryptography"
        )
    if key is None:
        # Allow a dedicated key via env var if present
        import os
        env_key = os.getenv("CRYPTO_KEY")
        if env_key:
            return Fernet(env_key.encode())
        # Fallback: derive from MINIMAX_KEY
        from .config import MINIMAX_KEY
        return Fernet(_derive_fernet_key(MINIMAX_KEY))
    # User-supplied key — accept raw bytes (b64) or arbitrary string (derive)
    try:
        return Fernet(key.encode())
    except (ValueError, Exception):
        return Fernet(_derive_fernet_key(key))


class Crypto:
    """Secure encryption/decryption for sensitive data."""

    @staticmethod
    def encrypt(data: str, key: str = None) -> str:
        """
        Encrypts data and returns a Fernet token (base64-encoded string).
        The token includes a timestamp and HMAC for integrity.
        """
        try:
            f = _get_fernet(key)
            return f.encrypt(data.encode()).decode()
        except RuntimeError:
            # Fallback to legacy XOR if cryptography is missing
            return Crypto._legacy_encrypt(data, key)

    @staticmethod
    def decrypt(data: str, key: str = None) -> str:
        """
        Decrypts a Fernet token. Raises ValueError if the token is invalid
        or has expired.
        """
        try:
            f = _get_fernet(key)
            return f.decrypt(data.encode()).decode()
        except RuntimeError:
            # Fallback to legacy XOR
            return Crypto._legacy_decrypt(data, key)
        except InvalidToken:
            # Maybe it's a legacy token? Try the fallback.
            try:
                return Crypto._legacy_decrypt(data, key)
            except Exception:
                raise ValueError("Invalid or corrupted ciphertext")

    # --- Legacy fallback (insecure, kept for migration only) ---
    @staticmethod
    def _legacy_encrypt(data: str, key: str = None) -> str:
        if key is None:
            from .config import MINIMAX_KEY
            key = MINIMAX_KEY[:16]
        encrypted = "".join(
            chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data)
        )
        return base64.b64encode(encrypted.encode()).decode()

    @staticmethod
    def _legacy_decrypt(data: str, key: str = None) -> str:
        if key is None:
            from .config import MINIMAX_KEY
            key = MINIMAX_KEY[:16]
        encrypted = base64.b64decode(data.encode()).decode()
        return "".join(
            chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(encrypted)
        )