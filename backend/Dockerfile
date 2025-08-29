FROM python:3.12-slim AS builder
ARG INCLUDE_ML=0
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg build-essential git && rm -rf /var/lib/apt/lists/*
WORKDIR /w
COPY requirements.base.txt requirements.base.txt
COPY requirements.ml.txt requirements.ml.txt
COPY requirements.txt requirements.txt
# Install base deps
RUN pip install --prefix /install -r requirements.base.txt \
    && if [ "$INCLUDE_ML" = "1" ]; then pip install --prefix /install -r requirements.ml.txt; fi
# Skip whisper preload to save space; lazy load at runtime if installed.

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