FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/models \
    AUDIO_DIR=/data/audio \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1

# ffmpeg gives torchcodec (used by pyannote) the shared libraries it expects.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only PyTorch keeps the image far smaller than the default CUDA build.
RUN pip install torch==2.14.1 torchaudio==2.11.0 \
    --index-url https://download.pytorch.org/whl/cpu \
    --extra-index-url https://pypi.org/simple

COPY requirements.txt requirements-ml.txt ./
RUN pip install -r requirements.txt -r requirements-ml.txt

COPY app ./app

# Run as a normal user; audio and model cache live on mounted volumes.
RUN useradd --create-home --uid 1000 voiceops \
    && mkdir -p /data/audio /models \
    && chown -R voiceops:voiceops /data /models /app
USER voiceops

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
