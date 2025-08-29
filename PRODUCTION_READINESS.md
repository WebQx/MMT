# Production Readiness Guide for MMT

## Overview

This guide outlines the production-grade enhancements implemented in the MMT (Medical Transcription Tool) repository. The system is now equipped with comprehensive monitoring, security, scalability, and operational features required for production deployment.

## Production Hardening ✅

### 1. Dead Letter Queue (DLQ) Reprocessor
- **Status**: ✅ Implemented with exponential backoff and Prometheus metrics
- **Location**: `backend/dlq_reprocessor.py`
- **Features**:
  - Configurable retry attempts via `MAX_REPROCESS_ATTEMPTS`
  - Exponential backoff with `BACKOFF_BASE_SECONDS`
  - Comprehensive metrics for monitoring
  - OpenTelemetry tracing support

### 2. Mandatory Audit Logging
- **Status**: ✅ Enforced in production
- **Configuration**: `AUDIT_LOG_FILE` environment variable (mandatory in production)
- **Features**:
  - JSONL format audit logs
  - Directory validation and write permission checks
  - Comprehensive event logging with correlation IDs
  - PHI masking capabilities

### 3. Data Retention Purge Job
- **Status**: ✅ Implemented as CronJob
- **Location**: `backend/retention.py`, `deploy/helm/mmt/templates/cron-retention.yaml`
- **Features**:
  - Configurable retention period via `RETENTION_DAYS`
  - Kubernetes CronJob with proper security context
  - Metrics tracking for purged records
  - Production-grade error handling

### 4. Encryption and Startup Validation
- **Status**: ✅ Implemented comprehensive validation
- **Location**: `backend/startup_checks.py`
- **Features**:
  - TLS certificate validation
  - Encryption key format and strength validation
  - Database configuration validation (prohibits SQLite in production)
  - External service configuration validation

## Observability ✅

### 5. Prometheus Alert Rules
- **Status**: ✅ Comprehensive alerts defined
- **Location**: `backend/alerts_prometheus.yml`
- **Coverage**:
  - DLQ ingress rate and reprocessor failures
  - Queue depth and latency monitoring
  - Vault health and key refresh failures
  - API error rates and response times
  - Circuit breaker and publish failure alerts

### 6. OpenTelemetry Tracing
- **Status**: ✅ End-to-end tracing implemented
- **Features**:
  - W3C trace propagation across RabbitMQ
  - FastAPI, SQLAlchemy, and Requests instrumentation
  - Trace IDs embedded in structured logs
  - OTLP export support

## Scaling and Autoscaling ✅

### 7. KEDA-based Autoscaling
- **Status**: ✅ Configured with RabbitMQ queue trigger
- **Configuration**: `deploy/helm/mmt/templates/keda-scaledobject.yaml`
- **Features**:
  - RabbitMQ queue length-based scaling
  - Configurable polling intervals and cooldown periods
  - Production-ready scaling parameters

### 8. Worker Pool Optimization
- **Status**: ✅ Dynamic optimization based on CPU cores
- **Configuration**:
  - `WORKER_POOL_OPTIMIZATION_ENABLED`: Enable automatic optimization
  - `MIN_WORKERS_PER_CORE` / `MAX_WORKERS_PER_CORE`: Per-core scaling limits
  - `ASYNC_MAX_WORKERS` / `ASYNC_QUEUE_MAXSIZE`: Fine-tuning parameters

## Security ✅

### 9. JWT Secret Rotation
- **Status**: ✅ Automated with HashiCorp Vault
- **Features**:
  - Vault AppRole authentication
  - Automatic key refresh and token renewal
  - RSA key support for enhanced security
  - Comprehensive metrics for monitoring

### 10. TLS Configuration
- **Status**: ✅ Production enforcement with validation
- **Features**:
  - TLS enabled by default in production (`ENFORCE_TLS_IN_PRODUCTION`)
  - Certificate validation during startup
  - Configurable via `SSL_CERT_FILE` and `SSL_KEY_FILE`

## Deployment Enhancements ✅

### 11. External Services Support
- **Status**: ✅ Configuration for external RabbitMQ and Redis
- **Configuration**:
  - `EXTERNAL_RABBITMQ_ENABLED` / `EXTERNAL_RABBITMQ_HOST`
  - `EXTERNAL_REDIS_ENABLED` / `EXTERNAL_REDIS_HOST`
  - Production warnings for localhost configurations

### 12. RedisBloom Idempotency
- **Status**: ✅ Enhanced deduplication efficiency
- **Configuration**:
  - `ENABLE_REDIS_BLOOM_IDEMPOTENCY`: Enable RedisBloom features
  - `REDIS_BLOOM_KEY_PREFIX`: Namespace configuration
  - `REDIS_BLOOM_TTL_SECONDS`: TTL management

## CI/CD Pipeline ✅

### 13. Comprehensive GitHub Actions Workflow
- **Status**: ✅ Enhanced CI pipeline implemented
- **Location**: `.github/workflows/ci-cd.yml`
- **Features**:
  - **Backend Testing**: pytest with coverage reporting
  - **Linting**: flake8 code quality checks
  - **Type Checking**: mypy static analysis
  - **Security Scanning**: bandit and safety dependency checks
  - **Container Scanning**: Trivy vulnerability assessment
  - **Integration Tests**: Redis and RabbitMQ service tests
  - **Production Validation**: Startup checks and configuration validation

