# OAuth Provider Setup Guide for Production

This guide will help you configure Google, Microsoft, and Apple OAuth providers for your MMT app in production.

## Prerequisites

1. **Backend deployed to Railway** with the following environment variables configured
2. **Frontend deployed to GitHub Pages** at `https://webqx.github.io/MMT/`

## Required Railway Environment Variables

Add these to your Railway backend service:

```bash
# OAuth Configuration
OAUTH_BACKEND_BASE_URL=https://mmt-backend-production.up.railway.app
OAUTH_FRONTEND_REDIRECT_URL=https://webqx.github.io/MMT/

# Provider-specific credentials (to be filled after setup)
OAUTH_GOOGLE_CLIENT_ID=your_google_client_id
OAUTH_GOOGLE_CLIENT_SECRET=your_google_client_secret

OAUTH_MICROSOFT_CLIENT_ID=your_microsoft_client_id
OAUTH_MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret

OAUTH_APPLE_CLIENT_ID=your_apple_client_id
OAUTH_APPLE_CLIENT_SECRET=your_apple_client_secret
```

## 1. Google OAuth Setup

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the "Google+ API" and "OAuth2 API"

### Step 2: Configure OAuth Consent Screen
1. Go to **APIs & Services > OAuth consent screen**
2. Choose **External** user type
3. Fill in required fields:
   - **App name**: MMT - Medical Transcription Tool
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. Add authorized domains:
   - `webqx.github.io`
   - `up.railway.app`

### Step 3: Create OAuth Credentials
1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth 2.0 Client IDs**
3. Choose **Web application**
4. Set **Authorized JavaScript origins**:
   - `https://webqx.github.io`
   - `https://mmt-backend-production.up.railway.app`
5. Set **Authorized redirect URIs**:
   - `https://mmt-backend-production.up.railway.app/auth/oauth/google/callback`
6. Save and copy the **Client ID** and **Client Secret**

### Step 4: Update Railway Environment
```bash
OAUTH_GOOGLE_CLIENT_ID=your_actual_google_client_id
OAUTH_GOOGLE_CLIENT_SECRET=your_actual_google_client_secret
```

## 2. Microsoft OAuth Setup

### Step 1: Register App in Azure Portal
1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory > App registrations**
3. Click **New registration**
4. Fill in:
   - **Name**: MMT Medical Transcription Tool
   - **Supported account types**: Accounts in any organizational directory and personal Microsoft accounts
   - **Redirect URI**: Web - `https://mmt-backend-production.up.railway.app/auth/oauth/microsoft/callback`

### Step 2: Configure Authentication
1. Go to **Authentication** in your app registration
2. Add additional redirect URIs if needed
3. Under **Implicit grant and hybrid flows**, enable:
   - Access tokens
   - ID tokens

### Step 3: Add API Permissions
1. Go to **API permissions**
2. Add the following Microsoft Graph permissions:
   - `openid`
   - `email`
   - `profile`
   - `offline_access`

### Step 4: Create Client Secret
1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Add description and set expiration
4. Copy the **Value** (this is your client secret)

### Step 5: Update Railway Environment
```bash
OAUTH_MICROSOFT_CLIENT_ID=your_application_id_from_azure
OAUTH_MICROSOFT_CLIENT_SECRET=your_client_secret_value
```

## 3. Apple OAuth Setup

