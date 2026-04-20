"""
Crypto - encryption/decryption simple para datos sensibles
"""
import base64

class Crypto:
    @staticmethod
    def encrypt(data: str, key: str = None) -> str:
        if key is None:
            from .config import MINIMAX_KEY
            key = MINIMAX_KEY[:16]
        encrypted = "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))
        return base64.b64encode(encrypted.encode()).decode()

    @staticmethod
    def decrypt(data: str, key: str = None) -> str:
        if key is None:
            from .config import MINIMAX_KEY
            key = MINIMAX_KEY[:16]
        encrypted = base64.b64decode(data.encode()).decode()
        return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(encrypted))