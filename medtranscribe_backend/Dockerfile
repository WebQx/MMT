FROM python:3.10-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates xz-utils \
    && curl -sSL https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o /tmp/ffmpeg.tar.xz \
    && mkdir -p /tmp/ffmpeg \
    && tar -xJf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg --strip-components=1 \
    && mv /tmp/ffmpeg/ffmpeg /usr/local/bin/ffmpeg \
    && mv /tmp/ffmpeg/ffprobe /usr/local/bin/ffprobe \
    && chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe \
    && rm -rf /tmp/ffmpeg /tmp/ffmpeg.tar.xz \
    && apt-get purge -y --auto-remove curl xz-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

ENV PIP_NO_CACHE_DIR=1
RUN pip install --upgrade pip && pip install --no-cache-dir \
    django==4.2.* gunicorn djangorestframework faster-whisper pymysql

EXPOSE 8000

CMD ["gunicorn", "medtranscribe_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