### Step 1: Apple Developer Account
1. You need a paid Apple Developer account ($99/year)
2. Go to [Apple Developer Portal](https://developer.apple.com/)

### Step 2: Create App ID
1. Go to **Certificates, Identifiers & Profiles**
2. Click **Identifiers > App IDs**
3. Create new App ID:
   - **Description**: MMT Medical Transcription
   - **Bundle ID**: `com.webqx.mmt` (or your chosen identifier)
   - Enable **Sign In with Apple**

### Step 3: Create Services ID
1. Go to **Identifiers > Services IDs**
2. Create new Services ID:
   - **Description**: MMT Web Service
   - **Identifier**: `com.webqx.mmt.web`
   - Enable **Sign In with Apple**
3. Configure **Sign In with Apple**:
   - **Primary App ID**: Select the App ID created above
   - **Web Domain**: `webqx.github.io`
   - **Return URLs**: `https://mmt-backend-production.up.railway.app/auth/oauth/apple/callback`

### Step 4: Create Private Key
1. Go to **Keys**
2. Create new key:
   - **Key Name**: MMT Apple Sign In Key
   - Enable **Sign In with Apple**
   - Select your App ID
3. Download the `.p8` key file and note the **Key ID**

### Step 5: Generate Client Secret
Apple requires generating a JWT as the client secret. Use this Python script:

```python
import jwt
import time
from datetime import datetime, timedelta

# Your Apple Developer information
TEAM_ID = "your_team_id"  # Found in Apple Developer Account
KEY_ID = "your_key_id"    # From the key you created
CLIENT_ID = "com.webqx.mmt.web"  # Your Services ID

# Read the private key
with open("AuthKey_YOUR_KEY_ID.p8", "r") as f:
    private_key = f.read()

# Create JWT
headers = {
    "alg": "ES256",
    "kid": KEY_ID
}

payload = {
    "iss": TEAM_ID,
    "iat": int(time.time()),
    "exp": int(time.time()) + 86400 * 180,  # 180 days
    "aud": "https://appleid.apple.com",
    "sub": CLIENT_ID
}

client_secret = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
print(f"Apple Client Secret: {client_secret}")
```

### Step 6: Update Railway Environment
```bash
OAUTH_APPLE_CLIENT_ID=com.webqx.mmt.web
OAUTH_APPLE_CLIENT_SECRET=your_generated_jwt_token
```

## 4. Deploy and Test

### Step 1: Deploy Backend
1. Go to GitHub Actions in your repository
2. Manually trigger the "Deploy Backend Production to Railway" workflow
3. Wait for deployment to complete

### Step 2: Deploy Frontend
1. Commit and push your changes to the main branch
2. This will trigger the GitHub Pages deployment automatically

### Step 3: Test OAuth Flows
1. Visit `https://webqx.github.io/MMT/`
2. Try logging in with each provider:
   - Google
   - Microsoft  
   - Apple (only works on Safari/iOS for full testing)

## Troubleshooting

### Common Issues

1. **"OAuth not configured" error**
   - Check that environment variables are set in Railway
   - Restart the Railway service after adding variables

2. **Redirect URI mismatch**
   - Ensure redirect URIs in provider settings match exactly:
   - `https://mmt-backend-production.up.railway.app/auth/oauth/{provider}/callback`

3. **CORS errors**
   - Check that your domains are properly configured in OAuth providers
   - Ensure Railway backend allows requests from GitHub Pages

4. **Apple Sign In not working**
   - Apple Sign In requires HTTPS in production
   - Test on Safari or iOS devices for full compatibility
   - Ensure JWT token hasn't expired (regenerate if needed)

### Verification Commands

Test that OAuth endpoints are working:

```bash
# Test Google OAuth authorize endpoint
curl "https://mmt-backend-production.up.railway.app/auth/oauth/google/authorize"

# Test Microsoft OAuth authorize endpoint  
curl "https://mmt-backend-production.up.railway.app/auth/oauth/microsoft/authorize"

# Test Apple OAuth authorize endpoint
curl "https://mmt-backend-production.up.railway.app/auth/oauth/apple/authorize"
```

Each should return a JSON response with an `authorize_url` field.

## Security Notes

1. **Client Secrets**: Keep all client secrets secure and never commit them to code
2. **Redirect URIs**: Only add necessary redirect URIs to prevent misuse
3. **Scopes**: Only request minimum necessary OAuth scopes
4. **Token Rotation**: Regularly rotate Apple JWT tokens (they expire)
5. **Domain Verification**: Ensure all domains are properly verified with providers

## Next Steps

After successful OAuth setup:
1. Test user registration and login flows
2. Set up user profile management
3. Configure user session handling
4. Add logout functionality
5. Test on multiple devices and browsers