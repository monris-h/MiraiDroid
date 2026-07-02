"""
Tests for src/crypto.py - encryption/decryption roundtrip.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_encrypt_decrypt_roundtrip():
    """Encrypting and decrypting should return the original string."""
    from src.crypto import Crypto
    plaintext = "Hola mundo secreto 123 🔐"
    key = "my-test-key-12345"
    encrypted = Crypto.encrypt(plaintext, key)
    decrypted = Crypto.decrypt(encrypted, key)
    assert decrypted == plaintext, f"Expected '{plaintext}', got '{decrypted}'"


def test_encrypt_produces_different_ciphertexts():
    """Fernet uses a random IV, so two encryptions of the same plaintext differ."""
    from src.crypto import Crypto
    key = "my-test-key"
    a = Crypto.encrypt("hello", key)
    b = Crypto.encrypt("hello", key)
    assert a != b, "Two encryptions of the same plaintext should differ (random IV)"
    # But both should decrypt back to the same plaintext
    assert Crypto.decrypt(a, key) == "hello"
    assert Crypto.decrypt(b, key) == "hello"


def test_decrypt_wrong_key_fails():
    """Decrypting with the wrong key should raise ValueError."""
    from src.crypto import Crypto
    encrypted = Crypto.encrypt("secret", "key1")
    try:
        Crypto.decrypt(encrypted, "key2")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_decrypt_garbage_raises():
    """Decrypting garbage should raise ValueError, not crash."""
    from src.crypto import Crypto
    try:
        Crypto.decrypt("not-a-valid-ciphertext", "anykey")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_unicode_roundtrip():
    """Encryption should handle unicode properly."""
    from src.crypto import Crypto
    text = "日本語 Ñoño 🚀 café"
    key = "k"
    encrypted = Crypto.encrypt(text, key)
    assert Crypto.decrypt(encrypted, key) == text


if __name__ == "__main__":
    test_encrypt_decrypt_roundtrip()
    test_encrypt_produces_different_ciphertexts()
    test_decrypt_wrong_key_fails()
    test_decrypt_garbage_raises()
    test_unicode_roundtrip()
    print("✅ All crypto tests passed")