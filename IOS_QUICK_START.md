# iOS Deployment Quick Start Guide

## 🎯 What You Need to Do Now

### 1. Enroll in Apple Developer Program (START HERE)
**This is the first and most important step!**

1. Go to: https://developer.apple.com/programs/enroll/
2. Sign in with your Apple ID (or create one)
3. Click "Enroll" and choose account type:
   - **Individual**: $99/year, your name as seller
   - **Organization**: $99/year, company name as seller (requires D-U-N-S number)
4. Complete payment ($99)
5. Wait for approval (24-48 hours for individuals)

**You cannot proceed with other steps until this is approved.**

### 2. While Waiting for Approval

Read these documents to prepare:
- `APPLE_DEVELOPER_SETUP.md` - Complete setup guide
- `IOS_DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist

### 3. After Approval - Create Your App

1. **Log into App Store Connect**: https://appstoreconnect.apple.com

2. **Create New App**:
   - Click "My Apps" → "+" → "New App"
   - Platform: iOS
   - Name: MMT - Medical Transcription (or your choice)
   - Language: English
   - **Bundle ID**: Click "+" to create new
     - Format: `com.yourcompany.mmt` or `com.yourdomain.mmt`
     - Example: `com.medtech.mmt`
     - **IMPORTANT**: Must be unique, cannot change later!
   - SKU: MMT-001 (or any unique identifier)

3. **Record This Information**:
   ```
   Apple ID: __________________ (your email)
   Team ID: __________________ (from developer.apple.com → Membership)
   Team Name: __________________
   Bundle ID: __________________ (the one you just created)
   App Store Connect Team ID: __________________ (from Users and Access)
   ```

### 4. Create App Store Connect API Key

**This allows GitHub Actions to deploy automatically**

1. Go to: https://appstoreconnect.apple.com/access/api
2. Click "+" to create new key
3. Name: "GitHub Actions CI"
4. Access: "App Manager"
5. Click "Generate"
6. **DOWNLOAD THE .p8 FILE IMMEDIATELY** (only shown once!)
7. Record:
   - Key ID: __________________
   - Issuer ID: __________________
   - Save the .p8 file in a secure location

### 5. Update Your Project's Bundle Identifier

```bash
# From the repository root
./scripts/update_bundle_id.sh com.yourcompany.mmt

