
## 📌 Project Overview

The Secure Steganography Tool is a full-stack application designed to securely embed and extract hidden messages within media files such as images and audio. The system combines steganography techniques (LSB encoding) with AES encryption to ensure both concealment and data security.

Users can upload a media file, input a secret message, and generate an encoded file that visually or audibly appears unchanged. The tool also supports extracting hidden messages from previously encoded files.

The backend is built using FastAPI, handling file processing, encryption, and API communication, while the frontend provides a simple and interactive user interface for seamless operation.

# 🔐 Hybrid-Multimedia-Steganography-and-Cryptography-Tool

A full-stack application that allows users to securely hide and extract secret data inside images, audio, and video files using steganography techniques combined with encryption.

---

## 📌 Features

- Hide secret messages inside media files
- Supports:
  - 🖼️ Images (PNG, JPG)
  - 🎵 Audio (WAV)
- AES encryption for secure data embedding
- Extract hidden data from encoded files
- Simple and user-friendly interface
- Download processed files

---

## 🛠️ Tech Stack

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python
- FastAPI
- Uvicorn

### Libraries
- OpenCV
- NumPy
- Pillow
- Wave (for audio processing)

---

## 📂 Project Structure
Hybrid-Multimedia-Steganography-and-Cryptography-Tool/
│
├── frontend/ # UI files
│ ├── index.html
│ ├── styles.css
│ └── app.js
│
├── server/ # Backend logic
│ ├── main.py
│ ├── utils.py
│ ├── stego/
│ │ ├── image_stego.py
│ │ └── audio_stego.py
│
├── requirements.txt
└── README.md


---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository
git clone https://github.com/Shreyas1105/Hybrid-Multimedia-Steganography-and-Cryptography-Tool.git
cd Hybrid-Multimedia-Steganography-and-Cryptography-Tool

### 2️⃣ Setup virtual environment
cd server
python -m venv venv
Activate:
   venv\Scripts\activate(Windows)
   source venv/bin/activate(Mac)

### 3️⃣ Install dependencies
pip install -r requirements.txt

### 4️⃣ Run the backend
cd ..(Go back to root folder)
uvicorn server.main:app --reload

### 5️⃣ Run the frontend
http://127.0.0.1:8000/ui/index.html

📖 How to Use
🔹 Encode Data
Upload a media file (image/audio/video)
Enter the password
Enter secret message
Click Process
Download the encoded file

🔹 Decode Data
Upload encoded file
Enter the password
Click Extract
View hidden message

⚠️ Limitations
Audio processing supports only .wav files
File size affects data capacity
Limited support for video files (future improvement)

###Author -- Shreyas M Shenoy
### Any Queries : shreyasmshenoy11@gmail.com
