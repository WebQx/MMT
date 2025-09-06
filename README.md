# Multilingual Medical Transcription (MMT) - End-to-End Blueprint

Current Version: **v0.3.0**
## UI & Navigation Flow (Flutter)
\n+## Automated Documentation for Medical Transcriptions\n+\n+🔹 **Automated Documentation Features:**\n+\n+• Capture patient-provider conversations and generate complete clinical notes\n+• Document history, examination, assessment, and plan\n+• Create comprehensive notes by the end of each visit\n+• Support both in-clinic and telehealth visits\n*** End Patch

### Pages & Features
- **Login Page:** Modern, centered card layout with logo, email/password fields, sign in, sign up, and guest login options.
- **Passkey Intro Page:** After sign-up, users see a passkey benefits page with clear messaging and a continue button.
- **Onboarding Page:** Account setup with user details (name, organization, role) and stepper/progress indicator.
- **Note Preferences Page:** HPI format selector (Bulleted/Prose) with preview and user name in AppBar.
- **Demo Page:** Microphone selection, welcome message, and button to start demo session.
- **Encounter Page:** Modular layout with left (patient/metadata), middle (SOAP tabs, audio controls), and right (transcript, ICD-10 coding) panels.
- **Upgrade Page:** 1-month free trial, tiered pricing (country-based), and free MUP access. Integrated with FastAPI tier assignment API.

### Navigation
Pages are connected using Flutter's Navigator. Data (e.g., user name, email, tier) is passed between pages as needed. The upgrade page calls the backend to auto-assign tiers using IP geolocation and Keycloak ID.

### Integration Points
- **Backend API:** FastAPI `/assign-tier` endpoint for tier assignment, called from the Upgrade Page.
- **Frontend:** All UI pages use modern Flutter widgets and theming for a consistent experience.

---

## Overview
MMT is a secure, multilingual, healthcare-grade transcription platform supporting real-time, ambient, and offline transcription. It integrates with OpenAI Whisper (cloud), local Whisper, OpenEMR, and supports OAuth2 (Keycloak) and guest login. The app is deployable as a Flutter web app (e.g., Firebase Hosting / GitHub Pages) and as a mobile/desktop app.

---

## What's New (v0.3.0)
Focused release adding clinical usability + transcription flexibility:

* Cloud transcription enhancements: support for `prompt`, `language`, `temperature`, and inline base64 audio (`audio_b64`) in JSON mode.
* Temperature clamping & optional language omission when set to `auto` (tests included).
* Experimental clinical chart templates & parsing endpoints (feature flag) for structured SOAP-style extraction.
* Build slimming: optional heavy ML dependency exclusion via Docker build arg `INCLUDE_ML=0`.
* Unified version bump across backend, Helm chart, and Flutter app.
* Security / infra from earlier releases: JWKS rotation metrics, circuit breaker + fallback persistence, field encryption, rate limit headers, PHI masking (persist + response), Vault RSA key retrieval.

Upgrade Notes:
* Rebuild backend image with tag `0.3.0` (and optionally `--build-arg INCLUDE_ML=0`).
* If using chart templates, set `ENABLE_CHART_TEMPLATES=1` in environment.
* No breaking API changes for existing multipart `/transcribe/cloud/` usage.
* New JSON mode body fields are optional; omit to keep prior behavior.

---

## Architecture

**Frontend:** Flutter (Web, Mobile, Desktop)
- Multilingual UI (Flutter intl)
- OAuth2 (Keycloak) & Guest login
- Passkey onboarding flow
- Account setup and note preferences
- Demo and encounter documentation interfaces
- Upgrade page with tier assignment
- Audio recording, file picker, ambient mode
- Print/email/share results

**Backend:** FastAPI (Python)
- REST API for transcription, login, health, etc.
- Local Whisper for "transcribe later"
- OpenAI Whisper API for real-time/ambient
- RabbitMQ for async integration with OpenEMR
- .env for secrets (OpenAI, Keycloak, OpenEMR, RabbitMQ)

