# Apple Developer Account Setup & iOS App Store Deployment Guide

## Prerequisites

### 1. Apple Developer Account Enrollment
- **Cost**: $99 USD per year
- **URL**: https://developer.apple.com/programs/enroll/
- **Requirements**:
  - Apple ID
  - Payment method (credit card)
  - D-U-N-S Number (for organizations)
  - Government-issued photo ID

### 2. Account Types
- **Individual**: Personal Apple ID, your name appears as seller
- **Organization**: Company name appears, requires D-U-N-S number and legal entity verification

## Step 1: Enroll in Apple Developer Program

1. **Visit Apple Developer**:
   ```
   https://developer.apple.com/programs/
   ```

2. **Sign in with Apple ID** or create one

3. **Click "Enroll"** and follow steps:
   - Accept terms and conditions
   - Choose account type (Individual/Organization)
   - Complete identity verification
   - Pay $99 annual fee

4. **Wait for approval** (usually 24-48 hours for individuals, 1-2 weeks for organizations)

## Step 2: App Store Connect Setup

### Create App ID and Bundle Identifier

1. **Log into App Store Connect**:
   ```
   https://appstoreconnect.apple.com
   ```

2. **Go to "My Apps" → "+" → "New App"**

3. **Configure App Information**:
   - **Platform**: iOS
   - **Name**: MMT - Medical Transcription (or your preferred name)
   - **Primary Language**: English
   - **Bundle ID**: Create new → `com.yourcompany.mmt` (replace `yourcompany` with your team name)
   - **SKU**: `MMT-001` (unique identifier for your records)

4. **User Access**: Full Access

### Required App Information

Fill in these required fields in App Store Connect:

1. **Privacy Policy URL**: Required for all apps
   - Must be a live, accessible URL
   - Should explain data collection and usage

2. **App Description**:
   ```
   MMT (Multilingual Medical Transcription) - Professional medical transcription app 
   for healthcare providers. Record, transcribe, and manage patient notes securely 
   with multilingual support and HIPAA-compliant features.
   ```

3. **Keywords**: medical, transcription, healthcare, doctor, notes, speech-to-text

4. **Support URL**: Your support website or GitHub page

5. **Marketing URL** (optional): Your app website

## Step 3: Certificates and Provisioning Profiles

### A. Development Certificates (for local testing)

1. **In Xcode**:
   - Open project: `/workspaces/MMT/app/ios/Runner.xcworkspace`
   - Select "Runner" in Project Navigator
   - Go to "Signing & Capabilities" tab
   - Check "Automatically manage signing"
   - Select your Team from dropdown
   - Xcode will create development certificates automatically

### B. Distribution Certificates (for App Store/TestFlight)

**Option 1: Manual Setup** (if you have a Mac):

1. **Open Keychain Access** on Mac:
   - Keychain Access → Certificate Assistant → Request a Certificate from a Certificate Authority
   - Enter your email and name
   - Select "Saved to disk"
   - Save the `.certSigningRequest` file

2. **In Apple Developer Portal**:
   ```
   https://developer.apple.com/account/resources/certificates/list
   ```
   - Click "+" to create new certificate
   - Select "iOS Distribution (App Store and Ad Hoc)"
   - Upload the `.certSigningRequest` file
   - Download the certificate (`.cer` file)
   - Double-click to install in Keychain

3. **Export Certificate**:
   - Open Keychain Access
   - Find your distribution certificate
   - Right-click → Export
   - Save as `.p12` file with a strong password
   - **KEEP THIS PASSWORD SECURE** - you'll need it for CI/CD

**Option 2: Fastlane Match** (recommended for CI/CD):
```bash
# Install fastlane
gem install fastlane

# Initialize match
cd app/ios
fastlane match init

# Follow prompts to set up a private Git repo for certificates
```

## Step 4: Configure iOS Project

### Update Bundle Identifier

Your current bundle ID: `com.example.mmt`

**You need to change this to a unique identifier that matches your App Store Connect app.**

Recommended format: `com.yourcompany.mmt` or `com.yourdomain.mmt`

### Required Permissions (Info.plist)

For MMT app functionality, add these to `app/ios/Runner/Info.plist`:

```xml
<!-- Microphone access for audio recording -->
<key>NSMicrophoneUsageDescription</key>
<string>This app needs access to the microphone to record medical transcriptions.</string>

<!-- Speech Recognition -->
<key>NSSpeechRecognitionUsageDescription</key>
<string>This app uses speech recognition to transcribe your medical notes.</string>

<!-- Photo Library (if app saves/loads files) -->
<key>NSPhotoLibraryUsageDescription</key>
<string>This app needs access to your photo library to save transcription documents.</string>

<!-- Camera (if app has photo/video features) -->
<key>NSCameraUsageDescription</key>
<string>This app needs camera access for capturing medical documentation.</string>
```

## Step 5: TestFlight Beta Testing

