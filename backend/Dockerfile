FROM python:3.12-slim AS builder
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# Security: Update packages and install minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg build-essential git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /w
COPY requirements.base.txt requirements.base.txt
COPY requirements.ml.txt requirements.ml.txt
COPY requirements.txt requirements.txt

# Install dependencies with security updates
# Always install ML dependencies in production builds
RUN pip install --upgrade pip setuptools wheel && \
    pip install --prefix /install -r requirements.base.txt && \
    echo "Installing ML dependencies for production..." && \
    pip install --prefix /install -r requirements.ml.txt

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1

# Security: Create non-root user with minimal privileges
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=appuser:appuser . .

# Security: Remove write permissions from application files
RUN chmod -R 755 /app && \
    chmod -R 644 /app/*.py /app/*.txt /app/*.yml /app/*.yaml /app/*.json 2>/dev/null || true

# Create uploads directory with proper permissions
RUN mkdir -p /app/uploads && chown appuser:appuser /app/uploads

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:9000/health/live', timeout=5)"

EXPOSE 9000

# Production configuration
ENV WORKERS="2" \
    WORKER_TIMEOUT="120" \
    MAX_REQUESTS="1000" \
    MAX_REQUESTS_JITTER="100" \
    PRELOAD_APP="true"

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "2", \
     "-b", "0.0.0.0:9000", \
     "--timeout", "120", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--preload", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "main:app"]