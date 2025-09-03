# Production Deployment Checklist

## Critical Security Fixes Applied

### ✅ Security Vulnerabilities Fixed
- [x] **Log Injection (CWE-117)**: Added input sanitization for all user inputs before logging
- [x] **Path Traversal (CWE-22)**: Added filename validation to prevent directory traversal attacks
- [x] **Resource Leaks (CWE-400)**: Fixed connection management in DLQ reprocessor
- [x] **Session ID Validation**: Added proper validation for session identifiers
- [x] **Division by Zero**: Fixed Prometheus recording rules to prevent query failures

### ⚠️ Remaining Issues to Address

#### High Priority
1. **Generic Exception Handling**: Replace broad `except Exception:` with specific exception types
2. **Error Handling**: Replace `try/except/pass` blocks with proper error logging
3. **Input Validation**: Add comprehensive input validation for all public methods

#### Medium Priority
1. **Function Complexity**: Break down large functions (>70 lines) into smaller components
2. **Cyclomatic Complexity**: Simplify functions with high decision complexity
3. **Global Variables**: Refactor global state management

## Production Environment Requirements

### Infrastructure
- [ ] **Database**: MySQL configured (SQLite blocked in production)
- [ ] **Message Queue**: RabbitMQ cluster with persistence
- [ ] **Cache**: Redis cluster for rate limiting and sessions
- [ ] **Monitoring**: Prometheus + Grafana dashboard deployed
- [ ] **Logging**: Centralized log aggregation (ELK/Loki)
- [ ] **Secrets**: Vault or AWS Secrets Manager integration

### Security Configuration
- [ ] **CORS**: Set specific allowed origins (no wildcards)
- [ ] **TLS**: HTTPS enforced with valid certificates
- [ ] **Authentication**: Keycloak properly configured
- [ ] **Encryption**: Field-level encryption keys configured
- [ ] **Rate Limiting**: Redis-backed rate limiting enabled
- [ ] **Admin API**: Strong admin key configured

### Environment Variables (Production)
```bash
# Core
ENV=prod
APP_VERSION=0.3.0

# Database
TRANSCRIPTS_DB_HOST=mysql-host
TRANSCRIPTS_DB_USER=mmt_user
TRANSCRIPTS_DB_PASSWORD=<strong-password>
TRANSCRIPTS_DB_NAME=mmt_prod

# Security
INTERNAL_JWT_SECRET=<64-char-random-string>
ALLOW_GUEST_AUTH=false
CORS_ALLOW_ORIGINS=https://yourdomain.com
WEBSOCKET_ALLOWED_ORIGINS=https://yourdomain.com

# Encryption
ENABLE_FIELD_ENCRYPTION=true
ENCRYPTION_KEYS=key1:<base64-key>,key2:<base64-key>
PRIMARY_ENCRYPTION_KEY_ID=key1

# External Services
OPENAI_API_KEY=<openai-key>
KEYCLOAK_ISSUER=https://auth.yourdomain.com/realms/mmt
KEYCLOAK_JWKS_URL=https://auth.yourdomain.com/realms/mmt/protocol/openid-connect/certs

# Infrastructure
RABBITMQ_URL=amqps://user:pass@rabbitmq-cluster:5671/
REDIS_URL=redis://redis-cluster:6379/0

# Monitoring
SENTRY_DSN=<sentry-dsn>
OTEL_EXPORTER_OTLP_ENDPOINT=https://jaeger.yourdomain.com
```

### Kubernetes Deployment
- [ ] **Resource Limits**: CPU/Memory limits configured
- [ ] **Security Context**: Non-root user, read-only filesystem
- [ ] **Health Checks**: Liveness and readiness probes
- [ ] **Secrets**: Kubernetes secrets for sensitive data
- [ ] **Network Policies**: Restrict pod-to-pod communication
- [ ] **RBAC**: Minimal service account permissions

### Monitoring & Alerting
- [ ] **Metrics**: All Prometheus metrics scraped
- [ ] **Alerts**: Critical alerts configured (see alerts_prometheus.yml)
- [ ] **Dashboard**: Grafana dashboard imported
- [ ] **Log Monitoring**: Error rate and security event alerts
- [ ] **Uptime**: External health check monitoring

### Compliance & Audit
- [ ] **Audit Logging**: Structured audit logs enabled
- [ ] **Data Retention**: Retention policies configured
- [ ] **PHI Handling**: PHI masking configured per requirements
- [ ] **Backup**: Database backup strategy implemented
- [ ] **Disaster Recovery**: Recovery procedures documented

### Performance & Scaling
- [ ] **Auto-scaling**: HPA or KEDA configured
- [ ] **Load Testing**: Performance baseline established
- [ ] **Circuit Breakers**: Failure handling tested
- [ ] **Queue Monitoring**: RabbitMQ queue depth alerts
- [ ] **Connection Pooling**: Database connection limits set

## Deployment Steps

1. **Pre-deployment**
   ```bash
   # Run security scan
   docker build -t mmt-backend:prod --build-arg INCLUDE_ML=0 backend/
   trivy image mmt-backend:prod
   
   # Run tests
   cd backend && pytest -v
   ```

2. **Database Migration**
   ```bash
   # Apply migrations
   alembic upgrade head
   ```

3. **Deploy Application**
   ```bash
   # Deploy with Helm
   helm upgrade --install mmt deploy/helm/mmt \
     --set image.tag=0.3.0 \
     --set env.ENV=prod \
     --values production-values.yaml
   ```

4. **Post-deployment Verification**
   - [ ] Health endpoints responding
   - [ ] Metrics being scraped
   - [ ] Alerts firing correctly
   - [ ] Authentication working
   - [ ] File upload/transcription working
   - [ ] Database connectivity confirmed

## Security Incident Response

### Immediate Actions
1. **Log Analysis**: Check audit logs for suspicious activity
2. **Access Review**: Verify all active sessions and tokens
3. **Network Isolation**: Isolate affected components if needed
4. **Key Rotation**: Rotate JWT secrets and encryption keys if compromised

### Communication
- **Internal**: Notify security team and stakeholders
- **External**: Follow breach notification requirements (GDPR, HIPAA)
- **Documentation**: Maintain incident timeline and actions taken

## Maintenance

### Regular Tasks
- **Weekly**: Review security alerts and logs
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Security audit and penetration testing
- **Annually**: Disaster recovery testing

### Key Rotation Schedule
- **JWT Secrets**: Every 90 days
- **Encryption Keys**: Every 180 days
- **Database Passwords**: Every 90 days
- **API Keys**: Per provider recommendations