## Database and Integration ✅

### 14. FHIR Integration Robustness
- **Status**: ✅ Robust without legacy API fallback
- **Features**:
  - Primary FHIR endpoint with proper error handling
  - Comprehensive test coverage for FHIR workflows
  - No dependency on legacy API in production mode

### 15. Production Database Enforcement
- **Status**: ✅ MySQL/PostgreSQL only in production
- **Features**:
  - SQLite prohibited in production environment
  - Database URL validation during startup
  - Support for external database services

## Configuration Management

### Environment Variables

Key production configuration variables:

```bash
# Environment
ENV=prod

# Database (Required)
DATABASE_URL=mysql://user:password@mysql-host:3306/mmt_db

# Audit Logging (Mandatory in Production)
AUDIT_LOG_FILE=/app/logs/audit.log

# Security
INTERNAL_JWT_SECRET=your-32-character-secret-key-here
ENFORCE_TLS_IN_PRODUCTION=true
SSL_CERT_FILE=/app/certs/server.crt
SSL_KEY_FILE=/app/certs/server.key

# Worker Optimization
WORKER_POOL_OPTIMIZATION_ENABLED=true
ASYNC_MAX_WORKERS=4
ASYNC_QUEUE_MAXSIZE=100

# External Services
EXTERNAL_RABBITMQ_ENABLED=true
EXTERNAL_RABBITMQ_HOST=rabbitmq.example.com
EXTERNAL_REDIS_ENABLED=true
EXTERNAL_REDIS_HOST=redis.example.com

# RedisBloom Idempotency
ENABLE_REDIS_BLOOM_IDEMPOTENCY=true

# Data Retention
RETENTION_DAYS=30
ASYNC_TASK_RETENTION_DAYS=7
```

### Helm Configuration

Deploy with production-ready settings:

```bash
helm upgrade --install mmt deploy/helm/mmt \
    --set env.ENV=prod \
    --set env.AUDIT_LOG_FILE=/app/logs/audit.log \
    --set env.WORKER_POOL_OPTIMIZATION_ENABLED=true \
    --set env.EXTERNAL_RABBITMQ_ENABLED=true \
    --set env.EXTERNAL_REDIS_ENABLED=true \
    --set keda.enabled=true \
    --set retention.schedule="0 2 * * *" \
    --set auditLogs.enabled=true \
    --set tls.enabled=true
```

## Monitoring and Alerting

### Prometheus Metrics

Key metrics to monitor in production:

- **DLQ Metrics**: `reprocessor_*_total`
- **Queue Health**: `transcription_queue_depth`, `async_task_queue_size`
- **Latency**: `transcription_duration_seconds`, `api_request_duration_seconds`
- **Errors**: `publish_failures_total`, `breaker_open_total`
- **Vault Health**: `vault_refresh_failures_total`, `vault_token_renew_*_total`

### Alert Rules

Critical alerts configured in `alerts_prometheus.yml`:

- High DLQ ingress rate
- Reprocessor permanent failures
- Elevated latency (P95 > 5s for transcription, >15s for E2E)
- Queue backlog sustained (>100 messages for 15m)
- Vault key refresh/token renewal failures
- High API error rate (>5% 5xx responses)

## Testing and Validation

### Production Startup Tests

Run production validation:

```bash
cd backend
export ENV=prod
export AUDIT_LOG_FILE=/tmp/audit.log
export DATABASE_URL=mysql://user:pass@host/db
export INTERNAL_JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
python startup_checks.py
```

### Integration Tests

Comprehensive test suite covers:

- Startup validation checks
- FHIR integration (without legacy fallback)
- OpenTelemetry trace propagation
- DLQ reprocessor functionality
- Encryption and security features

## Deployment Checklist

Before production deployment:

- [ ] Configure external MySQL/PostgreSQL database
- [ ] Set up external RabbitMQ and Redis services  
- [ ] Generate and configure TLS certificates
- [ ] Set up Vault for JWT key rotation
- [ ] Configure audit log persistence volume
- [ ] Enable Prometheus monitoring and alerts
- [ ] Configure KEDA autoscaling
- [ ] Run production validation tests
- [ ] Set up data retention schedule
- [ ] Configure external observability stack (Jaeger, Grafana)

## Maintenance Operations

### Routine Tasks

1. **Monitor alerts** for DLQ health, latency, and errors
2. **Review audit logs** for security events
3. **Rotate encryption keys** based on security policy
4. **Update worker pool settings** based on load patterns
5. **Validate backup and recovery** procedures

### Troubleshooting

- **High DLQ ingress**: Check downstream service health
- **Vault failures**: Verify AppRole credentials and network connectivity
- **Queue backlog**: Review autoscaling configuration and resource limits
- **Startup failures**: Check startup validation logs for specific issues

This production-ready MMT deployment provides enterprise-grade reliability, security, and observability for medical transcription workflows.