# Deployment Guide (Demo vs Production)

This document explains how to run the stack in two modes:

1. Local / Lightweight Demo (no external dependencies like RabbitMQ, Redis, OpenEMR) – quick evaluation.
2. Production Backend on Railway + Static Frontend Hosting (GitHub Pages / Firebase / any CDN) – scalable deployment.

---
## 1. Architecture Overview

Component | Demo Mode | Production Mode
----------|-----------|----------------
FastAPI Backend (`backend`) | Runs locally in DEMO_MODE with queue + external integrations disabled | Deployed to Railway, full features, external services optional
Frontend (Flutter Web) | Served locally via Docker (port 3000) or static hosting | Static hosting (GitHub Pages / Firebase) points to Railway API
Landing Page (`frontend-landing`) | Provides health dashboard + API switcher | Same; can override API via query string or global config
RabbitMQ | Omitted | Optional (enable for async pipeline)
Redis | Omitted | Optional (rate limiting, caching)
OpenEMR + MariaDB | Omitted | Optional EHR integration profile
SQLite File | Local fallback persistence | Railway ephemeral storage (configure external DB if needed later)

---
## 2. Environment Variable Matrix (Backend)

Category | Key | Demo Default | Production Recommendation
---------|-----|--------------|---------------------------
Mode | DEMO_MODE | 1 | 0
Env Name | ENV / ENVIRONMENT_NAME | dev | prod
Auth | ALLOW_GUEST_AUTH | 1 | 0 (unless public sandbox)
Auth | ALLOW_LOCAL_LOGIN | 1 (implicit) | 0
Internal JWT | INTERNAL_JWT_SECRET | auto weak OK | Strong (>=32 chars) REQUIRED
Transcription | ENABLE_CLOUD_TRANSCRIPTION | 1 | 1 (or 0 if only local)
Transcription | ENABLE_LOCAL_TRANSCRIPTION | 0 | 1 if local model container added
Queue | RABBITMQ_URL | unused | amqp://... (if RabbitMQ enabled)
Rate Limit | RATE_LIMIT_PER_MINUTE | 120 | Tune (e.g. 300)
Security | CORS_ALLOW_ORIGINS | * | Explicit origins list
Telemetry | SENTRY_DSN | null | Set for error tracing
Encryption | ENABLE_FIELD_ENCRYPTION | 0 | 1 (with keys) if PHI in DB
Retention | RETENTION_DAYS | 0 | Policy-based (e.g. 30/90)
Demo | STORE_PHI | true | true/false depending on compliance

See `backend/config.py` for all available keys.

Production template: see `backend/.env.production.example` for a curated, annotated list of recommended variables. Copy it to `.env` (never commit secrets) or load values directly into the Railway dashboard / secret manager.

---
## 3. Railway Backend Deployment

### 3.1 One-Time Setup

1. Create a new Railway project.
2. Add a service from GitHub repository (this repo) selecting the `backend/` directory if prompted (or root + set build).
3. Configure build:
	 - Railway will detect Python. If needed set:
		 - Build Command: `pip install -r backend/requirements.txt`
		 - Start Command: `python -m backend.main`
	 - Or create a `Procfile` (optional): `web: python -m backend.main`
4. Add environment variables (minimum):
	 - `ENV=prod`
	 - `DEMO_MODE=0`
	 - `INTERNAL_JWT_SECRET=<strong-random-32+chars>`
	 - `ALLOW_GUEST_AUTH=0`
	 - `ENABLE_CLOUD_TRANSCRIPTION=1`
	 - (Optional) `SENTRY_DSN`, `RATE_LIMIT_PER_MINUTE`, `CORS_ALLOW_ORIGINS=https://your-frontend.example`
5. (Optional) Add Redis / RabbitMQ via Railway plugins and set `REDIS_URL` / `RABBITMQ_URL`.

### 3.2 GitHub Actions Automation

A workflow (`.github/workflows/railway-backend.yml`) will:
1. Trigger on pushes to `main` (and optionally tags for releases).
2. Install Railway CLI.
3. Deploy the backend service with `railway up` or `railway deploy`.

Required GitHub Secrets:
 - `RAILWAY_TOKEN`: Railway account deploy token.

After first manual deploy, copy the public URL Railway assigns (e.g. `https://mmt-production.up.railway.app`). This becomes the Production API base.

---
## 4. Frontend Hosting & Runtime API Selection

The landing page & Flutter web bundle can run anywhere (GitHub Pages, Firebase, S3+CloudFront). The API base is NOT hard-coded:

Precedence (highest first):
1. URL Query Parameter: `?api=https://your-api.example`
2. Global JS: `window.__MMT_CONFIG = { API_BASE_URL: 'https://your-api.example' }` (inline before `script.js`)
3. Default heuristic (localhost dev, or placeholder prod URL)

