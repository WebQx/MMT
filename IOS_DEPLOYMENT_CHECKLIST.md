# iOS TestFlight Deployment Checklist

## Phase 1: Apple Developer Account Setup

- [ ] **Enroll in Apple Developer Program**
  - Visit: https://developer.apple.com/programs/enroll/
  - Cost: $99/year
  - Wait for approval (24-48 hours for individuals)

- [ ] **Gather Account Information**
  - [ ] Apple ID email
  - [ ] Team ID (found in developer.apple.com → Membership)
  - [ ] Team Name

## Phase 2: App Store Connect Configuration

- [ ] **Create App in App Store Connect**
  - Visit: https://appstoreconnect.apple.com
  - Click "My Apps" → "+" → "New App"
  - Platform: iOS
  - Name: MMT - Medical Transcription (or your choice)
  - Primary Language: English
  - **Bundle ID**: Choose and create (e.g., `com.yourcompany.mmt`)
  - SKU: MMT-001 (or your choice)

- [ ] **Record App Information**
  - [ ] App Store Connect Team ID
  - [ ] Bundle ID chosen
  - [ ] App ID (numeric, shown in App Store Connect)

- [ ] **Create App Store Connect API Key**
  - Go to: https://appstoreconnect.apple.com/access/api
  - Click "+" to create key
  - Name: "GitHub Actions CI"
  - Access: "App Manager"
  - **DOWNLOAD THE .p8 FILE** (only available once!)
  - Record:
    - [ ] Key ID
    - [ ] Issuer ID
    - [ ] Save the .p8 file securely

## Phase 3: Certificates and Provisioning

### Option A: Using Xcode (Requires Mac)

- [ ] **Open Project in Xcode**
  ```bash
  cd app/ios
  open Runner.xcworkspace
  ```

- [ ] **Update Bundle Identifier**
  - Select "Runner" in project navigator
  - Go to "Signing & Capabilities" tab
  - Update Bundle Identifier to match App Store Connect

- [ ] **Configure Signing**
  - Check "Automatically manage signing"
  - Select your Team from dropdown
  - Xcode will create certificates automatically

- [ ] **Create Distribution Certificate**
  - Keychain Access → Certificate Assistant → Request Certificate
  - Developer Portal → Certificates → "+" → iOS Distribution
  - Upload request, download certificate
  - Double-click to install

- [ ] **Export Certificate as .p12**
  - Keychain Access → Find certificate
  - Right-click → Export → Save as .p12
  - **Set a strong password**
  - Record password securely

### Option B: Using Fastlane Match (Recommended for CI/CD)

- [ ] **Install Fastlane**
  ```bash
  gem install fastlane
  ```

- [ ] **Initialize Match**
  ```bash
  cd app/ios
  fastlane match init
  ```

- [ ] **Create Private Certificates Repository**
  - Create private GitHub repo: `certificates-mmt`
  - Grant access to CI/CD service account

- [ ] **Run Match**
  ```bash
  fastlane match appstore
  ```

## Phase 4: Update Project Configuration

- [ ] **Update Bundle Identifier in Project**
  ```bash
  # From repository root
  ./scripts/update_bundle_id.sh com.yourcompany.mmt
  ```

- [ ] **Verify Info.plist Permissions**
  - Check `app/ios/Runner/Info.plist` has:
    - NSMicrophoneUsageDescription
    - NSSpeechRecognitionUsageDescription
    - Other required permissions

- [ ] **Update Fastlane Configuration**
  - Edit `app/ios/fastlane/Appfile`
  - Update bundle identifier
  - Add Apple ID

- [ ] **Test Local Build** (if you have a Mac)
  ```bash
  cd app
  flutter build ios --release
  ```

## Phase 5: GitHub Secrets Configuration

Configure these secrets in GitHub (Settings → Secrets and variables → Actions):

### Required Secrets:

- [ ] **APPLE_ID**
  - Your Apple Developer account email

- [ ] **APPLE_TEAM_ID**
  - Found in: developer.apple.com → Membership → Team ID

- [ ] **APP_STORE_CONNECT_TEAM_ID**
  - Found in: App Store Connect → Users and Access → Team ID

- [ ] **IOS_BUNDLE_ID**
  - The bundle identifier you chose (e.g., com.yourcompany.mmt)

- [ ] **APP_STORE_CONNECT_API_KEY_ID**
  - The Key ID from App Store Connect API key

- [ ] **APP_STORE_CONNECT_API_ISSUER_ID**
  - The Issuer ID from App Store Connect API key

- [ ] **APP_STORE_CONNECT_API_KEY_CONTENT**
  - Base64-encoded .p8 file content
  ```bash
  base64 -i AuthKey_XXXXXXXX.p8 | pbcopy
  ```