**EHR Integration:**
- OpenEMR via REST API (RabbitMQ consumer)

**Security & Compliance:**
- GDPR, HIPAA, ISO 27701 ready
## Multilingual Medical Transcription (MMT)

Comprehensive, healthcare-grade transcription platform supporting real-time, ambient, and offline modes with OpenAI Whisper (cloud), local Whisper, WebSocket streaming, and OpenEMR integration. Secure by design: OAuth2 (Keycloak), internal JWT sessions, PHI masking, audit logging, metrics, tracing, and optional field-level encryption.

---

### High-Level Architecture

| Layer | Components |
|-------|------------|
| Frontend | Flutter (web/mobile/desktop), OAuth2 & guest auth, audio capture, ambient mode |
| Backend API | FastAPI, unified `/transcribe/`, local & cloud Whisper, WebSocket streaming, idempotent publish, metrics, tracing |
| Async / Messaging | RabbitMQ (transcription events, DLQ, reprocessor, circuit breaker & fallback persistence) |
| Persistence | MySQL (prod) / SQLite (dev), field encryption optional, retention purge job |
| Security | Keycloak external JWT via JWKS, internal JWT rotation (HS256/RSA/Vault), rate limiting, CORS / WS origin allowlist, PHI redaction (persist + response) |
| Observability | Prometheus metrics & recording rules, Grafana dashboard, Sentry (optional), OpenTelemetry traces |
| Compliance | Audit log JSONL, PHI masking toggles, retention, encryption, access role mapping |

---

### Key Features Snapshot
* JWKS-based external JWT verification with background refresh + metrics (`jwks_refresh_total`, `jwks_keys_active`).
* WebSocket origin allowlist & rejection metrics.
* Response PHI masking (`MASK_PHI_IN_RESPONSES`) + persistence PHI masking (`STORE_PHI=false`).
* Circuit breaker & fallback local persistence when queue unavailable.
* Async task executor with bounded queue & metrics.
* Field-level encryption (AES-GCM) with rotation & metrics.
* Vault AppRole RSA key retrieval + renewal for internal JWT signing (optional RSA mode).
* Cloud transcription JSON mode with customizable prompt, language, temperature.
* Clinical chart template listing, prompt generation, and transcript parsing (flagged).

---

### Quick Start (Backend)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in secrets
uvicorn main:app --reload --port 9000
```

### Flutter Web Build & Firebase Hosting
```bash
cd app
flutter build web --release
firebase deploy --only hosting  # assuming firebase.json configured to deploy app/build/web
```
Configure `flutter build web --base-href /` if deploying at root hosting site.

---

### Example Environment (Backend `.env` excerpt)
```env
OPENAI_API_KEY=sk-...
KEYCLOAK_ISSUER=https://keycloak.example/realms/mmt
KEYCLOAK_JWKS_URL=https://keycloak.example/realms/mmt/protocol/openid-connect/certs
GUEST_SECRET=changeme-guest
INTERNAL_JWT_SECRET=long-strong-random-string
RABBITMQ_URL=amqp://user:pass@rabbitmq:5672/
OPENEMR_FHIR_BASE_URL=https://openemr.example
STORE_PHI=true
MASK_PHI_IN_RESPONSES=false
ENABLE_LOCAL_TRANSCRIPTION=true
ENABLE_CLOUD_TRANSCRIPTION=true
```

---

### Deployment (Helm)
See `deploy/helm/mmt`:
```bash
helm dependency update deploy/helm/mmt
helm upgrade --install mmt deploy/helm/mmt \
	--set image.repository=yourrepo/mmt-backend \
	--set image.tag=0.3.0 \
	--set env.INTERNAL_JWT_SECRET=<strong-secret> \
	--set env.KEYCLOAK_ISSUER=... --set env.KEYCLOAK_JWKS_URL=...
