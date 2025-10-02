"""Centralised configuration for the transcription backend.

Loads environment variables once and exposes typed settings.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator
import secrets
import structlog


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API / Auth
    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")
    openai_api_key_file: str | None = Field(default=None, env="OPENAI_API_KEY_FILE")
    whisper_api_key: str | None = Field(default=None, env="WHISPER_API_KEY")
    whisper_api_key_file: str | None = Field(default=None, env="WHISPER_API_KEY_FILE")
    keycloak_public_key: str | None = Field(default=None, env="KEYCLOAK_PUBLIC_KEY")
    keycloak_issuer: str | None = Field(default=None, env="KEYCLOAK_ISSUER")
    keycloak_jwks_url: str | None = Field(default=None, env="KEYCLOAK_JWKS_URL")
    keycloak_jwks_refresh_seconds: int = Field(default=300, env="KEYCLOAK_JWKS_REFRESH_SECONDS")
    keycloak_writer_role: str | None = Field(default="writer", env="KEYCLOAK_WRITER_ROLE")
    keycloak_reader_role: str | None = Field(default="reader", env="KEYCLOAK_READER_ROLE")
    keycloak_admin_role: str | None = Field(default="admin", env="KEYCLOAK_ADMIN_ROLE")
    guest_secret: str = Field(default="guestsecret", env="GUEST_SECRET")
    # Local/dev email/password login (format: "user@example.com:pass,other:pass")
    allow_local_login: bool = Field(default_factory=lambda: os.environ.get("ENV", "dev") != "prod", env="ALLOW_LOCAL_LOGIN")
    local_login_users: str | None = Field(default=None, env="LOCAL_LOGIN_USERS")

    # RabbitMQ / Queues
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/", env="RABBITMQ_URL")
    transcription_queue: str = Field(default="transcriptions", env="TRANSCRIPTION_QUEUE")

    # Models
    whisper_model_size: str = Field(default="base", env="WHISPER_MODEL_SIZE")

    # Feature flags
    enable_cloud_transcription: bool = Field(default=True, env="ENABLE_CLOUD_TRANSCRIPTION")
    enable_local_transcription: bool = Field(default=True, env="ENABLE_LOCAL_TRANSCRIPTION")
    enable_partial_streaming: bool = Field(default=False, env="ENABLE_PARTIAL_STREAMING")
    # Chart templates / structured note prompts
    enable_chart_templates: bool = Field(default=False, env="ENABLE_CHART_TEMPLATES")

    # External storage providers
    storage_provider: str = Field(default="database", env="STORAGE_PROVIDER")
    nextcloud_base_url: str | None = Field(default=None, env="NEXTCLOUD_BASE_URL")
    nextcloud_username: str | None = Field(default=None, env="NEXTCLOUD_USERNAME")
    nextcloud_password: str | None = Field(default=None, env="NEXTCLOUD_PASSWORD")
    nextcloud_root_path: str = Field(default="MedicalTranscripts", env="NEXTCLOUD_ROOT_PATH")
    nextcloud_timeout_seconds: float = Field(default=10.0, env="NEXTCLOUD_TIMEOUT_SECONDS")
    nextcloud_verify_tls: bool = Field(default=True, env="NEXTCLOUD_VERIFY_TLS")

    # OpenEMR FHIR integration (optional)
    openemr_fhir_base_url: str | None = Field(default=None, env="OPENEMR_FHIR_BASE_URL")
    openemr_fhir_client_id: str | None = Field(default=None, env="OPENEMR_FHIR_CLIENT_ID")
    openemr_fhir_client_secret: str | None = Field(default=None, env="OPENEMR_FHIR_CLIENT_SECRET")
    openemr_fhir_username: str | None = Field(default=None, env="OPENEMR_FHIR_USERNAME")
    openemr_fhir_password: str | None = Field(default=None, env="OPENEMR_FHIR_PASSWORD")
    openemr_site: str = Field(default="default", env="OPENEMR_SITE")
    openemr_fhir_grant_type: str = Field(default="password", env="OPENEMR_FHIR_GRANT_TYPE")  # password | client_credentials
    openemr_fhir_scopes: str | None = Field(default=None, env="OPENEMR_FHIR_SCOPES")
    openemr_fhir_redirect_uri: str | None = Field(default=None, env="OPENEMR_FHIR_REDIRECT_URI")
    openemr_fhir_use_pkce: bool = Field(default=True, env="OPENEMR_FHIR_USE_PKCE")

    # Generic OAuth provider settings (for web SSO flows)
    oauth_frontend_redirect_url: str | None = Field(default=None, env="OAUTH_FRONTEND_REDIRECT_URL")
    oauth_backend_base_url: str | None = Field(default=None, env="OAUTH_BACKEND_BASE_URL")
    # Google
    oauth_google_client_id: str | None = Field(default=None, env="OAUTH_GOOGLE_CLIENT_ID")
    oauth_google_client_secret: str | None = Field(default=None, env="OAUTH_GOOGLE_CLIENT_SECRET")
    # Microsoft (Azure AD v2)
    oauth_microsoft_client_id: str | None = Field(default=None, env="OAUTH_MICROSOFT_CLIENT_ID")
    oauth_microsoft_client_secret: str | None = Field(default=None, env="OAUTH_MICROSOFT_CLIENT_SECRET")
    # Apple (requires client secret generation or precomputed secret)
    oauth_apple_client_id: str | None = Field(default=None, env="OAUTH_APPLE_CLIENT_ID")
    oauth_apple_client_secret: str | None = Field(default=None, env="OAUTH_APPLE_CLIENT_SECRET")

    rate_limit_per_minute: int = Field(default=120, env="RATE_LIMIT_PER_MINUTE")
    consumer_max_attempts: int = Field(default=3, env="CONSUMER_MAX_ATTEMPTS")
    # Redis (optional) for rate limiting / caching
    redis_url: str | None = Field(default=None, env="REDIS_URL")
    allow_guest_auth: bool = Field(default_factory=lambda: os.environ.get("ENV", "dev") != "prod", env="ALLOW_GUEST_AUTH")
    internal_jwt_secret: str = Field(default_factory=lambda: os.environ.get("INTERNAL_JWT_SECRET") or secrets.token_urlsafe(32), env="INTERNAL_JWT_SECRET")
    internal_jwt_old_secrets: str | None = Field(default=None, env="INTERNAL_JWT_OLD_SECRETS")  # comma separated
    environment_name: str = Field(default_factory=lambda: os.environ.get("ENV", "dev"), env="ENVIRONMENT_NAME")
    advanced_phi_masking: bool = Field(default=False, env="ADVANCED_PHI_MASKING")
    app_version: str = Field(default="0.3.0", env="APP_VERSION")
    # Data retention / compliance
    retention_days: int = Field(default=0, env="RETENTION_DAYS")  # 0 => disabled
    store_phi: bool = Field(default=True, env="STORE_PHI")  # if False, mask before persistence
    audit_log_file: str | None = Field(default=None, env="AUDIT_LOG_FILE")
    enable_idempotency: bool = Field(default=True, env="ENABLE_IDEMPOTENCY")
    idempotency_cache_size: int = Field(default=5000, env="IDEMPOTENCY_CACHE_SIZE")
    idempotency_ttl_seconds: int = Field(default=3600, env="IDEMPOTENCY_TTL_SECONDS")
    use_bloom_idempotency: bool = Field(default=False, env="USE_BLOOM_IDEMPOTENCY")
    bloom_error_rate: float = Field(default=0.001, env="BLOOM_ERROR_RATE")
    bloom_capacity: int = Field(default=100000, env="BLOOM_CAPACITY")
    queue_depth_poll_interval: int = Field(default=15, env="QUEUE_DEPTH_POLL_INTERVAL")
    admin_api_key: str | None = Field(default=None, env="ADMIN_API_KEY")
    # RSA key rotation (optional)
    use_rsa_internal_jwt: bool = Field(default=False, env="USE_RSA_INTERNAL_JWT")
    internal_jwt_private_key_pem: str | None = Field(default=None, env="INTERNAL_JWT_PRIVATE_KEY_PEM")
    internal_jwt_public_key_pem: str | None = Field(default=None, env="INTERNAL_JWT_PUBLIC_KEY_PEM")
    internal_jwt_old_public_keys_pem: str | None = Field(default=None, env="INTERNAL_JWT_OLD_PUBLIC_KEYS_PEM")  # '||' separated
    internal_jwt_private_key_file: str | None = Field(default=None, env="INTERNAL_JWT_PRIVATE_KEY_FILE")
    internal_jwt_public_key_file: str | None = Field(default=None, env="INTERNAL_JWT_PUBLIC_KEY_FILE")
    drain_wait_seconds: int = Field(default=60, env="DRAIN_WAIT_SECONDS")
    enable_db_idempotency: bool = Field(default=False, env="ENABLE_DB_IDEMPOTENCY")
    idempotency_db_ttl_seconds: int = Field(default=86400, env="IDEMPOTENCY_DB_TTL_SECONDS")
    # Vault integration (optional)
    vault_addr: str | None = Field(default=None, env="VAULT_ADDR")
    vault_token: str | None = Field(default=None, env="VAULT_TOKEN")
    vault_rsa_secret_path: str | None = Field(default=None, env="VAULT_RSA_SECRET_PATH")  # e.g. kv/data/mmt-internal-jwt
    vault_rsa_refresh_seconds: int = Field(default=300, env="VAULT_RSA_REFRESH_SECONDS")
    vault_role_id: str | None = Field(default=None, env="VAULT_ROLE_ID")
    vault_secret_id: str | None = Field(default=None, env="VAULT_SECRET_ID")
    # Field-level encryption
    enable_field_encryption: bool = Field(default=False, env="ENABLE_FIELD_ENCRYPTION")
    encryption_keys: str | None = Field(default=None, env="ENCRYPTION_KEYS")  # format kid1:base64key,kid2:base64key
    primary_encryption_key_id: str | None = Field(default=None, env="PRIMARY_ENCRYPTION_KEY_ID")
    encryption_rotate_hours: int = Field(default=0, env="ENCRYPTION_ROTATE_HOURS")  # 0 disables automatic rotation
    # Size / streaming limits
    max_upload_bytes: int = Field(default=50_000_000, env="MAX_UPLOAD_BYTES")  # 50 MB
    max_ws_buffer_bytes: int = Field(default=10_000_000, env="MAX_WS_BUFFER_BYTES")  # 10 MB
    max_request_body_bytes: int = Field(default=60_000_000, env="MAX_REQUEST_BODY_BYTES")  # 60 MB overall (form + file)
    # CORS / Security
    cors_allow_origins: str | None = Field(default="*", env="CORS_ALLOW_ORIGINS")  # comma separated or *
    csp_policy: str | None = Field(default="default-src 'self'" , env="CSP_POLICY")
    websocket_allowed_origins: str | None = Field(default="*", env="WEBSOCKET_ALLOWED_ORIGINS")  # comma separated or *
    mask_phi_in_responses: bool = Field(default=False, env="MASK_PHI_IN_RESPONSES")
    # Async transcription executor config
    async_max_workers: int = Field(default=2, env="ASYNC_MAX_WORKERS")
    async_queue_maxsize: int = Field(default=50, env="ASYNC_QUEUE_MAXSIZE")  # bounded submission queue
    async_task_retention_days: int = Field(default=7, env="ASYNC_TASK_RETENTION_DAYS")
    async_cleanup_interval_hours: int = Field(default=24, env="ASYNC_CLEANUP_INTERVAL_HOURS")
    force_sync_publish: bool = Field(default=False, env="FORCE_SYNC_PUBLISH")  # primarily for test determinism
    # Telemetry (Sentry)
    sentry_dsn: str | None = Field(default=None, env="SENTRY_DSN")
    sentry_traces_sample_rate: float = Field(default=0.0, env="SENTRY_TRACES_SAMPLE_RATE")
    # Demo mode (disable external integrations & queue publishing)
    demo_mode: bool = Field(default=False, env="DEMO_MODE")

    @model_validator(mode="after")
    def _apply_whisper_secret_fallback(self):  # type: ignore[override]
        """Normalize OpenAI/Whisper API credentials, supporting secret file mounts."""

        def _read_secret(path: str | None) -> str | None:
            if not path:
                return None
            try:
                data = Path(path).read_text(encoding="utf-8").strip()
                return data or None
            except FileNotFoundError:
                structlog.get_logger(__name__).warning("config/secret-file-missing", path=path)
            except OSError as exc:  # pragma: no cover - unexpected IO errors
                structlog.get_logger(__name__).warning("config/secret-file-error", path=path, error=str(exc))
            return None

        if not self.openai_api_key:
            file_value = _read_secret(self.openai_api_key_file) or _read_secret(self.whisper_api_key_file)
            if file_value:
                object.__setattr__(self, "openai_api_key", file_value)
        if not self.openai_api_key and self.whisper_api_key:
            object.__setattr__(self, "openai_api_key", self.whisper_api_key.strip())
        if self.openai_api_key:
            object.__setattr__(self, "openai_api_key", self.openai_api_key.strip())
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()  # type: ignore[arg-type]
    # Production secret enforcement
    env = os.environ.get("ENV", os.environ.get("ENVIRONMENT_NAME", "dev"))
    if env == 'prod':
        log = structlog.get_logger(__name__)
        if s.use_rsa_internal_jwt:
            if not (s.internal_jwt_private_key_pem or s.internal_jwt_private_key_file):
                raise RuntimeError("RSA mode enabled in prod without private key configured")
            if not (s.internal_jwt_public_key_pem or s.internal_jwt_public_key_file):
                raise RuntimeError("RSA mode enabled in prod without public key configured")
        else:
            auto_gen = 'INTERNAL_JWT_SECRET' not in os.environ
            weak = len(s.internal_jwt_secret) < 32
            if auto_gen or weak:
                raise RuntimeError("Explicit strong INTERNAL_JWT_SECRET (>=32 chars) required in prod")
        if s.enable_field_encryption:
            # basic validation: must have keys & primary (deeper handled elsewhere)
            if not (s.encryption_keys and s.primary_encryption_key_id):
                raise RuntimeError("Field encryption enabled in prod but keys/primary missing")
        log.info("config/validated", prod=True)
    return s