# Replace com.yourcompany.mmt with YOUR bundle ID from step 3
```

### 6. Configure GitHub Secrets

Go to: https://github.com/WebQx/MMT/settings/secrets/actions

Click "New repository secret" for each of these:

#### Basic Information:
| Secret Name | Value | Where to Get It |
|------------|-------|----------------|
| `APPLE_ID` | Your Apple Developer email | Your account |
| `APPLE_TEAM_ID` | Team ID | developer.apple.com → Membership |
| `APP_STORE_CONNECT_TEAM_ID` | Team ID | appstoreconnect.apple.com → Users and Access |
| `IOS_BUNDLE_ID` | Your bundle ID | The one you created (e.g., com.yourcompany.mmt) |

#### API Key (from step 4):
| Secret Name | Value | How to Get |
|------------|-------|------------|
| `APP_STORE_CONNECT_API_KEY_ID` | Key ID | From API key page |
| `APP_STORE_CONNECT_API_ISSUER_ID` | Issuer ID | From API key page |
| `APP_STORE_CONNECT_API_KEY_CONTENT` | Base64 of .p8 file | `base64 -i AuthKey_XXXXXX.p8 \| pbcopy` |

#### Certificates (Need a Mac for this - see option below if you don't have one):

If you have a Mac:

1. **Create Distribution Certificate**:
   ```bash
   # In Keychain Access:
   # 1. Certificate Assistant → Request a Certificate from CA
   # 2. Save to disk
   
   # In developer.apple.com → Certificates:
   # 3. Create "iOS Distribution" certificate
   # 4. Upload the request file
   # 5. Download and install the certificate
   
   # Export as .p12:
   # 6. In Keychain Access, find certificate
   # 7. Right-click → Export → Save as .p12
   # 8. Set a strong password
   ```

2. **Add these secrets**:
   | Secret Name | Value | How to Get |
   |------------|-------|------------|
   | `IOS_DISTRIBUTION_CERTIFICATE_BASE64` | Base64 of .p12 | `base64 -i certificate.p12 \| pbcopy` |
   | `IOS_DISTRIBUTION_CERTIFICATE_PASSWORD` | Password you set | From export step |
   | `KEYCHAIN_PASSWORD` | Random password | `openssl rand -base64 32` |

3. **Download Provisioning Profile**:
   ```bash
   # In developer.apple.com → Profiles:
   # 1. Create "App Store" provisioning profile
   # 2. Select your app ID and distribution certificate
   # 3. Download the .mobileprovision file
   ```

4. **Add secret**:
   | Secret Name | Value | How to Get |
   |------------|-------|------------|
   | `IOS_PROVISIONING_PROFILE_BASE64` | Base64 of profile | `base64 -i profile.mobileprovision \| pbcopy` |

**Don't have a Mac?** You can use fastlane match (see APPLE_DEVELOPER_SETUP.md for alternative approach)

### 7. Deploy to TestFlight

Once all secrets are configured:

**Option A: Automatic (on push to main)**:
```bash
git commit -m "feat: my changes [ios-deploy]"
git push origin main
```

**Option B: Manual dispatch**:
1. Go to: https://github.com/WebQx/MMT/actions
2. Click "iOS Build and Deploy"
3. Click "Run workflow"
4. Select "Deploy to TestFlight: true"
5. Click "Run workflow"

### 8. Monitor Deployment

1. Watch GitHub Actions: https://github.com/WebQx/MMT/actions
2. Once complete, check App Store Connect → TestFlight
3. Wait 10-60 minutes for Apple to process the build
4. Add test information and invite testers

### 9. Invite Beta Testers

1. In App Store Connect → TestFlight
2. Add internal testers (up to 100, no review needed)
3. Or add external testers (up to 10,000, requires Apple review)
4. Testers get email, install TestFlight app, accept invitation

## 📁 Files Created

- `APPLE_DEVELOPER_SETUP.md` - Comprehensive setup guide
- `IOS_DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist
- `.github/workflows/ios-deploy.yml` - CI/CD workflow
- `app/ios/fastlane/Fastfile` - Deployment automation
- `app/ios/fastlane/Appfile` - Apple ID configuration
- `scripts/update_bundle_id.sh` - Bundle ID update script

## ⏱️ Timeline

- **Today**: Enroll in Apple Developer Program
- **Day 1-2**: Wait for approval
- **Day 2**: Configure app in App Store Connect
- **Day 2**: Set up certificates and GitHub secrets
- **Day 2**: First TestFlight build (via GitHub Actions)
- **Day 2**: Wait for Apple processing (10-60 min)
- **Day 2-3**: Internal testing begins
- **Day 3-4**: Submit for external beta review (if needed)
- **Week 1-2**: Beta testing
- **Week 2+**: Submit to App Store for review

## 🆘 Common Issues

**"Bundle ID already registered"**
→ Choose a different bundle ID

**"No valid code signing identity found"**
→ Create/import distribution certificate

**"GitHub Actions fails on signing"**
→ Check all secrets are correctly base64-encoded

**"App Store Connect processing stuck"**
→ Wait patiently, can take up to 1 hour

## 📚 Documentation

- Full Setup: `APPLE_DEVELOPER_SETUP.md`
- Checklist: `IOS_DEPLOYMENT_CHECKLIST.md`
- Apple Developer: https://developer.apple.com
- App Store Connect: https://appstoreconnect.apple.com

## 🎉 Success Criteria

✅ Apple Developer account approved
✅ App created in App Store Connect
✅ Bundle ID updated in project
✅ GitHub secrets configured
✅ First build successfully uploaded to TestFlight
✅ Beta testers can install and test the app

## 💡 Pro Tips

1. **Start enrollment ASAP** - it's the longest wait
2. **Choose bundle ID carefully** - cannot change after submission
3. **Test locally first** if you have a Mac
4. **Use internal testers** for quick testing (no review)
5. **Keep .p8 API key secure** - cannot be downloaded again
6. **Document your passwords** - you'll need them for secrets
7. **Read App Store Review Guidelines** before final submission

## Next Steps After TestFlight

Once beta testing is successful:
1. Gather and add App Store screenshots
2. Write app description and keywords
3. Create privacy policy (required)
4. Submit for App Store review
5. Wait 24-72 hours for review
6. Release to the public!

Good luck! 🚀
