# Project Developed by Shreyas M Shenoy
import os
import shutil
import uuid
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# ---- Utility & crypto imports ----
from server.utils import (
    secure_filename,
    save_upload_file,
    tmp_path,
    is_image,
    is_audio,
    is_video,
    cleanup,
)
from server.crypto.aes_gcm import encrypt_bytes, decrypt_bytes

# ---- Stego modules ----
from server.stego.image_stego import (
    embed as embed_image,
    extract as extract_image,
    capacity_bytes as cap_image,
)
from server.stego.audio_stego import (
    embed as embed_audio,
    extract as extract_audio,
    capacity_bytes as cap_audio,
)
# ✅ Removed cap_video import (not needed)
from server.stego.video_stego import (
    embed as embed_video,
    extract as extract_video,
    capacity_bytes as cap_video,
)

# ---- App setup ----
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(APP_ROOT, "frontend")

app = FastAPI(title="Secure Stego Service")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIR), name="ui")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

DOWNLOADS = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOADS, exist_ok=True)


# ==============================================================
#                       CORE ENDPOINT
# ==============================================================

@app.post("/api/process")
async def process(
    file: UploadFile = File(...),
    password: str = Form(...),
    container: str = Form(...),
    mode: str = Form(...),
    secret_text: str = Form(None),
):
    filename = secure_filename(file.filename or "upload")
    ext = os.path.splitext(filename)[1].lower()
    tmp_in = tmp_path(suffix=ext)
    save_upload_file(file, tmp_in)

    try:
        # =======================================================
        #                     IMAGE CONTAINER
        # =======================================================
        if container == "image":
            if not is_image(tmp_in):
                raise HTTPException(status_code=400, detail="Uploaded file is not an image")

            if mode == "embed":
                if secret_text is None:
                    raise HTTPException(status_code=400, detail="Missing secret_text for embed")

                cap = cap_image(tmp_in)
                payload = secret_text.encode("utf-8")
                if len(payload) > cap:
                    raise HTTPException(
                        status_code=400, detail=f"Payload too large for image: capacity {cap} bytes"
                    )

                enc = encrypt_bytes(payload, password)
                out = embed_image(tmp_in, enc)

                dl_name = filename  # ✅ keep same file name
                dst = os.path.join(DOWNLOADS, dl_name)
                shutil.copy(out, dst)

                return JSONResponse(
                    {"download": True, "url": f"/download/{os.path.basename(dst)}", "filename": dl_name}
                )

            else:  # extract
                enc = extract_image(tmp_in)
                try:
                    pt = decrypt_bytes(enc, password)
                except Exception:
                    raise HTTPException(status_code=400, detail="Decryption failed or wrong password")

                return JSONResponse({"plaintext": pt.decode("utf-8")})

        # =======================================================
        #                     AUDIO CONTAINER
        # =======================================================
        elif container == "audio":
            if not is_audio(tmp_in):
                raise HTTPException(status_code=400, detail="Uploaded file is not audio")

            if mode == "embed":
                if secret_text is None:
                    raise HTTPException(status_code=400, detail="Missing secret_text")

                cap = cap_audio(tmp_in)
                payload = secret_text.encode("utf-8")
                if len(payload) > cap:
                    raise HTTPException(
                        status_code=400, detail=f"Payload too large for audio: capacity {cap} bytes"
                    )

                enc = encrypt_bytes(payload, password)
                out = embed_audio(tmp_in, enc)

                dl_name = filename  # ✅ same as original
                dst = os.path.join(DOWNLOADS, dl_name)
                shutil.copy(out, dst)

                return JSONResponse(
                    {"download": True, "url": f"/download/{os.path.basename(dst)}", "filename": dl_name}
                )

            else:  # extract
                enc = extract_audio(tmp_in)
                try:
                    pt = decrypt_bytes(enc, password)
                except Exception:
                    raise HTTPException(status_code=400, detail="Decryption failed or wrong password")

                return JSONResponse({"plaintext": pt.decode("utf-8")})

        # =======================================================
        #                     VIDEO CONTAINER
        # =======================================================
        elif container == "video":
            if not is_video(tmp_in):
                raise HTTPException(status_code=400, detail="Uploaded file is not video")

            if mode == "embed":
                if secret_text is None:
                    raise HTTPException(status_code=400, detail="Missing secret_text")

                payload = secret_text.encode("utf-8")
                enc = encrypt_bytes(payload, password)
                
                # 'out' is the path to the new ..._stego.avi file
                out = embed_video(tmp_in, enc)

                # 
                # 🩹 --- THIS IS THE FIX ---
                # The download name MUST match the new file's name and extension.
                # The embed_video function creates a "..._stego.avi" file.
                # We must use this name for the download.
                #
                base_name, _ = os.path.splitext(filename)
                dl_name = f"{base_name}_stego.avi"
                
                dst = os.path.join(DOWNLOADS, dl_name)
                # This now correctly copies ..._stego.avi to .../downloads/input_stego.avi
                shutil.copy(out, dst)

                return JSONResponse(
                    {"download": True, "url": f"/download/{os.path.basename(dst)}", "filename": dl_name}
                )

            else:  # extract
                enc = extract_video(tmp_in)
                try:
                    pt = decrypt_bytes(enc, password)
                except Exception:
                    raise HTTPException(status_code=400, detail="Decryption failed or wrong password")

                return JSONResponse({"plaintext": pt.decode("utf-8")})

        else:
            raise HTTPException(status_code=400, detail="Invalid container type")

    finally:
        cleanup(tmp_in)


# ==============================================================
#                       DOWNLOAD ROUTE
# ==============================================================

@app.get("/download/{fname}")
def download_file(fname: str):
    p = os.path.join(DOWNLOADS, fname)
    if not os.path.exists(p):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(p, filename=fname, media_type="application/octet-stream")