```

Add KEDA scaling: `--set keda.enabled=true`.

---

### Security Checklist (Prod)
- [ ] Strong `INTERNAL_JWT_SECRET` (>=32) or RSA mode with Vault / static keys.
- [ ] `ALLOW_GUEST_AUTH=0` (unless demo).
- [ ] `CORS_ALLOW_ORIGINS` & `WEBSOCKET_ALLOWED_ORIGINS` set (no wildcard).
- [ ] Keycloak issuer + JWKS reachable; rotation test passes.
- [ ] Admin drain key set (`ADMIN_API_KEY`).
- [ ] Audit log path or log forwarding configured.
- [ ] Encryption keys & primary ID (if `ENABLE_FIELD_ENCRYPTION=true`).
- [ ] Retention & purge (`RETENTION_DAYS`) agreed & enabled.

### Observability Checklist
- [ ] Metrics scraped & dashboard imported (`grafana_dashboard.json`).
- [ ] Alerts loaded (`alerts_prometheus.yml`, `recording_rules.yaml`).
- [ ] Sentry DSN set (optional) & traces exported.
- [ ] JWKS / breaker / publish failure alerts configured.

---

### Testing
```bash
pytest -q backend/tests
```
Key tests: JWKS rotation, circuit breaker fallback, encryption roundtrip, websocket auth/origin, idempotency, retention, smart auth.

---

### File Highlights
* `backend/main.py` – API, auth, websocket, async executor.
* `backend/metrics.py` – Prometheus metric definitions.
* `backend/audit.py` – Audit + PHI masking helpers.
* `backend/persistence.py` – DB & encryption storage logic.
* `backend/tests/` – Comprehensive backend test suite.
* `deploy/helm/mmt/` – Kubernetes deployment chart.
* `app/lib/` – Flutter client sources.

---

### Contributing
```bash

### 3. Register an API Client
1. Go to **Administration > API Clients**
2. Click **Add API Client**
3. Enter a name (e.g., "MMT Integration") and save
4. Copy the generated API key and secret

---

### License
MIT – see `LICENSE`.

---

### Contact
Info@WebQx.Healthcare | https://github.com/WebQx/MMT
In `/backend/.env`, set:
```
# Use the correct OpenEMR URL for your environment:
# For local Docker: http://localhost:8080/apis/api
# For remote/cloud: http://your-server-ip:8080/apis/api
OPENEMR_API_URL=http://localhost:8080/apis/api
OPENEMR_API_KEY=<your_openemr_api_key>
```

### 5. Test the Integration
1. Start the MMT backend and RabbitMQ consumer
2. Transcribe audio in the MMT app
3. Check OpenEMR for new transcription records
4. Check backend and consumer logs for errors or confirmation

Compatibility note: This repository pins OpenEMR to the `V7_0_3_4` Docker image. Some OpenEMR installs expose the REST API at `/apis/api` while others use `/apis/default/transcriptions`. If you see 404s or unexpected responses, try adjusting `OPENEMR_API_URL` in `/backend/.env` to the correct path for your instance.

Run the RabbitMQ consumer (ensure `.env` is present and RabbitMQ is running):

```bash
python3 backend/openemr_consumer.py
```

---
# Multilingual Medical Transcription (MMT) - End-to-End Blueprint

## Overview
MMT is a secure, multilingual, healthcare-grade transcription platform supporting real-time, ambient, and offline transcription. It integrates with OpenAI Whisper (cloud), local Whisper, OpenEMR, and supports OAuth2 (Keycloak) and guest login. The app is deployable as a Flutter web app (e.g., GitHub Pages) and as a mobile/desktop app.

---

## Architecture

**Frontend:** Flutter (Web, Mobile, Desktop)
- Multilingual UI (Flutter intl)
- OAuth2 (Keycloak) & Guest login
- Audio recording, file picker, ambient mode
- Print/email/share results

