# MMT Deployment Ready Guide

This guide will help you deploy the MMT (Medical Transcription Tool) backend to Railway and frontend to GitHub Pages.

## 🚀 Deployment Overview

- **Backend**: Deploys to Railway via GitHub Actions
- **Frontend**: Deploys to GitHub Pages via GitHub Actions
- **Automatic**: Railway deployment triggers only after all CI/CD tests pass successfully

## 📋 Pre-Deployment Checklist

### 1. Railway Setup

#### Required Railway Secrets in GitHub Repository
Go to `Settings > Secrets and variables > Actions` and add:

- `RAILWAY_TOKEN`: Your Railway API token
  - Get this from Railway Dashboard > Account Settings > Tokens
  - Generate a new token with deployment permissions

#### Optional Railway Secrets for Production Features
- `REMOTE_API_BASE_URL`: Your Railway app URL (e.g., `https://your-app.railway.app`)
- `ADMIN_API_KEY`: Admin API key for smoke testing the deployed backend

### 2. Frontend (GitHub Pages) Setup

#### Required GitHub Pages Configuration
1. Go to `Settings > Pages`
2. Set Source to "Deploy from a branch"
3. Select `gh-pages` branch
4. Set folder to `/ (root)`

#### Optional Frontend Secrets
- `PUBLIC_BACKEND_URL`: Production backend URL for frontend (your Railway URL)
- `PROD_BASE_URL`: Alternative production base URL
- `OPENAI_API_KEY`: For OpenAI Whisper integration in frontend

### 3. Backend Configuration

#### Environment Variables to Set in Railway
Configure these in your Railway service environment:

**Core Settings:**
```bash
# API Configuration
OPENAI_API_KEY=your_openai_api_key_here
KEYCLOAK_ISSUER=https://your-keycloak.com/realms/mmt
KEYCLOAK_PUBLIC_KEY=your_keycloak_public_key

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Security
GUEST_SECRET=your_secure_guest_secret
ALLOW_LOCAL_LOGIN=false  # Set to false for production

# Application
ENV=prod
PORT=9000
HOST=0.0.0.0
```

**ML/Transcription Settings (Optional):**
```bash
# Enable if you want local Whisper transcription
ENABLE_LOCAL_TRANSCRIPTION=false
WHISPER_MODEL_SIZE=base

# Enable if you want PII detection
ENABLE_PII_DETECTION=false
```

## 🔄 Deployment Workflow

### Automatic Deployment Process

1. **Push to `main` branch** triggers:
   - `MMT CI/CD` workflow (backend tests, frontend tests, GitHub Pages deploy)
   - `security-scan` workflow (dependency and Docker security scanning)  
   - `Mobile CI` workflow (Flutter mobile app testing)

2. **After ALL workflows complete successfully**:
   - `Deploy Backend to Railway` workflow automatically triggers
   - Deploys backend to Railway
   - Runs smoke tests to verify deployment
   - Optionally creates release tags

### Manual Deployment

You can manually trigger Railway deployment:
1. Go to `Actions > Deploy Backend to Railway`
2. Click "Run workflow"
3. Optionally specify:
   - Release tag to create after successful deploy
   - Whether to include ML dependencies

## 🏗️ Deployment Commands

### To Deploy Everything
```bash
# Push to main branch - this will trigger all workflows
git push origin main
```

### To Deploy Frontend Only
The frontend deploys as part of the main CI/CD workflow and also has a dedicated GitHub Pages workflow.

### To Deploy Backend Only (Manual)
Use the GitHub Actions interface to manually trigger the Railway backend deployment.

## 🧪 Testing Deployment

### Frontend Testing
1. After deployment, visit: `https://your-username.github.io/MMT/`
2. Verify the app loads and connects to your backend
3. Test core functionality like transcription

### Backend Testing
1. Check Railway dashboard for deployment status
2. Visit health endpoint: `https://your-app.railway.app/health/live`
3. Check demo status: `https://your-app.railway.app/demo/status`
4. Verify demo_mode is false for production

## 🔧 Configuration Options

### Backend Deployment Options

#### Light Mode (Default)
- Uses `requirements.light.txt`
- Excludes heavy ML dependencies (Whisper, Torch, Spacy)
- Faster deployment, smaller memory footprint
- Best for cloud-based transcription services

#### Full ML Mode
- Uses `requirements.txt` with full ML stack
- Includes local Whisper transcription capabilities
- Requires more memory and longer deployment time
- Enable by setting `include_ml: true` in manual deployment

### Frontend Build Options

The frontend can be built with different configurations:
- Default: Connects to localhost backend (development)
- Production: Uses `PUBLIC_BACKEND_URL` secret for backend connection
- Custom: Set specific base URLs via workflow dispatch

## 🚨 Troubleshooting

### Railway Deployment Issues

1. **RAILWAY_TOKEN not set**
   - Ensure you've added the Railway token to GitHub secrets
   - Token must have deployment permissions

2. **Deployment timeout**
   - Check Railway logs for detailed error messages
   - Consider using light mode if full ML stack times out

3. **Health check failures**
   - Verify environment variables are set correctly
   - Check Railway service logs for startup errors

### Frontend Deployment Issues

1. **GitHub Pages not updating**
   - Check if GitHub Pages is enabled
   - Verify `gh-pages` branch exists and is set as source
   - Check workflow logs for deployment errors

2. **Frontend can't connect to backend**
   - Verify `PUBLIC_BACKEND_URL` secret is set correctly
   - Check CORS configuration in backend
   - Ensure Railway backend is running and accessible

### Workflow Dependency Issues

1. **Railway deployment not triggering**
   - Ensure all prerequisite workflows completed successfully
   - Check that workflow names match exactly:
     - "MMT CI/CD"
     - "security-scan" 
     - "Mobile CI"

2. **Tests failing**
   - Backend tests: Check Python syntax and dependencies
   - Frontend tests: Verify Flutter configuration
   - Security scan: Review dependency vulnerabilities

## 🎯 Next Steps After Deployment

1. **Monitor the deployments**
   - Check Railway dashboard for backend health
   - Verify GitHub Pages deployment succeeded
   - Test end-to-end functionality

2. **Set up monitoring**
   - Configure Railway alerts
   - Set up health check monitoring
   - Monitor application logs

3. **Configure production settings**
   - Review and secure all environment variables
   - Set up proper authentication (Keycloak)
   - Configure database backups
   - Set up SSL certificates if needed

4. **Test thoroughly**
   - Test all transcription features
   - Verify user authentication flows
   - Test file upload and processing
   - Validate OpenEMR integration (if used)

## 📞 Support

If you encounter issues:
1. Check the workflow logs in GitHub Actions
2. Review Railway deployment logs
3. Verify all required secrets are set
4. Ensure environment variables match your configuration needs

Happy deploying! 🚀