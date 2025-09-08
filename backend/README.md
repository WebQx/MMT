# MMT Transcription Backend

Features implemented:

- Local Whisper transcription (`/transcribe/local/` and unified `/transcribe/`)
- Cloud OpenAI Whisper transcription (`/transcribe/cloud/` or `/transcribe/?use_cloud=true`)
- Chunked upload (`/upload_chunk/`)
- Prototype WebSocket streaming (`/ws/transcribe`)
- Unified `/transcribe/` endpoint:
    - Multipart with `file`: local or cloud (set `use_cloud=true`).
    - JSON ambient: `{ "text": "already transcribed", "mode": "ambient" }` → direct publish (no model).
- RabbitMQ publishing of final transcripts
- Modular config (`config.py`), services, and post-processing
- OpenEMR FHIR DocumentReference publishing (password grant) via consumer if FHIR env vars set
- Structured JSON logging (structlog) + correlation IDs
- Basic entity extraction & summarization enrichment in consumer
 - Prometheus metrics endpoint `/metrics` & optional partial streaming (`ENABLE_PARTIAL_STREAMING=1`)
 - Persistent transcript storage (MySQL via TRANSCRIPTS_DB_* env or fallback SQLite)
 - Rate limiting middleware & basic source tagging
- Rate limit response headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`)
 - DLQ publishing for failed consumer messages (`openemr_transcriptions_dlq`)
- DLQ reprocessor service (`dlq_reprocessor.py`) with exponential backoff and Prometheus metrics
 - Multi-stage Dockerfile with pre-fetched Whisper model & non-root user
 - SMART-on-FHIR authorization_code flow endpoints (`/auth/fhir/authorize` + `/auth/fhir/callback`) issuing internal JWT bound to FHIR access token session
 - Guest auth disabled by default in production (`ENV=prod` or `ALLOW_GUEST_AUTH=0`)
 - Transcription endpoints require `user/DocumentReference.write` scope (no guest write)
 - Internal JWT secret rotates on restart if not set via env
 - TLS: To enable HTTPS, set `UVICORN_SSL_KEYFILE` and `UVICORN_SSL_CERTFILE` env vars and run with `--ssl-keyfile`/`--ssl-certfile` (see below)

### Production Hardening (In Progress)
- DLQ reprocessor with exponential backoff & Prometheus metrics.
- Audit logging (JSONL) optional via `AUDIT_LOG_FILE` env.
- PHI masking toggle (`STORE_PHI=false`) masks persisted text/summary.
- Data retention config placeholder (`RETENTION_DAYS`). (Implement purge job next.)
- Queue publish error handling returns 503 instead of silent loss.
 - OpenTelemetry tracing with W3C propagation across RabbitMQ + trace IDs & span IDs embedded in logs.
 - KEDA-based autoscaling (RabbitMQ queue length) optional via Helm `keda.enabled=true`.
 - Vault AppRole authentication for automated RSA internal JWT key retrieval & token renewal.
 - Prometheus recording rules & Grafana dashboard JSON for latency, queue depth, and Vault health.
- Async transcription task offload with bounded worker pool & queue (metrics: async_tasks_started_total, async_tasks_completed_total, async_tasks_failed_total, async_task_duration_seconds, async_task_queue_size, async_tasks_purged_total)
- Circuit breaker on publish with metrics breaker_open_total, breaker_fallback_persist_total
- Drain mode metric drain_start_total and 503 rejection of new transcription requests while draining
 - Optional clinical chart templates & structured parsing endpoints (enable with `ENABLE_CHART_TEMPLATES=1`)

### Clinical Chart Templates & Structured Notes

Feature flag: `ENABLE_CHART_TEMPLATES=1`

Endpoints:

1. `GET /chart/templates` — list available templates (initial: `general_soap`).
2. `GET /chart/prompt/{template_key}` — returns an instructional prompt guiding high‑quality structured capture (useful for front-end UI hints or AI augmentation).
3. `POST /chart/parse` — naive rule-based extraction of fields from a raw transcript body.

Template structure (example `general_soap`):

```
{
    "key": "general_soap",
    "sections": [
        {"key":"subjective","fields":[{"key":"chief_complaint"}, {"key":"hpi"}, {"key":"ros"}]},
        {"key":"objective","fields":[{"key":"vitals"}, {"key":"exam"}]},
        {"key":"assessment","fields":[{"key":"impression"}]},
        {"key":"plan","fields":[{"key":"tests"},{"key":"treatment"},{"key":"follow_up"}]}
    ]
}
```

Example prompt retrieval:
```
curl -s http://localhost:9000/chart/prompt/general_soap | jq -r .prompt
```

Example parse (guest token in dev):
```
TOKEN=$GUEST_SECRET
curl -s -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    -d '{"text":"Chief Complaint: cough 3 days\nHPI: Dry cough worse at night","template_key":"general_soap"}' \
    http://localhost:9000/chart/parse | jq