**Backend:** FastAPI (Python)
- REST API for transcription, login, health, etc.
- Local Whisper for "transcribe later"
- OpenAI Whisper API for real-time/ambient
- RabbitMQ for async integration with OpenEMR
- .env for secrets (OpenAI, Keycloak, OpenEMR, RabbitMQ)
 - Redis (optional) for rate limiting, session cache, distributed idempotency

**EHR Integration:**
- OpenEMR via REST API (RabbitMQ consumer)

**Security & Compliance:**
- GDPR, HIPAA, ISO 27701 ready
- OAuth2 (Keycloak), HTTPS, audit logging, data minimization

---

## User Flows

### 1. Login
- User chooses: Login with Keycloak (OAuth2) or Continue as Guest
- On success, receives access token (JWT or guest secret)

### 2. Main UI
- Select transcription type:
	- Realtime Transcription (OpenAI Whisper API)
	- Record Now, Transcribe Later (local Whisper)
- Select network mode: Cellular, WiFi, Cloud
- Optionally enable Ambient Mode (continuous listening, OpenAI Whisper API)

### 3. Transcription
- Upload/record audio or enable ambient mode
- For real-time/ambient/cloud: `/transcribe/cloud/` (OpenAI Whisper API)
- For transcribe later: `/transcribe/` (local Whisper)
- Results shown in app, can be printed/emailed
- All results sent to RabbitMQ for OpenEMR integration

### 4. EHR Integration
- RabbitMQ consumer posts transcriptions to OpenEMR API

---

## Security & Compliance
- All secrets in `/backend/.env`
- OAuth2 (Keycloak) for user auth, guest mode for demo/testing
- HTTPS required for all production deployments
- CORS enabled for frontend domain
- Data minimization, audit logging, user data management

---

## Deployment

### Web (Flutter) via Firebase Hosting
1. Create a Firebase project (or use existing) and enable Hosting.
2. Add secrets in GitHub repo settings:
	- `FIREBASE_SERVICE_ACCOUNT`: JSON service account (Base64 or raw) with `Firebase Hosting Admin`.
	- `FIREBASE_PROJECT_ID`: Your project id.
3. Update `.firebaserc` replacing `YOUR_FIREBASE_PROJECT_ID`.
4. (Optional) Adjust `firebase.json` headers or path if you change build dir.
5. Push to `main` (or run workflow manually) to trigger `firebase-web` workflow.

The workflow builds the Flutter web app from `app/` and deploys the contents of `app/build/web` to the live channel.


### Backend (FastAPI)
1. Set up `.env` with all secrets (OpenAI, Keycloak, OpenEMR, RabbitMQ)
2. Run: `uvicorn main:app --reload`
3. Ensure CORS is enabled for your frontend domain
 4. (Optional) Supply `REDIS_URL` to enable distributed idempotency + rate limiting.

### Idempotency & Duplicate Suppression
To avoid double-processing (client retries, network races), the consumer applies best-effort idempotency:

Env flags:
```
ENABLE_IDEMPOTENCY=true
IDEMPOTENCY_CACHE_SIZE=5000        # in-memory fallback size
IDEMPOTENCY_TTL_SECONDS=3600       # TTL for Redis keys
REDIS_URL=redis://redis:6379/0     # enables distributed dedupe
USE_BLOOM_IDEMPOTENCY=false        # enable if RedisBloom module loaded
BLOOM_ERROR_RATE=0.001             # desired false-positive rate
BLOOM_CAPACITY=100000              # expected unique hashes before auto-scaling
```
Behavior:
* If Redis present: SHA-256 hash key stored with NX+EX (atomic first-seen).
* If Redis absent or fails: bounded FIFO in-memory set used (approximate across replicas).
* Hash includes filename + text for determinism.
 * Optional RedisBloom BF.ADD quick membership check reduces memory & key churn; exact SET still guarantees correctness.

