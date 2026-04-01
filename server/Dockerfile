# Project Developed by Shreyas M Shenoy
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libgl1 libglib2.0-0 ffmpeg && rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