Optional convenience key:
`PRODUCTION_API_BASE_URL` – if set in `window.__MMT_CONFIG`, the landing banner will show a "Connect to Production" button when currently pointed at a demo backend (`/demo/status` returns `demo_mode: true`).

The landing script calls `GET /demo/status` to render a banner:
 - Blue: Demo Mode Active
 - Green: Production Backend Connected
 - Red: Unreachable / static only

Users can click "Change API" in the banner to set a new endpoint (persists via URL query update / page reload).

---
## 5. Demo Mode Locally

Run a minimal stack:

```
docker compose -f docker-compose.yml -f docker-compose.override.demo.yml up -d backend frontend-landing
```

Then open http://localhost (landing) or http://localhost:3000 (Flutter app) depending on routing.

Demo mode behavior:
 - Transcriptions stored locally (SQLite) only
 - No RabbitMQ publish
 - OpenEMR, Redis, Django services skipped
 - Safe for quick evaluation / screenshots

---
## 6. Enabling Optional Profiles (Production)

Profiles (compose):
 - `ehr`: OpenEMR + MariaDB
 - `django`: Django backend
 - `queue`: RabbitMQ
 - `cache`: Redis

Example enabling EHR + Queue locally:
```
docker compose --profile ehr --profile queue up -d
```

---
## 7. Updating the Frontend to Use Railway

Once Railway URL is known (e.g. `https://mmt-prod.up.railway.app`):
 - For static hosting: add a tiny `config.js` before main script:
	 ```html
	 <script>window.__MMT_CONFIG={API_BASE_URL:'https://mmt-prod.up.railway.app'};</script>
	 <script src="/script.js" defer></script>
	 ```
 - Or append `?api=https://mmt-prod.up.railway.app` to the landing page URL.

For Flutter web build environments, you can also bake an env value by setting `--dart-define=API_BASE_URL=https://mmt-prod.up.railway.app` during build and reading it in Dart (future enhancement; not yet wired by default).

---
## 8. Security Checklist (Prod Backend)

- [ ] Set `ENV=prod`
- [ ] Strong `INTERNAL_JWT_SECRET` or RSA keys with `USE_RSA_INTERNAL_JWT=1`
- [ ] Restrictive `CORS_ALLOW_ORIGINS`
- [ ] Disable guest + local logins (`ALLOW_GUEST_AUTH=0`, `ALLOW_LOCAL_LOGIN=0`)
- [ ] Consider `RATE_LIMIT_PER_MINUTE` tuning
- [ ] Configure `SENTRY_DSN` and tracing sample rate if needed
- [ ] Decide on `RETENTION_DAYS` and `STORE_PHI`
- [ ] Add encryption keys if storing PHI (`ENABLE_FIELD_ENCRYPTION=1`)

---
## 9. Future Enhancements

Planned (not yet implemented):
 - Dedicated backend Docker image slimming
 - External Postgres/MySQL for production persistence
 - Infrastructure as code (Terraform) for secrets & DNS
 - Blue/Green or canary release strategy on Railway

---
## 10. Troubleshooting

Issue | Cause | Fix
------|-------|----
Banner shows "Backend unreachable" | Wrong API URL / CORS block | Check browser console network tab; add correct origin to CORS_ALLOW_ORIGINS
Demo banner persists in prod | `DEMO_MODE=1` still set | Remove env variable / redeploy
401 / auth errors | Guest auth disabled | Provide valid JWT / enable guest for testing
Large image pull time | No pruning / big layers | Optimize Dockerfile, use multi-stage slimming

---
## 11. Quick Reference

Local demo start:
```
docker compose -f docker-compose.yml -f docker-compose.override.demo.yml up -d backend frontend-landing
```

Railway deploy (manual CLI):
```
railway login
railway link
railway up
```

Override API at runtime:
```
https://your-landing.example?api=https://mmt-prod.up.railway.app
```

---
## 12. Secret Generation & Hardening

Use the helper script to generate strong secrets (JWT, admin key, optional RSA pair, and field encryption keys):

```
python scripts/generate_secrets.py --all
```

Flags:
* `--rsa` – include RSA key pair for `USE_RSA_INTERNAL_JWT=1`
* `--encryption N` – generate N AES-256 keys (`ENCRYPTION_KEYS`, `PRIMARY_ENCRYPTION_KEY_ID`)
* `--all` – shorthand for `--rsa --encryption 2`

Append the output to your production `.env` (never commit real secrets). If using Railway, copy values into its variables UI.

