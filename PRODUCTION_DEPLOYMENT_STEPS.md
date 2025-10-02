# Quick Production Deployment Guide

## What I've Done

✅ **Updated Frontend Configuration**:
- Set `allowOfflineAuth = kDebugMode` (false in production builds)
- Updated `baseUrl` to use Railway backend in production
- Modified GitHub Pages workflow to use Railway backend URL

✅ **Backend Configuration Ready**:
- Railway deployment workflow is configured
- Environment variables template ready
- OAuth endpoints implemented and tested

✅ **OAuth Setup Guide Created**:
- Complete instructions for Google, Microsoft, and Apple OAuth
- Step-by-step provider configuration
- Security best practices included

## Next Steps for You

### 1. Deploy Backend to Railway (Required)

Go to your GitHub repository:
1. Navigate to **Actions** tab
2. Find "Deploy Backend Production to Railway" workflow
3. Click "Run workflow"
4. Set parameters:
   - `production_mode`: `true`
   - `include_ml`: `false` (for faster deployment)
5. Click "Run workflow"

**Required Railway Environment Variables** (set these in Railway dashboard):
```bash
# Core settings
ENV=prod
DEMO_MODE=false
ALLOW_GUEST_AUTH=true

# OAuth (after setting up providers)
OAUTH_BACKEND_BASE_URL=https://mmt-backend-production.up.railway.app
OAUTH_FRONTEND_REDIRECT_URL=https://webqx.github.io/MMT/
```

### 2. Set Up OAuth Providers

Follow the detailed guide in `OAUTH_SETUP_GUIDE.md`:

1. **Google OAuth** - Easiest to set up first
2. **Microsoft OAuth** - Good for enterprise users  
3. **Apple OAuth** - Requires paid developer account

### 3. Deploy Frontend

After backend is running:
1. Commit and push current changes to `main` branch
2. GitHub Actions will automatically deploy to GitHub Pages with production backend URL

### 4. Test Production App

Visit: `https://webqx.github.io/MMT/`

**Expected behavior**:
- ✅ App loads without "Demo mode" warnings
- ✅ OAuth login buttons attempt to redirect to providers
- ✅ Guest login still works for testing
- ❌ OAuth logins will fail until providers are configured

## Current Status

🎯 **Ready for OAuth Configuration**: Your app infrastructure is production-ready. You just need to:

1. **Deploy the backend** (5 minutes via GitHub Actions)
2. **Configure OAuth providers** (30-60 minutes total)
3. **Test the complete flow** (5 minutes)

## Quick Test Commands

Once backend is deployed, test OAuth endpoints:

```bash
# Should return JSON with authorize_url
curl "https://mmt-backend-production.up.railway.app/auth/oauth/google/authorize"

# Should return 400 "not configured" until you add OAuth credentials
curl "https://mmt-backend-production.up.railway.app/auth/oauth/microsoft/authorize"
curl "https://mmt-backend-production.up.railway.app/auth/oauth/apple/authorize"
```

## Support

If you encounter issues:
1. Check Railway deployment logs in the Railway dashboard
2. Verify environment variables are set correctly
3. Test OAuth endpoints with curl commands
4. Check browser console for frontend errors

The app architecture is solid - it's just a matter of deploying and configuring the OAuth providers! 🚀