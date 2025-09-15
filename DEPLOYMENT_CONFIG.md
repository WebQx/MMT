# MMT Deployment Configuration Guide

## Overview

This guide documents the deployment configurations for:
- **Frontend Demo**: Deployed to GitHub Pages with demo mode enabled
- **Backend Production**: Deployed to Railway with full production configuration

## Frontend Demo Deployment (GitHub Pages)

### Configuration
- **Platform**: GitHub Pages
- **URL**: https://webqx.github.io/MMT/
- **Mode**: Demo mode with connection to Railway backend
- **Features**: Full frontend functionality with live backend connection

### Environment Variables
- `BACKEND_URL`: Points to Railway production backend (default: https://mmt-backend-production.up.railway.app)
- `DEMO_MODE`: true
- `ENVIRONMENT`: demo

### Deployment Trigger
- Automatic: Push to main branch
- Manual: Workflow dispatch with optional backend URL override

## Backend Production Deployment (Railway)

### Configuration
- **Platform**: Railway
- **Mode**: Full production (no demo mode)
- **Features**: Complete ML stack, all transcription services enabled

### Required Environment Variables

#### Core Production Settings
```
ENV=prod
ENVIRONMENT_NAME=production
DEMO_MODE=false
```

#### Security & Authentication
```
INTERNAL_JWT_SECRET=<secure-32+-character-secret>
GUEST_SECRET=<secure-guest-secret>
ALLOW_GUEST_AUTH=false  # Disabled in production
```

#### API Keys
```
OPENAI_API_KEY=<your-openai-api-key>
```

#### Database & Persistence
```
TRANSCRIPTS_DB_URL=<mysql-connection-string>
ENCRYPTION_KEYS=<base64-encoded-encryption-keys>
PRIMARY_ENCRYPTION_KEY_ID=<primary-key-id>
```

#### Message Queue
```
RABBITMQ_URL=<rabbitmq-connection-string>
```

#### Feature Flags (Production)
```
ENABLE_LOCAL_TRANSCRIPTION=true
ENABLE_CLOUD_TRANSCRIPTION=true
ENABLE_PARTIAL_STREAMING=true
INCLUDE_ML=true
```

#### Optional Integrations
```
# OpenEMR FHIR Integration
OPENEMR_FHIR_BASE_URL=<openemr-fhir-endpoint>
OPENEMR_FHIR_CLIENT_ID=<client-id>
OPENEMR_FHIR_CLIENT_SECRET=<client-secret>

# Keycloak Authentication
KEYCLOAK_PUBLIC_KEY=<keycloak-public-key>
KEYCLOAK_ISSUER=<keycloak-issuer-url>
KEYCLOAK_JWKS_URL=<keycloak-jwks-url>

# Monitoring
SENTRY_DSN=<sentry-dsn>
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Railway Service Configuration

The backend is configured with:
- **Health Check**: `/health/live` endpoint
- **Restart Policy**: ON_FAILURE with max 3 retries
- **Auto-scaling**: Based on resource usage
- **Build**: Nixpacks with full ML dependencies

### Deployment Triggers
- **Automatic**: When CI/CD workflows complete successfully on main branch
- **Manual**: Workflow dispatch with options:
  - `include_ml`: Install ML dependencies (default: true)
  - `production_mode`: Deploy in production mode (default: true)
  - `release_tag`: Optional release tag creation

## Security Considerations

### Production Backend
- Demo mode disabled (`DEMO_MODE=false`)
- Guest authentication disabled
- Strong JWT secrets required (32+ characters)
- Field encryption enabled with proper key management
- All integrations use secure authentication

### Demo Frontend
- Read-only demo capabilities
- Connected to production backend for live functionality
- No sensitive operations exposed
- Rate limiting applied through backend

## Monitoring & Health Checks

### Backend Health Endpoints
- `/health/live` - Liveness probe
- `/health/ready` - Readiness probe
- `/metrics` - Prometheus metrics

### Demo Status Check
The deployment includes smoke tests that verify:
- Backend health endpoint accessibility
- Demo mode is properly disabled in production backend
- Transcription services are functional

## Deployment Workflow

1. **Code Changes**: Push to main branch
2. **CI/CD Pipeline**: Runs tests and security scans
3. **Backend Deployment**: Automatic deployment to Railway in production mode
4. **Frontend Deployment**: Automatic deployment to GitHub Pages in demo mode
5. **Health Checks**: Automated verification of deployment success
6. **Release Tagging**: Optional release tag creation

## Troubleshooting

### Common Issues
1. **Railway Start Script Error**: Ensure `start.sh` is executable and present
2. **Environment Variables**: Verify all required production variables are set
3. **Health Check Failures**: Check backend logs for startup errors
4. **Frontend-Backend Connection**: Verify CORS settings and API URLs

### Logs Access
- **Railway Backend**: Railway dashboard or CLI
- **GitHub Pages**: GitHub Actions workflow logs
- **Application Logs**: Structured JSON logs with correlation IDs