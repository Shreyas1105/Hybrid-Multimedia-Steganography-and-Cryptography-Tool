# Project Developed by Shreyas M Shenoy
import os, tempfile, uuid, mimetypes, shutil
from pathlib import Path
from fastapi import UploadFile

TMP_DIR = os.path.join(os.path.dirname(__file__), "tmp")
os.makedirs(TMP_DIR, exist_ok=True)

def secure_filename(filename: str) -> str:
    name = os.path.basename(filename or "")
    name = name.strip().replace(" ", "_")
    import re
    name = re.sub(r'[^A-Za-z0-9.\-_]+', '', name)
    if not name:
        name = f"file_{uuid.uuid4().hex[:8]}"
    return name

def save_upload_file(upload_file: UploadFile, dest: str):
    Path(os.path.dirname(dest)).mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    try: upload_file.file.seek(0)
    except: pass
    return dest

def tmp_path(suffix=""):
    fd, p = tempfile.mkstemp(suffix=suffix, dir=TMP_DIR)
    os.close(fd)
    return p

def is_image(path: str):
    m,_ = mimetypes.guess_type(path)
    return (m or "").startswith("image")

def is_audio(path: str):
    m,_ = mimetypes.guess_type(path)
    return (m or "").startswith("audio")

def is_video(path: str):
    m,_ = mimetypes.guess_type(path)
    return (m or "").startswith("video")

def cleanup(path: str):
    try: os.remove(path)
    except: pass
