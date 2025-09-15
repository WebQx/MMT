#!/bin/bash

# Railway start script for MMT Backend
# This script starts the FastAPI application using gunicorn with uvicorn workers

set -e

echo "Starting MMT Backend on Railway..."

# Set default port if not provided by Railway
PORT=${PORT:-8000}

# Set default workers if not provided
WORKERS=${WORKERS:-1}

# Set default timeouts
WORKER_TIMEOUT=${WORKER_TIMEOUT:-120}
MAX_REQUESTS=${MAX_REQUESTS:-1000}
MAX_REQUESTS_JITTER=${MAX_REQUESTS_JITTER:-100}

# Production environment configuration
export ENV=${ENV:-prod}
export ENVIRONMENT_NAME=${ENVIRONMENT_NAME:-production}
export DEMO_MODE=${DEMO_MODE:-false}

# Ensure required production secrets are set
if [ "$ENV" = "prod" ] && [ -z "$INTERNAL_JWT_SECRET" ]; then
    echo "Setting default INTERNAL_JWT_SECRET for Railway deployment"
    export INTERNAL_JWT_SECRET="railway_production_jwt_secret_32_chars_long_abcdef1234567890"
fi

# Set RabbitMQ to a local/embedded mode for Railway (or use Railway's addon)
export RABBITMQ_URL=${RABBITMQ_URL:-"amqp://guest:guest@localhost:5672/"}
export ALLOW_GUEST_AUTH=${ALLOW_GUEST_AUTH:-"true"}

echo "Configuration:"
echo "  PORT: $PORT"
echo "  WORKERS: $WORKERS"
echo "  WORKER_TIMEOUT: $WORKER_TIMEOUT"
echo "  MAX_REQUESTS: $MAX_REQUESTS"
echo "  ENV: $ENV"
echo "  DEMO_MODE: $DEMO_MODE"

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