```

Output (simplified):
```
{
    "template": "general_soap",
    "fields": {
        "chief_complaint": "cough 3 days",
        "hpi": "Dry cough worse at night",
        "ros": null,
        "vitals": null,
        "exam": null,
        "impression": null,
        "tests": null,
        "treatment": null,
        "follow_up": null
    }
}
```

Notes / roadmap:
- Current parser is heuristic (header: value lines). Upgrade path: embedding similarity, NER, or LLM extraction.
- Add additional specialty templates (e.g., urgent care, cardiology) by registering in `chart_templates.py`.
- Frontend can pre-load prompt to guide dictation UI or provide inline hints.

### Helm Deployment
Helm chart located at `deploy/helm/mmt`.

Basic install (includes Bitnami RabbitMQ & Redis if enabled):
```
helm dependency update deploy/helm/mmt
helm install mmt deploy/helm/mmt \
    --set image.repository=yourrepo/mmt-backend --set image.tag=latest \
    --set env.RETENTION_DAYS=30
```

Retention purge runs daily at 02:00 if `RETENTION_DAYS>0` (CronJob) and DLQ reprocessor runs every 10 minutes.

To disable bundled RabbitMQ/Redis (use external):
```
helm install mmt deploy/helm/mmt --set rabbitmq.enabled=false --set redis.enabled=false \
    --set rabbitmq.url=amqp://user:pass@external-rmq:5672/ --set redis.url=redis://external-redis:6379/0
```

Ingress example:
```
helm upgrade --install mmt deploy/helm/mmt \
    --set ingress.enabled=true \
    --set ingress.hosts[0].host=transcribe.example.com \
    --set ingress.tls[0].hosts[0]=transcribe.example.com \
    --set ingress.tls[0].secretName=mmt-tls
```

Sealed Secret example (Bitnami controller):
```
kubectl create secret generic transcripts-db --dry-run=client -o yaml \
    --from-literal=host=db.example --from-literal=user=mmt --from-literal=password='S3cret!' | \
    kubeseal --format yaml > transcripts-db-sealed.yaml
kubectl apply -f transcripts-db-sealed.yaml
```

### TLS/HTTPS

To run with HTTPS in production:

```
export UVICORN_SSL_KEYFILE=/path/to/key.pem
export UVICORN_SSL_CERTFILE=/path/to/cert.pem
uvicorn main:app --host 0.0.0.0 --port 9000 --ssl-keyfile $UVICORN_SSL_KEYFILE --ssl-certfile $UVICORN_SSL_CERTFILE
```

### Persistence Environment Variables

```
### DLQ Reprocessor

Run the DLQ reprocessor (in separate process or container):

```
python dlq_reprocessor.py
```

Environment variables you can override:

- `DLQ_QUEUE` (default `openemr_transcriptions_dlq`)
- `MAIN_QUEUE` (default `openemr_transcriptions`)
- `MAX_REPROCESS_ATTEMPTS` (default 5)
- `BACKOFF_BASE_SECONDS` (default 5)

### Prometheus Alert Rules

See `alerts_prometheus.yml` for suggested alerting (DLQ ingress, reprocessor failures, lack of success).

### CI / Quality Gates (proposed)

Suggested steps for a CI pipeline (GitHub Actions / GitLab):

```
pip install -r backend/requirements.txt
flake8 backend
mypy backend --ignore-missing-imports
pytest -q backend/tests
safety check -r backend/requirements.txt
```

Container scanning can be added via Trivy: `trivy image your-registry/mmt-backend:TAG`.

### Autoscaling (HPA vs KEDA)

Two options exist:

