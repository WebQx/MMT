FROM python:3.12-slim AS builder
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg build-essential git && rm -rf /var/lib/apt/lists/*
WORKDIR /w
COPY requirements.txt ./
RUN pip install --prefix /install -r requirements.txt && \
    python -c "import whisper; whisper.load_model('base')"

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/* && useradd -m appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 9000
ENV WORKERS="2"
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:9000", "main:app"]