Rotation Strategy:
1. Add a new key as `k3:...` to `ENCRYPTION_KEYS`
2. Deploy, validate decrypt operations still succeed
3. Update `PRIMARY_ENCRYPTION_KEY_ID=k3`
4. (Option) Re-encrypt older records offline / via a migration task

For JWT secret rotation (HS256):
1. Add old secret to `INTERNAL_JWT_OLD_SECRETS` (comma separated)
2. Set new `INTERNAL_JWT_SECRET`
3. Deploy; after TTL expiry of old tokens, remove old secret from list

For RSA rotation: append previous public keys in `INTERNAL_JWT_OLD_PUBLIC_KEYS_PEM` separated by `||`.

---
## 13. Demo → Production Upgrade UX

If a user loads the landing page pointed at a demo backend (`DEMO_MODE=1`), and `window.__MMT_CONFIG.PRODUCTION_API_BASE_URL` is defined, the banner shows a "Connect to Production" button. Clicking it rewrites the URL with `?api=...` pointing at the production backend and reloads.

Setup Example (static host `index.html`):
```html
<script>
	window.__MMT_CONFIG = {
		API_BASE_URL: 'https://demo.mmt.example',
		PRODUCTION_API_BASE_URL: 'https://api.mmt.example'
	};
</script>
<script src="/script.js" defer></script>
```

This allows a frictionless evaluation path: explore demo → upgrade to full capabilities without changing hosting artifacts.

---
## 14. CI Post-Deploy Smoke & Tagging

The Railway deploy workflow performs an optional post-deploy smoke test if `REMOTE_API_BASE_URL` is provided as a repository secret:

Checks:
1. `GET /health/live` returns 200
2. `GET /demo/status` returns `demo_mode: false` (build fails if still true)

Skipping: If the secret is absent, smoke tests are skipped (non-fatal).

Manual Release Tag:
Trigger the workflow with `workflow_dispatch` and supply `release_tag` (e.g. `v0.3.1`) to automatically tag the repository after a successful deployment.

Tag Workflow Path: `.github/workflows/railway-backend.yml`

Recommended Process:
1. Run workflow with proposed tag (e.g. `v0.3.1-rc1`)
2. Verify smoke test pass + remote health workflow green
3. Re-run with final tag (e.g. `v0.3.1`)

Rollback: Push a hotfix commit and redeploy or revert to previous tag; Railway keeps prior build images in its history.

Generated: Keep this file updated when environment variables or deployment workflows change.

---
## 15. Optimizing Deploy Time (Conditional ML Stack)

Large ML dependencies (torch, whisper, spacy, presidio) can add several minutes and hundreds of MB to cold installs. If you do not need local Whisper inference or advanced PII NLP in a given environment (e.g. a lightweight production where only cloud transcription is enabled), you can skip them.

### 15.1 Files

- `backend/requirements.base.txt` – core API + observability
- `backend/requirements.ml.txt` – heavy ML packages (now explicitly pins `torch==2.3.1` to avoid resolver backtracking)
- `backend/requirements.light.txt` – convenience wrapper that only includes base requirements

### 15.2 Workflow Flag

The GitHub Actions workflow `railway-backend.yml` exposes an input:

`include_ml` (default `false`)

Behavior:
- `include_ml = false` → installs `requirements.light.txt`
- `include_ml = true`  → installs full `requirements.txt` (which references base + ml)

### 15.3 Environment Alignment

Ensure these settings match what you install:

| Setting | When to set | Required ML packages |
|---------|-------------|----------------------|
| `ENABLE_LOCAL_TRANSCRIPTION=1` | Need on-box Whisper inference | Install ML stack (`include_ml=true`)
| `ENABLE_LOCAL_TRANSCRIPTION=0` | Rely only on cloud transcription | `include_ml=false` (lighter)
| `ENABLE_CLOUD_TRANSCRIPTION=1` | Uses OpenAI Whisper API | Only base deps (OpenAI client is already in base) |

If you accidentally disable ML install but leave `ENABLE_LOCAL_TRANSCRIPTION=1`, the application will fallback gracefully and log a warning (whisper import will be `None`).

### 15.4 Manual Local Use

Local dev quick start (no ML):
```
pip install -r backend/requirements.light.txt
```

Enable local transcription later:
```
pip install -r backend/requirements.ml.txt
```

### 15.5 Rationale for Torch Pin

Pinning `torch==2.3.1` avoids prolonged pip backtracking across many CUDA build variants that was previously observed, shaving significant time off dependency resolution. Update intentionally and test before changing this version.

### 15.6 Future Improvements

- Pre-build a slim base image and layer ML separately
- Cache wheelhouse for torch + whisper between runs
- Split presidio/spacy into a separate optional NLP feature flag

---

