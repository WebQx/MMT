from __future__ import annotations

from prometheus_client import Counter, Histogram
from prometheus_client import Gauge

# Core pipeline metrics
transcripts_published_total = Counter(
	"transcripts_published_total", "Number of transcripts published"
)
consumer_fhir_success_total = Counter(
	"consumer_fhir_success_total", "FHIR DocumentReferences created"
)
consumer_legacy_success_total = Counter(
	"consumer_legacy_success_total", "Legacy API posts"
)
consumer_failure_total = Counter(
	"consumer_failure_total", "Consumer failures"
)
websocket_partial_sent_total = Counter(
	"websocket_partial_sent_total", "Partial websocket transcripts"
)
websocket_rejected_total = Counter(
	"websocket_rejected_total", "Rejected websocket connection attempts", ["reason"]
)
transcription_duration_seconds = Histogram(
	"transcription_duration_seconds", "Transcription duration seconds"
)
api_requests_total = Counter(
	"api_requests_total", "HTTP requests total", ["method", "path", "code"]
)
api_request_duration_seconds = Histogram(
	"api_request_duration_seconds", "API request duration seconds", buckets=(0.05,0.1,0.25,0.5,1,2,5)
)
api_in_flight_requests = Gauge(
	"api_in_flight_requests", "Current in-flight HTTP requests"
)
consumer_dlq_total = Counter(
	"consumer_dlq_total", "Messages routed to DLQ"
)
transcripts_persisted_total = Counter(
	"transcripts_persisted_total", "Transcripts persisted to storage"
)
reprocessor_attempt_total = Counter(
	"reprocessor_attempt_total", "DLQ reprocessor attempts"
)
reprocessor_success_total = Counter(
	"reprocessor_success_total", "DLQ reprocessor successful republishes"
)
reprocessor_failure_total = Counter(
	"reprocessor_failure_total", "DLQ reprocessor transient failures"
)
reprocessor_permanent_failure_total = Counter(
	"reprocessor_permanent_failure_total", "DLQ messages exhausted retries"
)
transcripts_purged_total = Counter(
	"transcripts_purged_total", "Transcripts purged by retention job"
)

publish_failures_total = Counter(
	"publish_failures_total", "Failures attempting to publish to queue"
)

transcripts_persist_failures_total = Counter(
	"transcripts_persist_failures_total", "Failed transcript persistence attempts"
)

audit_events_total = Counter(
	"audit_events_total", "Audit events recorded", ["event"]
)

decryption_warnings_total = Counter(
	"decryption_warnings_total", "Transcripts returned with decryption_warning flag"
)

# SLO / quality metrics
e2e_transcription_latency_seconds = Histogram(
	"e2e_transcription_latency_seconds",
	"End-to-end latency (seconds) from API publish to consumer persistence",
	buckets=(0.5, 1, 2, 3, 5, 8, 13, 21, 34, 55),  # Fibonacci-ish style spread
)
duplicates_skipped_total = Counter(
	"duplicates_skipped_total",
	"Duplicate transcript messages skipped due to idempotency hash",
)

# Idempotency source counters
idempotency_db_hits_total = Counter(
	"idempotency_db_hits_total",
	"Messages recognized as duplicates via DB idempotency layer",
)
idempotency_redis_hits_total = Counter(
	"idempotency_redis_hits_total",
	"Messages recognized as duplicates via Redis idempotency layer",
)
idempotency_memory_hits_total = Counter(
	"idempotency_memory_hits_total",
	"Messages recognized as duplicates via in-memory idempotency layer",
)

# Operational gauges
transcription_queue_depth = Gauge(
	"transcription_queue_depth",
	"vault_refresh_failures_total",
	"Current depth of the transcription publish queue (approximate)",
)

# Circuit breaker metrics
breaker_open_total = Counter(
	"breaker_open_total", "Times the publish circuit breaker opened"
)
breaker_fallback_persist_total = Counter(
	"breaker_fallback_persist_total", "Transcripts persisted locally due to open circuit"
)

# JWKS / external auth metrics
jwks_refresh_total = Counter(
	"jwks_refresh_total", "Number of JWKS refresh attempts", ["status"]  # status=success|fail
)
jwks_keys_active = Gauge(
	"jwks_keys_active", "Current number of active JWKS keys cached"
)

