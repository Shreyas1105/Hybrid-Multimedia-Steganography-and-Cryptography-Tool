# Secure Stego — Conference-ready implementation

## Summary
Secure Stego is an application demonstrating secure steganography:
- Key derivation: PBKDF2-HMAC-SHA256 (200k iterations).
- Symmetric encryption: AES-GCM (nonce + auth).
- Embedding: LSB for PNG, WAV and MP4 containers.
- Header-based format detection and robust extraction.

## Quick start (local)
1. Clone repo.
2. Create virtualenv and install:
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: .\venv\Scripts\Activate.ps1
   pip install -r server/requirements.txt
