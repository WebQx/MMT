#!/usr/bin/env bash
set -euo pipefail

# Simple helper to build & run a fully local MMT bundle for offline usage.
# Assumes docker and docker-compose are installed.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Building backend image..."
# If a saved image exists (bundle mode), load it instead of building
if [ -f images/backend.tar ]; then
  echo "Loading backend image from images/backend.tar"
  docker load -i images/backend.tar
else
  docker build -t webqx/mmt-backend:local ./backend
fi

# Build Flutter web if flutter available
if command -v flutter >/dev/null 2>&1; then
  echo "Found flutter; building web assets"
  pushd app
  flutter pub get
  flutter build web --release --base-href /MMT/
  popd
else
  echo "Flutter not found; skipping web build. Ensure built web assets exist at app/build/web"
fi

echo "Starting services with docker-compose.local.yml"
docker compose -f docker-compose.local.yml up -d --build

echo "Local MMT stack is up. Backend: http://localhost:8000  Web: http://localhost:8080"
