# Project Developed by Shreyas M Shenoy
"""
AES-GCM encryption with PBKDF2 key derivation.
Blob format: SALT(16) || NONCE(12) || CIPHERTEXT
"""
import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SALT_SIZE = 16
NONCE_SIZE = 12
ITERATIONS = 200_000

def derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS, dklen=32)

def encrypt_bytes(plaintext: bytes, password: str) -> bytes:
    salt = os.urandom(SALT_SIZE)
    key = derive_key(password, salt)
    nonce = os.urandom(NONCE_SIZE)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return salt + nonce + ciphertext

def decrypt_bytes(blob: bytes, password: str) -> bytes:
    if len(blob) < (SALT_SIZE + NONCE_SIZE + 16):
        raise ValueError("Blob too small")
    salt = blob[:SALT_SIZE]
    nonce = blob[SALT_SIZE:SALT_SIZE+NONCE_SIZE]
    ciphertext = blob[SALT_SIZE+NONCE_SIZE:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)
