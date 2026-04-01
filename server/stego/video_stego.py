# Project Developed by Shreyas M Shenoy
"""
Reliable, optimized video steganography using LSB method.
- Works for MP4 or AVI input; outputs FFV1 AVI (lossless-safe).
- Preserves FPS, resolution, and frame count.
- Debug logs included.
- Header: MAGIC(4) | VERSION(1) | LENGTH(4) | PAYLOAD
"""

import cv2
import os
import numpy as np
import time

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

MAGIC = b"STG0"
VERSION = 1
HEADER_LEN = 4 + 1 + 4  # magic + version + payload length

FAST_MODE = False  # Set True to embed in only the first frames (debug only)

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def _bytes_to_bits(b: bytes) -> np.ndarray:
    """Convert bytes → bit array."""
    return np.unpackbits(np.frombuffer(b, dtype=np.uint8))


def _bits_to_bytes(bits: np.ndarray) -> bytes:
    """Convert bit array → bytes."""
    pad = (-len(bits)) % 8
    if pad:
        bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
    return np.packbits(bits).tobytes()


def build_blob(payload: bytes) -> bytes:
    """Header + payload."""
    return MAGIC + bytes([VERSION]) + len(payload).to_bytes(4, "big") + payload


# ─────────────────────────────────────────────────────────────
# CAPACITY CHECK
# ─────────────────────────────────────────────────────────────

def capacity_bytes(video_path: str) -> int:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Cannot open video.")

    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    bits = frames * w * h * 3
    usable = bits // 8 - HEADER_LEN
    print(f"[INFO] Max payload: {usable} bytes ({usable/1024:.2f} KB).")
    return usable


# ─────────────────────────────────────────────────────────────
# EMBEDDING
# ─────────────────────────────────────────────────────────────

def embed(video_in: str, encrypted_bytes: bytes, out_path: str = None) -> str:
    blob = build_blob(encrypted_bytes)
    bits = _bytes_to_bits(blob)

    cap = cv2.VideoCapture(video_in)
    if not cap.isOpened():
        raise ValueError("Cannot open video file.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # FFV1 = true lossless, LSB safe
    fourcc = cv2.VideoWriter_fourcc(*"FFV1")

    if not out_path:
        base, _ = os.path.splitext(video_in)
        out_path = base + ".stego.avi"

    writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError("VideoWriter failed (codec missing?).")

    print(f"[INFO] Embedding → {out_path}")
    print(f"[INFO] {total_frames} frames, {w}x{h}, {fps:.2f} FPS")

    total_pixels = total_frames * w * h * 3
    if len(bits) > total_pixels:
        raise ValueError("Payload too large.")

    bit_idx = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        flat = frame.reshape(-1)
        chunk = min(len(bits) - bit_idx, flat.size)

        if chunk > 0:
            flat[:chunk] = (flat[:chunk] & 0xFE) | bits[bit_idx:bit_idx + chunk]
            bit_idx += chunk

        writer.write(flat.reshape(frame.shape))
        frame_idx += 1

        if frame_idx % 30 == 0:
            print(f"[INFO] Embedded {frame_idx}/{total_frames} frames...")

        if FAST_MODE and bit_idx >= len(bits):
            print("[DEBUG] FAST_MODE → stopping early.")
            break

    cap.release()
    writer.release()

    print(f"[✓] Embedding done: {bit_idx} bits ({bit_idx//8} bytes).")
    return out_path


# ─────────────────────────────────────────────────────────────
# EXTRACTION (WITH 20-MINUTE DELAY DURING PROCESS)
# ─────────────────────────────────────────────────────────────

def extract(video_in: str) -> bytes:
    cap = cv2.VideoCapture(video_in)
    if not cap.isOpened():
        raise ValueError("Cannot open video file.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[INFO] Extracting from: {video_in} ({total_frames} frames)")

    out_bytes = bytearray()
    bit_buffer = 0
    bit_count = 0

    target_prefix = MAGIC + bytes([VERSION])
    found_at = -1

    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        flat = frame.reshape(-1)

        # LSB → accumulator
        for v in flat:
            bit = v & 1
            bit_buffer = (bit_buffer << 1) | bit
            bit_count += 1
            if bit_count == 8:
                out_bytes.append(bit_buffer)
                bit_buffer = 0
                bit_count = 0

        frame_idx += 1

        # ────────────────────────────────────────────────
        # 20-MINUTE DELAY DURING EXTRACTION
        # Every 30 frames, stall for 20 minutes
        # ────────────────────────────────────────────────
        #if frame_idx % 30 == 0:
         #   print(f"[INFO] Extracted {frame_idx}/{total_frames} frames...")
          #  print("[INFO] Waiting for frames...")
           # time.sleep(10 * 60)
        # ────────────────────────────────────────────────

        # Look for MAGIC header
        if found_at == -1 and len(out_bytes) >= len(target_prefix):
            idx = out_bytes.find(target_prefix)
            if idx != -1:
                found_at = idx
                print(f"[INFO] Header found at byte {found_at}")

        # Header found → check if full payload available
        if found_at != -1:
            if len(out_bytes) >= found_at + HEADER_LEN:
                payload_len = int.from_bytes(out_bytes[found_at + 5: found_at + 9], "big")
                needed = found_at + HEADER_LEN + payload_len

                if len(out_bytes) >= needed:
                    payload = bytes(out_bytes[found_at + HEADER_LEN : needed])
                    cap.release()
                    print(f"[✓] Extraction complete: {len(payload)} bytes.")
                    return payload

    cap.release()

    if found_at == -1:
        raise ValueError("No valid payload (MAGIC missing).")
    else:
        observed = len(out_bytes) - (found_at + HEADER_LEN)
        raise ValueError(f"Incomplete payload (only {observed} bytes).")
