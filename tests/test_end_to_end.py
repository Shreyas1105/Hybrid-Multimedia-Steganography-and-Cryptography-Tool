# Project Developed by Shreyas M Shenoy
import os
from server.stego.image_stego import embed, extract, capacity_bytes
from server.crypto.aes_gcm import encrypt_bytes, decrypt_bytes
from PIL import Image
import tempfile

def test_image_roundtrip(tmp_path):
    p = tmp_path / "in.png"
    Image.new("RGBA", (128,128), (80,160,200,255)).save(p)
    secret = "ConferenceSecret"
    cap = capacity_bytes(str(p))
    assert len(secret.encode()) <= cap
    enc = encrypt_bytes(secret.encode(), "testpass")
    out = embed(str(p), enc, out_path=str(tmp_path / "out.png"))
    extracted = extract(out)
    dec = decrypt_bytes(extracted, "testpass")
    assert dec.decode() == secret