Metrics:
```
duplicates_skipped_total
e2e_transcription_latency_seconds_bucket / _count / _sum
```
Prometheus Alerts (Helm): P95 latency, duplicate spike, consumer failure ratio.

### Frontend (Flutter Web)
1. Run: `flutter build web --base-href /MMT/`
2. Deploy `build/web` to GitHub Pages or your web host
3. Set Keycloak redirect URI to your GitHub Pages URL

### OpenEMR & RabbitMQ
1. Deploy OpenEMR and RabbitMQ
2. Configure OpenEMR API key in `.env`
3. Start the RabbitMQ consumer

---

## File Structure (Key Parts)

- `/backend/main.py` - FastAPI backend, all endpoints
- `/backend/.env` - Secrets and API keys
- `/backend/openemr_consumer.py` - RabbitMQ to OpenEMR integration
- `/app/lib/main.dart` - Flutter app main logic
- `/app/pubspec.yaml` - Flutter dependencies
- `/app/web/index.html` - Web entry point

---

## Example .env
```env
OPENAI_API_KEY=sk-...
KEYCLOAK_PUBLIC_KEY=...
KEYCLOAK_ISSUER=...
GUEST_SECRET=guestsecret
OPENEMR_API_KEY=test-api-key
RABBITMQ_URL=amqp://guest:guest@localhost/
```

---

### API Endpoints (Backend)

- `/login/oauth2` – Exchange Keycloak token
- `/login/guest` – Guest token (if allowed)
- `/transcribe/` – Unified local/cloud (multipart). `use_cloud=true` to force cloud.
- `/transcribe/cloud/` – Direct cloud endpoint. Supports:
	* Multipart form (file upload) – legacy behavior.
	* JSON mode:
		```json
		{
			"audio_b64": "<optional base64 wav/mp3/ogg>",
			"prompt": "<custom domain prompt>",
			"language": "en" ,          // or "auto"
			"temperature": 0.2           // clamped (0.0–1.0)
		}
		```
		Provide either `audio_b64` or multipart `file`.
- `/chart/templates` – (flag) list chart template metadata.
- `/chart/prompt/{template}` – (flag) generate structured prompt.
- `/chart/parse` – (flag) extract structured fields from transcript.
- `/upload_chunk/` – Chunked upload for large files.
- `/network_advice/` – Simple bandwidth / advice endpoint.
- `/metrics` – Prometheus metrics.
- `/health` – Liveness / readiness.

---

## Compliance Checklist
- [x] OAuth2 login (Keycloak)
- [x] Guest login
- [x] HTTPS everywhere
- [x] All secrets in .env
- [x] CORS enabled
- [x] Data minimization
- [x] User data management (delete/export)
- [x] Audit logging (backend)
- [x] EHR integration (OpenEMR)

---

### Optional ML Dependencies / Slim Build
Exclude heavy local ML & NLP dependencies (Whisper local, spaCy, etc.):
```
docker build -t mmt-backend:0.3.0-slim --build-arg INCLUDE_ML=0 backend/
```
Default (`INCLUDE_ML=1`) keeps full local transcription capability. Cloud-only deployments can safely disable.

### Clinical Chart Templates (Experimental)
Enable via env: `ENABLE_CHART_TEMPLATES=1`.
Endpoints:
* `GET /chart/templates`
* `GET /chart/prompt/{template}`
* `POST /chart/parse` (body: `{ "text": "...", "template_key": "general_soap" }`)
Disable with `ENABLE_CHART_TEMPLATES=0`.

Use cases:
* Provide dictation guidance prompts in UI.
* Pre-structure transcripts for downstream coding / summarization.

Roadmap:
* Specialty templates (cardiology, pediatrics)
* ML/LLM-assisted extraction
* Confidence scoring per field

## Contact & Support
For issues, open a GitHub issue or contact the maintainers.

---

© 2025 WebQx – Released under MIT License.
