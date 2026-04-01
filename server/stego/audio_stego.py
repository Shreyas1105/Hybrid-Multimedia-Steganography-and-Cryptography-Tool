# Project Developed by Shreyas M Shenoy
"""
Simple WAV PCM16 LSB stego.
We embed in sample LSBs (least-significant-bit) of PCM16 samples (mono or stereo).
Header same as image: MAGIC + ver + length
Capacity: num_samples * channels bits -> bytes = bits // 8
"""

import wave
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
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def build_blob(payload: bytes) -> bytes:
    """Build header + payload blob."""
    return MAGIC + bytes([VERSION]) + len(payload).to_bytes(4, 'big') + payload


def capacity_bytes(wav_path: str) -> int:
    """Compute usable capacity in bytes for the given WAV."""
    with wave.open(wav_path, 'rb') as wf:
        n_frames = wf.getnframes()
        n_channels = wf.getnchannels()
        bits = n_frames * n_channels
        bytes_capacity = bits // 8
        usable = max(0, bytes_capacity - HEADER_LEN)
        return usable


def embed(wav_in: str, encrypted_bytes: bytes, out_path: str = None) -> str:
    """Embed encrypted bytes inside a 16-bit PCM WAV."""
    blob = build_blob(encrypted_bytes)
    bits = _bytes_to_bits(blob)

    # Read input WAV
    with wave.open(wav_in, 'rb') as wf:
        params = wf.getparams()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        if sampwidth != 2:
            raise ValueError("Only 16-bit PCM WAV supported")
        frames = wf.readframes(wf.getnframes())

    # Convert frames to writable NumPy array
    samples = np.frombuffer(frames, dtype=np.int16).copy()

    total_bits = samples.size
    if len(bits) > total_bits:
        raise ValueError("Payload too large for WAV")

    # Modify LSBs
    bit_idx = 0
    for i in range(samples.size):
        if bit_idx >= len(bits):
            break
        samples[i] = (samples[i] & ~1) | int(bits[bit_idx])
        bit_idx += 1

    # Write output
    out_frames = samples.tobytes()
    if not out_path:
        base, _ = os.path.splitext(wav_in)
        out_path = base + ".stego.wav"
    with wave.open(out_path, 'wb') as wf:
        wf.setparams(params)
        wf.writeframes(out_frames)

    return out_path


def extract(wav_in: str) -> bytes:
    """Extract hidden payload bytes from a stego WAV."""
    with wave.open(wav_in, 'rb') as wf:
        sampwidth = wf.getsampwidth()
        if sampwidth != 2:
            raise ValueError("Only 16-bit PCM WAV supported")
        frames = wf.readframes(wf.getnframes())

    samples = np.frombuffer(frames, dtype=np.int16)
    bits = ''.join(str(int(x & 1)) for x in samples)

    # Header parse
    header_bits = bits[:HEADER_LEN * 8]
    header = _bits_to_bytes(header_bits)
    if len(header) < HEADER_LEN or header[:4] != MAGIC:
        raise ValueError("No valid payload (magic missing)")
    ver = header[4]
    if ver != VERSION:
        raise ValueError("Unsupported version")

    payload_len = int.from_bytes(header[5:9], 'big')
    start = HEADER_LEN * 8
    end = start + payload_len * 8
    payload_bits = bits[start:end]
    if len(payload_bits) < payload_len * 8:
        raise ValueError("Incomplete payload")
    return _bits_to_bytes(payload_bits)