1. Horizontal Pod Autoscaler (HPA) using CPU/memory or custom metrics (template: `templates/hpa.yaml`).
2. KEDA ScaledObject (preferred for queue-driven workloads) using RabbitMQ queue length trigger (`templates/keda-scaledobject.yaml`).

Enable KEDA (disables traditional HPA to avoid conflicts):
```
helm upgrade --install mmt deploy/helm/mmt \
    --set keda.enabled=true \
    --set keda.rabbitmq.queueName=openemr_transcriptions \
    --set keda.rabbitmq.hostFromSecret=rabbitmq-credentials \
    --set keda.rabbitmq.hostFromSecretKey=connection
```

Key tunables (values.yaml):
- `keda.pollingInterval` (seconds between metric checks)
- `keda.cooldownPeriod` (seconds to scale to zero after idle)
- `keda.minReplicaCount` / `keda.maxReplicaCount`
- `keda.rabbitmq.queueLength` (target messages per replica)

### Vault AppRole & RSA Key Rotation

Set the following env vars (or Helm values under `env`):

```
VAULT_ADDR=https://vault.example.com
VAULT_ROLE_ID=xxxxxxxx
VAULT_SECRET_ID=yyyyyyyy
VAULT_RSA_SECRET_PATH=kv/data/mmt/jwt-keys   # or kv/mmt/jwt-keys depending on KV v2 layout
USE_RSA_INTERNAL_JWT=1
```

The application will:
1. Exchange ROLE_ID/SECRET_ID for a token (`auth/approle/login`).
2. Fetch RSA keypair (expects fields `private_key_pem` and `public_key_pem`).
3. Periodically refresh keys & renew the token (`auth/token/renew-self`).

Metrics:
- `vault_refresh_failures_total` (key fetch failures)
- `vault_token_renew_success_total` / `vault_token_renew_failures_total`

### Recording & Alerting Enhancements

`backend/recording_rules.yaml` defines percentile latency, queue depth, and Vault failure rate helpers. Load into Prometheus via its config (`rule_files`).

Grafana dashboard JSON: `backend/grafana_dashboard.json` – import to visualize latency p95/p99, queue depth, and Vault failures.

### Tracing Verification

Test `backend/tests/test_trace_propagation.py` asserts W3C tracecontext injection (traceparent header) when publishing to RabbitMQ. Consumer side extracts parent context (span linkage) so downstream spans share the same trace ID.

### Field-Level Encryption

Enable at-rest field encryption for transcript text, summary, and string enrichment values:

Environment variables:
```
ENABLE_FIELD_ENCRYPTION=true
ENCRYPTION_KEYS=key1:BASE64KEY1,key2:BASE64KEY2
PRIMARY_ENCRYPTION_KEY_ID=key1
ENCRYPTION_ROTATE_HOURS=6   # re-encrypt pass every 6h (0 disables)
```

Key format: 32-byte (256-bit) random key base64-encoded (AES-256-GCM). Example generation:
```
python - <<'PY'
import os, base64; print(base64.b64encode(os.urandom(32)).decode())
PY
```

Data model stores encrypted blobs with wrapper: `{ "enc": true, "kid": "key1", "v": "ENC:<b64(nonce+ciphertext)>" }`.

Rotation: Add new key to `ENCRYPTION_KEYS`, switch `PRIMARY_ENCRYPTION_KEY_ID`, optional short overlap, then allow rotation thread to re-encrypt batches. Metric `encryption_rotate_updated_total` increments per rotation batch.

Security recommendations:
- Store ENCRYPTION_KEYS in a Kubernetes Secret or Vault (never commit).
- Limit lifetime of keys; rotate on schedule (e.g., monthly) or upon suspected exposure.
- Backup keys securely; losing active keys renders ciphertext unrecoverable.

Production validation & enforcement:
- In `ENV=prod`, service now FAILS FAST unless:
    - Explicit `INTERNAL_JWT_SECRET` (>=32 chars) is set (HS256 mode), OR
    - RSA mode enabled (`USE_RSA_INTERNAL_JWT=true`) **and** both private/public keys are configured (file or PEM env vars).
- If `ENABLE_FIELD_ENCRYPTION=true` in prod, both `ENCRYPTION_KEYS` and `PRIMARY_ENCRYPTION_KEY_ID` must be present.
- Missing or invalid primary encryption key triggers startup error in prod.