# PHI masking metrics
phi_redactions_total = Counter(
	"phi_redactions_total", "Number of times PHI redaction applied", ["scope"]  # scope=persist|response
)

# Async transcription metrics
async_tasks_started_total = Counter(
	"async_tasks_started_total", "Async transcription tasks started"
)
async_tasks_completed_total = Counter(
	"async_tasks_completed_total", "Async transcription tasks completed successfully"
)
async_tasks_failed_total = Counter(
	"async_tasks_failed_total", "Async transcription tasks that errored"
)
async_task_duration_seconds = Histogram(
	"async_task_duration_seconds", "Async transcription task processing duration seconds", buckets=(0.5,1,2,3,5,8,13,21,34,55)
)
async_task_queue_size = Gauge(
	"async_task_queue_size", "Current size of the async transcription submission queue"
)
async_tasks_purged_total = Counter(
	"async_tasks_purged_total", "Async task records removed by cleanup job"
)

drain_start_total = Counter(
	"drain_start_total", "Times an administrative drain was initiated"
)

vault_refresh_failures_total = Counter(
	"vault_refresh_failures_total",
	"Count of Vault key refresh failures",
)

vault_token_renew_success_total = Counter(
	'vault_token_renew_success_total',
	'Number of successful Vault token renewals (AppRole)'
)
vault_token_renew_failures_total = Counter(
	'vault_token_renew_failures_total',
	'Number of failed Vault token renewals (AppRole)'
)

encryption_rotate_updated_total = Counter(
	'encryption_rotate_updated_total',
	'Number of transcript rows re-encrypted during key rotation'
)

encryption_key_reload_total = Counter(
	'encryption_key_reload_total',
	'Number of times encryption key material was (re)loaded'
)

encryption_encrypt_failures_total = Counter(
	'encryption_encrypt_failures_total',
	'Number of field encryption attempts that failed'
)

encryption_decrypt_failures_total = Counter(
	'encryption_decrypt_failures_total',
	'Number of field decryption attempts that failed'
)

from prometheus_client import Gauge as _Gauge
encryption_active_keys = _Gauge(
	'encryption_active_keys',
	'Current count of active (valid) encryption keys'
)

encryption_rotate_attempt_total = Counter(
	'encryption_rotate_attempt_total',
	'Number of rotation batch attempts executed'
)

encryption_rotate_failures_total = Counter(
	'encryption_rotate_failures_total',
	'Number of rotation batch attempts that failed'
)

__all__ = [
	# counters
	"transcripts_published_total",
	"consumer_fhir_success_total",
	"consumer_legacy_success_total",
	"consumer_failure_total",
	"websocket_partial_sent_total",
	"websocket_rejected_total",
	"consumer_dlq_total",
	"transcripts_persisted_total",
	"reprocessor_attempt_total",
	"reprocessor_success_total",
	"reprocessor_failure_total",
	"reprocessor_permanent_failure_total",
	"transcripts_purged_total",
	"publish_failures_total",
	"transcripts_persist_failures_total",
	"audit_events_total",
	"decryption_warnings_total",
	"duplicates_skipped_total",
	"idempotency_db_hits_total",
	"idempotency_redis_hits_total",
	"idempotency_memory_hits_total",
	"transcription_queue_depth",
	"vault_token_renew_success_total",
	"vault_token_renew_failures_total",
	"encryption_rotate_updated_total",
	"encryption_key_reload_total",
	"encryption_encrypt_failures_total",
	"encryption_decrypt_failures_total",
	"encryption_active_keys",
	"encryption_rotate_attempt_total",
	"encryption_rotate_failures_total",
	"breaker_open_total",
	"breaker_fallback_persist_total",
	"jwks_refresh_total",
	"jwks_keys_active",
	"phi_redactions_total",
	"async_tasks_started_total",
	"async_tasks_completed_total",
	"async_tasks_failed_total",
	"async_tasks_purged_total",
	"drain_start_total",
	# histograms
	"transcription_duration_seconds",
	"api_requests_total",
	"api_request_duration_seconds",
	"api_in_flight_requests",
	"e2e_transcription_latency_seconds",
	"async_task_duration_seconds",
	"async_task_queue_size",
]