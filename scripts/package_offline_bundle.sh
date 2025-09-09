#!/usr/bin/env bash
set -euo pipefail

# Create a ready-to-distribute tarball containing:
# - saved Docker images (backend)
# - docker-compose.local.yml
# - scripts/local-run.sh
# - web assets (app/build/web)
# - docs/LOCAL_INSTALL.md
# Usage: ./scripts/package_offline_bundle.sh [output_filename]

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT=${1:-"mmt-offline-$(date +%Y%m%d%H%M%S).tar.gz"}
TMPDIR=$(mktemp -d)
DIST_DIR="$TMPDIR/mmt-offline"
mkdir -p "$DIST_DIR/images"

pushd "$ROOT_DIR" >/dev/null

# Build backend image
echo "Building backend image..."
docker build -t webqx/mmt-backend:local-dist ./${ROOT_DIR#/}/backend || docker build -t webqx/mmt-backend:local-dist ./backend

# Build web assets if flutter available
if command -v flutter >/dev/null 2>&1; then
  echo "Building Flutter web assets..."
  pushd app >/dev/null
  flutter pub get
  flutter build web --release --base-href /MMT/
  popd >/dev/null
else
  echo "Flutter not found; expecting existing app/build/web contents."
fi

# Save backend image
echo "Saving backend image to tar..."
docker save -o "$DIST_DIR/images/backend.tar" webqx/mmt-backend:local-dist

# Copy compose, scripts, web assets, docs
cp docker-compose.local.yml "$DIST_DIR/"
cp -r scripts "$DIST_DIR/"
mkdir -p "$DIST_DIR/app/build"
if [ -d app/build/web ]; then
  cp -r app/build/web "$DIST_DIR/app/build/web"
fi
cp -r docs "$DIST_DIR/"

# Create a README in the bundle
cat > "$DIST_DIR/README.txt" <<EOF
MMT Offline Bundle

Contents:
- images/backend.tar: Docker image for the backend
- docker-compose.local.yml: Compose file to run the stack
- scripts/local-run.sh: helper script to load images & start the stack
- app/build/web: prebuilt web assets (optional)
- docs/: documentation and install instructions

To run:
1) Extract the tarball: tar -xzf ${OUT}
2) cd mmt-offline
3) ./scripts/local-run.sh

EOF

# Create tarball
pushd "$TMPDIR" >/dev/null
tar -czf "$ROOT_DIR/$OUT" "$(basename "$DIST_DIR")"
popd >/dev/null

# Clean
rm -rf "$TMPDIR"
popd >/dev/null

echo "Created package: $OUT"
