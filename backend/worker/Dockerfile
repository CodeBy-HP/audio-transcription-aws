FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake selected Whisper model weights into image for predictable startup.
ARG WHISPER_MODEL_ID=openai/whisper-tiny
ENV WHISPER_MODEL_ID=${WHISPER_MODEL_ID}
ENV WHISPER_MODEL_LOCAL_PATH=/models/whisper-model
RUN python -c "import os; from huggingface_hub import snapshot_download; snapshot_download(repo_id=os.environ['WHISPER_MODEL_ID'], local_dir=os.environ['WHISPER_MODEL_LOCAL_PATH'])"

COPY worker.py .

ENV PYTHONUNBUFFERED=1
CMD ["python", "worker.py"]
