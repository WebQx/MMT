#!/bin/bash

# Railway start script for MMT Backend
# This script starts the FastAPI application using gunicorn with uvicorn workers

set -e

echo "Starting MMT Backend on Railway..."

# Set default port if not provided by Railway
PORT=${PORT:-9000}

# Set default workers if not provided
WORKERS=${WORKERS:-2}

# Set default timeouts
WORKER_TIMEOUT=${WORKER_TIMEOUT:-120}
MAX_REQUESTS=${MAX_REQUESTS:-1000}
MAX_REQUESTS_JITTER=${MAX_REQUESTS_JITTER:-100}

# Production environment configuration
export ENV=${ENV:-prod}
export ENVIRONMENT_NAME=${ENVIRONMENT_NAME:-production}
export DEMO_MODE=${DEMO_MODE:-false}

echo "Configuration:"
echo "  PORT: $PORT"
echo "  WORKERS: $WORKERS"
echo "  WORKER_TIMEOUT: $WORKER_TIMEOUT"
echo "  MAX_REQUESTS: $MAX_REQUESTS"
echo "  ENV: $ENV"
echo "  DEMO_MODE: $DEMO_MODE"

# Validate production requirements
if [ "$ENV" = "prod" ] && [ -z "$INTERNAL_JWT_SECRET" ]; then
    echo "WARNING: INTERNAL_JWT_SECRET not set in production mode"
fi

# Start the application with gunicorn
exec gunicorn \
    -k "uvicorn.workers.UvicornWorker" \
    -w "$WORKERS" \
    -b "0.0.0.0:$PORT" \
    --timeout "$WORKER_TIMEOUT" \
    --max-requests "$MAX_REQUESTS" \
    --max-requests-jitter "$MAX_REQUESTS_JITTER" \
    --preload \
    --access-logfile "-" \
    --error-logfile "-" \
    "main:app"