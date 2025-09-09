Local Plug & Play Bundle (offline)

Overview

This document shows how to create a self-contained local bundle of the MMT application so users can run the full stack (backend, Redis, RabbitMQ, and the web frontend) locally without internet.

What the bundle contains

- Backend API server (Docker image built from `backend/`)
- Redis
- RabbitMQ
- Web static site served by Nginx (optional; you can run the Flutter app directly)

Requirements

- Docker & Docker Compose (Docker Compose v2 recommended)
- For building the web frontend (optional): Flutter SDK

Quick start (one-liner)

1) Build and run locally

```bash
# from repository root
chmod +x scripts/local-run.sh
./scripts/local-run.sh
```

This script builds the backend image, optionally builds the Flutter web app if `flutter` is available, and starts services via `docker compose -f docker-compose.local.yml up -d --build`.

Access

- Backend API: http://localhost:8000
- Web UI: http://localhost:8080 (if you built web assets or provided `app/build/web`)
- RabbitMQ management UI: http://localhost:15672 (guest/guest)

Notes & customization

- The `docker-compose.local.yml` file maps ports to localhost and uses simple default credentials for RabbitMQ/Redis. For production/local hardened installs change credentials and mount volumes for persistence.
- To include model files for Local Whisper (if you provide them), mount the model directory into the backend container via `volumes:` and set the appropriate env vars.
- This bundle is intended for offline demos or local usage; it is not hardened for production.

Troubleshooting

- If the web UI shows empty content ensure `app/build/web` exists; run `flutter build web` inside `app/`.
- If Docker build fails, inspect `docker logs` and `docker compose` output.

Next steps

- Create platform-specific installers for the standalone Local Whisper app and attach them to GitHub Releases.
- Add a script to package the web assets and backend image (tar + compose) for distribution to air-gapped environments.
 - To create a ready-to-distribute offline tarball run:

```bash
chmod +x scripts/package_offline_bundle.sh
./scripts/package_offline_bundle.sh ./mmt-offline.tar.gz
```

This will produce a tarball (e.g. `mmt-offline-YYYYMMDDHHMMSS.tar.gz`) which contains saved Docker images, the compose file, web assets and the `scripts/local-run.sh` helper. Distribute the tarball; users can extract and run `./scripts/local-run.sh` to load images and start the stack without internet.