- [ ] **IOS_DISTRIBUTION_CERTIFICATE_BASE64**
  - Base64-encoded .p12 certificate
  ```bash
  base64 -i distribution_certificate.p12 | pbcopy
  ```

- [ ] **IOS_DISTRIBUTION_CERTIFICATE_PASSWORD**
  - Password for the .p12 certificate

- [ ] **IOS_PROVISIONING_PROFILE_BASE64**
  - Base64-encoded provisioning profile
  ```bash
  base64 -i profile.mobileprovision | pbcopy
  ```

- [ ] **KEYCHAIN_PASSWORD**
  - A random strong password for CI keychain
  ```bash
  openssl rand -base64 32
  ```

## Phase 6: First TestFlight Build

### Manual Build (If Using Mac):

- [ ] **Build Archive in Xcode**
  - Product → Archive
  - Once complete, click "Distribute App"
  - Select "App Store Connect"
  - Upload

### Automated Build (GitHub Actions):

- [ ] **Trigger Workflow**
  - Commit changes and push to main
  - Or use workflow_dispatch in GitHub Actions
  - Select "Deploy to TestFlight: true"

- [ ] **Monitor Build**
  - Check GitHub Actions tab
  - Watch for build completion
  - Check for any errors

## Phase 7: TestFlight Configuration

- [ ] **Wait for Processing**
  - Go to App Store Connect → TestFlight
  - Wait 10-60 minutes for processing

- [ ] **Add Test Information**
  - What to Test: Description of features
  - Test Notes: Any special instructions

- [ ] **Add Internal Testers**
  - TestFlight → Internal Testing
  - Create group or add individuals
  - Up to 100 internal testers

- [ ] **Submit for Beta Review** (for external testing)
  - Required for external testers
  - Usually 24-48 hours review
  - Add external test groups

- [ ] **Invite Testers**
  - Testers receive email invitations
  - They install TestFlight app
  - Accept invitation and test

## Phase 8: Prepare for App Store Submission

- [ ] **Complete App Metadata**
  - App description
  - Keywords
  - Screenshots (required sizes)
  - App icon (1024x1024)
  - Privacy Policy URL
  - Support URL
  - Age rating

- [ ] **Test Thoroughly**
  - [ ] Core transcription features
  - [ ] Microphone permissions
  - [ ] Speech recognition
  - [ ] File saving/loading
  - [ ] UI/UX on different devices
  - [ ] Performance testing

- [ ] **Review App Store Guidelines**
  - https://developer.apple.com/app-store/review/guidelines/
  - Ensure compliance with all guidelines
  - Especially health/medical data handling

## Phase 9: App Store Submission

- [ ] **Select Build for Release**
  - App Store Connect → Your App → "1.0 Prepare for Submission"
  - Click "+" next to Build
  - Select TestFlight build

- [ ] **Answer Export Compliance**
  - Does your app use encryption?
  - Medical data should be encrypted

- [ ] **Submit for Review**
  - Click "Submit for Review"
  - Wait 24-72 hours typically

## Phase 10: Post-Submission

- [ ] **Monitor Review Status**
  - Check email for updates
  - Respond quickly to any questions

- [ ] **Upon Approval**
  - Choose release timing (automatic or manual)
  - Consider phased release

- [ ] **Monitor After Release**
  - Watch crash reports
  - Monitor user reviews
  - Track analytics

## Troubleshooting

### Common Issues:

**"No certificate available"**
- Solution: Create/import distribution certificate

**"Provisioning profile doesn't include signing certificate"**
- Solution: Regenerate provisioning profile with correct certificate

**"Bundle ID mismatch"**
- Solution: Ensure bundle ID matches in Xcode, App Store Connect, and fastlane

**"Invalid binary"**
- Solution: Check for missing architectures, ensure proper signing

**GitHub Actions fails on signing**
- Solution: Verify all secrets are correctly base64-encoded
- Check certificate password is correct

## Resources

- Apple Developer: https://developer.apple.com
- App Store Connect: https://appstoreconnect.apple.com
- Fastlane Docs: https://docs.fastlane.tools
- TestFlight: https://developer.apple.com/testflight/

## Timeline Estimate

- Apple Developer enrollment: 24-48 hours
- First TestFlight build setup: 2-4 hours
- TestFlight processing: 10-60 minutes per build
- Beta review (for external testing): 24-48 hours
- App Store review: 24-72 hours
- **Total**: ~3-7 days for first complete deployment

## Support

Need help? Check:
- APPLE_DEVELOPER_SETUP.md for detailed instructions
- GitHub Actions workflow logs for build issues
- Apple Developer forums
