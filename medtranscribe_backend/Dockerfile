FROM python:3.10-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
ENV PIP_NO_CACHE_DIR=1
RUN pip install --upgrade pip && pip install --no-cache-dir \
    django gunicorn djangorestframework faster-whisper pymysql
EXPOSE 8000
CMD ["gunicorn", "medtranscribe_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