Encryption & rotation metrics:
- `encryption_active_keys`
- `encryption_key_reload_total`
- `encryption_rotate_attempt_total`
- `encryption_rotate_failures_total`
- `encryption_rotate_updated_total`
- `encryption_encrypt_failures_total`
- `encryption_decrypt_failures_total`
- `decryption_warnings_total` (API served a transcript with suspicious ciphertext; indicates partial decrypt issue)

Persistence / publish / audit metrics:
- `publish_failures_total`
- `transcripts_persist_failures_total`
- `audit_events_total{event="..."}`

Health endpoint:
```
GET /healthz -> { "status": "ok", "version": "<app_version>", "env": "<env>", "encryption_keys": <count>, "field_encryption_enabled": true|false }
```
Use for liveness/readiness (key count is informational; does not expose key material).

Publish reliability:
- Queue publish now retries up to 3 attempts with linear backoff (0.5s,1s).
- Failures during retries increment `publish_failures_total`.

Audit fallback:
- If `AUDIT_LOG_FILE` unset, audit events emitted via structured logger & counted in `audit_events_total`.


TRANSCRIPTS_DB_HOST=mysql
TRANSCRIPTS_DB_USER=openemr
TRANSCRIPTS_DB_PASSWORD=openemr
TRANSCRIPTS_DB_NAME=openemr
```

### Async Transcription Executor

Environment variables:

```
ASYNC_MAX_WORKERS=4              # worker threads
ASYNC_QUEUE_MAXSIZE=100          # bounded submission queue size
ASYNC_TASK_RETENTION_DAYS=7      # cleanup old async task rows
ASYNC_CLEANUP_INTERVAL_HOURS=24  # cleanup job interval
```

Behavior:
- Requests with `async_mode=true` enqueue work; 202 returned immediately.
- If queue is full a 503 is returned ("Async processing capacity exhausted").
- Metrics exported (see above) for sizing & alerting.


If these are absent the service falls back to a local `transcripts.db` SQLite file (dev only).

### Keycloak Role Mapping
External JWT (Keycloak) roles mapped via realm_access.roles -> internal roles using env overrides:
```
KEYCLOAK_WRITER_ROLE=writer
KEYCLOAK_READER_ROLE=reader
KEYCLOAK_ADMIN_ROLE=admin
```
Required scope/role for write: internal role `writer` (or `admin`).

### Test Mode Optimization
Set `FAST_TEST_MODE=1` to bypass Whisper model download with a dummy transcriber for fast CI tests.

### Database Migrations (Alembic)

Alembic is configured under `backend/alembic`. Commands (run from `backend/` directory):

```
export ALEMBIC_DB_URL="mysql+pymysql://openemr:openemr@mysql:3306/openemr?charset=utf8mb4"
alembic upgrade head
```

Generate a new revision after model changes:

```
alembic revision -m "add new field"
```

SQLite is blocked in production (`ENV=prod`). Set `ENV=prod` and proper MySQL env vars before deploying.

## Quick start

Create virtual environment and install deps:

```
pip install -r requirements.txt
```

Run API:

```
uvicorn main:app --reload --port 9000
```

Stream example (pseudo-code):

```python
import websockets, json, base64, asyncio

async def send_audio(path):
    async with websockets.connect("ws://localhost:9000/ws/transcribe") as ws:
        with open(path, "rb") as f:
            data = f.read()
        # naive single chunk
        await ws.send(json.dumps({"type": "chunk", "data": base64.b64encode(data).decode(), "final": True, "filename": path}))
        async for msg in ws:
            print(msg)

asyncio.run(send_audio("sample.wav"))
```

## Tests
## FHIR Integration

Set the following environment variables (see `.env.example`) to enable FHIR publishing in the consumer:

```
OPENEMR_FHIR_BASE_URL=http://localhost:8080
OPENEMR_FHIR_CLIENT_ID=mmt_client
OPENEMR_FHIR_CLIENT_SECRET=mmt_secret
OPENEMR_FHIR_USERNAME=admin
OPENEMR_FHIR_PASSWORD=pass
OPENEMR_SITE=default
```

The consumer will attempt to create a `DocumentReference` with the transcription text. If FHIR creation fails it falls back to the legacy API endpoint.


```
pytest -q
```

Run specific test:

```
pytest backend/tests/test_entity_extraction.py::test_extract_entities -q
```
