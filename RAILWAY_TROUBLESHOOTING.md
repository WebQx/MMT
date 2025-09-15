# Railway Deployment Troubleshooting Guide

## Common Error Patterns to Look For

### 1. Build Errors
```
✖ Railpack could not determine how to build the app
Script start.sh not found
```
**Solution**: This should be fixed with our new `run.py` and `nixpacks.toml`

### 2. Python/Dependencies Issues
```
ModuleNotFoundError: No module named 'uvicorn'
ModuleNotFoundError: No module named 'gunicorn'
ModuleNotFoundError: No module named 'fastapi'
```
**Solution**: Check if `requirements.txt` includes all dependencies

### 3. Environment Variable Errors
```
RuntimeError: Explicit strong INTERNAL_JWT_SECRET (>=32 chars) required in prod
```
**Solution**: This should be fixed with our railway.toml configuration

### 4. Port Binding Issues
```
Error: Could not bind to 0.0.0.0:8000
Address already in use
```
**Solution**: Railway should automatically assign PORT variable

### 5. Application Import Errors
```
ImportError: cannot import name 'app' from 'main'
ModuleNotFoundError: No module named 'main'
```
**Solution**: Check if main.py exists and exports 'app'

## Diagnostic Steps

1. Check if the build phase completes successfully
2. Look for Python import errors during startup
3. Check if the health endpoint `/health/live` is accessible
4. Verify environment variables are set correctly

## If You See Specific Errors

Please share the exact error messages from Railway logs, and I can provide targeted fixes.

## Quick Test Commands

Once deployed, test with:
```bash
curl https://mmt-backend-production.up.railway.app/health/live
```

Expected response:
```json
{"status":"live"}
```