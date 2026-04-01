# Project Developed by Shreyas M Shenoy
"""
Image LSB stego for lossless images (PNG recommended).
Header: MAGIC(4)=b'STG0' + version(1) + payload_len(4 big-endian) then encrypted payload bytes.
Embedding: 1 LSB per R,G,B channel (3 bits per pixel).
"""
from PIL import Image
import numpy as np
import os

MAGIC = b"STG0"
VERSION = 1
HEADER_LEN = 4 + 1 + 4  # magic + version + length

def _bytes_to_bits(b: bytes) -> str:
    return ''.join(f'{x:08b}' for x in b)

def _bits_to_bytes(bits: str) -> bytes:
    if len(bits) % 8 != 0:
        bits = bits + '0' * (8 - (len(bits) % 8))
    return bytes(int(bits[i:i+8],2) for i in range(0,len(bits),8))

def build_blob(payload: bytes) -> bytes:
    l = len(payload)
    header = MAGIC + bytes([VERSION]) + l.to_bytes(4,'big')
    return header + payload

def capacity_bytes(image_path: str) -> int:
    with Image.open(image_path) as im:
        if im.mode not in ("RGB","RGBA"):
            im = im.convert("RGBA")
        w,h = im.size
        # 3 bits per pixel -> capacity bytes:
        cap_bits = w * h * 3
        cap_bytes = cap_bits // 8
        usable = max(0, cap_bytes - HEADER_LEN)
        return usable

def embed(input_path: str, encrypted_bytes: bytes, out_path: str = None) -> str:
    blob = build_blob(encrypted_bytes)
    bits = _bytes_to_bits(blob)
    im = Image.open(input_path)
    if im.mode not in ("RGB","RGBA"):
        im = im.convert("RGBA")
    arr = np.array(im)
    h,w = arr.shape[0], arr.shape[1]
    pixels = arr.reshape(-1, arr.shape[2])  # n x channels
    total_bits = pixels.shape[0]*3
    if len(bits) > total_bits:
        raise ValueError("Payload too large for this image")
    bit_idx = 0
    for i in range(pixels.shape[0]):
        for c in range(3):  # R,G,B
            if bit_idx >= len(bits):
                break
            pixels[i,c] = (int(pixels[i,c]) & ~1) | int(bits[bit_idx])
            bit_idx += 1
        if bit_idx >= len(bits):
            break
    new = pixels.reshape(arr.shape)
    out_img = Image.fromarray(new, mode=im.mode)
    if not out_path:
        base, _ = os.path.splitext(input_path)
        out_path = base + ".stego.png"
    out_img.save(out_path, format="PNG")
    return out_path

def extract(input_path: str) -> bytes:
    im = Image.open(input_path)
    if im.mode not in ("RGB","RGBA"):
        im = im.convert("RGBA")
    arr = np.array(im)
    pixels = arr.reshape(-1, arr.shape[2])
    bits = []
    for i in range(pixels.shape[0]):
        for c in range(3):
            bits.append(str(int(pixels[i,c] & 1)))
    bits_str = ''.join(bits)
    header_bits = bits_str[:HEADER_LEN*8]
    header = _bits_to_bytes(header_bits)
    if len(header) < HEADER_LEN or header[:4] != MAGIC:
        raise ValueError("No valid payload (magic header missing)")
    ver = header[4]
    if ver != VERSION:
        raise ValueError("Unsupported version")
    payload_len = int.from_bytes(header[5:9],'big')
    payload_bits_len = payload_len * 8
    start = HEADER_LEN*8
    payload_bits = bits_str[start:start+payload_bits_len]
    if len(payload_bits) < payload_bits_len:
        raise ValueError("Incomplete payload — image truncated")
    payload = _bits_to_bytes(payload_bits)
    return payload