### First TestFlight Build

1. **Archive the app** (after all configurations):
   ```bash
   cd app
   flutter build ios --release
   ```

2. **In Xcode**:
   - Open `ios/Runner.xcworkspace`
   - Select "Any iOS Device" as destination
   - Product → Archive
   - Once archived, click "Distribute App"
   - Select "App Store Connect"
   - Select "Upload"
   - Follow prompts to upload

3. **Processing in App Store Connect**:
   - Go to TestFlight tab in App Store Connect
   - Wait for processing (can take 10-60 minutes)
   - Once processed, add test information
   - Add internal testers (up to 100)
   - Submit for beta review (required for external testing)

### External Testing

- Add external test groups
- Up to 10,000 external testers
- Requires Apple review (usually 24-48 hours)
- Testers receive email invitation

## Step 6: Secrets Required for CI/CD

Store these securely in GitHub Secrets:

### Required Secrets:

1. **APPLE_ID**: Your Apple Developer account email
2. **APP_STORE_CONNECT_API_KEY_ID**: App Store Connect API key ID
3. **APP_STORE_CONNECT_API_ISSUER_ID**: Issuer ID
4. **APP_STORE_CONNECT_API_KEY_CONTENT**: Base64-encoded API key (.p8 file)
5. **MATCH_PASSWORD**: Password for fastlane match repository
6. **CERTIFICATE_PASSWORD**: Password for your distribution certificate (.p12)
7. **PROVISIONING_PROFILE**: Base64-encoded provisioning profile

### How to Create App Store Connect API Key:

1. Go to: https://appstoreconnect.apple.com/access/api
2. Click "+" to create new key
3. **Name**: "GitHub Actions CI"
4. **Access**: "App Manager" or "Developer"
5. Download the `.p8` file (ONLY AVAILABLE ONCE!)
6. Note the Key ID and Issuer ID

To base64 encode the API key:
```bash
base64 -i AuthKey_XXXXXXXX.p8 | pbcopy
```

## Step 7: App Store Submission

### Pre-Submission Checklist

- [ ] App successfully tested on TestFlight
- [ ] All required metadata filled in App Store Connect
- [ ] Screenshots for all required device sizes
- [ ] App icon (1024x1024 px, no transparency, no rounded corners)
- [ ] Privacy Policy URL active
- [ ] App Export Compliance filled out
- [ ] Age rating completed
- [ ] Pricing and availability set

### Submission Process

1. **In App Store Connect**:
   - Go to your app → "1.0 Prepare for Submission"
   - Fill all required fields:
     - Screenshots (iPhone 6.7" and 5.5" required, iPad 12.9" if supporting iPad)
     - Description
     - Keywords
     - Support URL
     - Marketing URL (optional)
     - App icon
     - Version number
     - Copyright
     - Age rating
     - App Review Information (contact info for reviewers)
     - Version Release (automatic or manual)

2. **Select Build**:
   - Click "+" next to Build
   - Select your TestFlight build

3. **Submit for Review**:
   - Click "Submit for Review"
   - Answer export compliance questions
   - Answer advertising identifier questions
   - Submit

4. **Wait for Review**:
   - Usually 24-72 hours
   - You'll receive status updates via email
   - May request additional information

## Step 8: Post-Approval

Once approved:
- **Automatic Release**: App goes live immediately
- **Manual Release**: You control when it goes live
- **Phased Release**: Gradual rollout to users over 7 days

## Bundle Identifier Setup

### Current Configuration
- Current: `com.example.mmt`
- **Change to**: `com.yourteam.mmt` (or your preferred domain)

### Where to Update:

1. **Xcode Project**:
   - Open `ios/Runner.xcworkspace`
   - Select "Runner" target
   - General tab → Bundle Identifier

2. **App Store Connect**:
   - Must match exactly

3. **GitHub Actions** (when we set it up):
   - Will be configured to use the correct bundle ID

## Cost Summary

- **Apple Developer Program**: $99/year
- **Optional: Physical devices for testing**: Variable
- **Optional: Mac for local building**: One-time (can use GitHub Actions instead)

## Next Steps

1. ✅ Enroll in Apple Developer Program
2. ✅ Create app in App Store Connect
3. ✅ Decide on your bundle identifier
4. ⏳ Update iOS project configuration (we'll do this next)
5. ⏳ Set up fastlane for automation
6. ⏳ Configure GitHub Actions for CI/CD
7. ⏳ Build and upload first TestFlight build

## Resources

- Apple Developer Portal: https://developer.apple.com
- App Store Connect: https://appstoreconnect.apple.com
- Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines/
- App Store Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- Fastlane Documentation: https://docs.fastlane.tools/
- TestFlight: https://developer.apple.com/testflight/

## Support

For issues during setup:
- Apple Developer Support: https://developer.apple.com/support/
- App Store Connect Help: https://help.apple.com/app-store-connect/
