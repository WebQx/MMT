#!/usr/bin/env bash
set -euo pipefail

# Download location for the offline sample archive.
# Replace this URL with a permanent release asset or object storage link.
SAMPLE_URL="https://example.com/path/to/mmt-offline-sample.tar.gz"
OUT="mmt-offline-sample.tar.gz"

if [[ -f "$OUT" ]]; then
  echo "File '$OUT' already exists. Remove it first if you want to re-download." >&2
  exit 1
fi

echo "Downloading offline sample (this may be large)..."
curl -fL "$SAMPLE_URL" -o "$OUT"

echo "Download complete: $OUT"
echo "You can extract with: tar xzf $OUT"
