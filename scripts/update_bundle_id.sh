#!/bin/bash

# iOS Bundle Identifier Update Script
# Usage: ./update_bundle_id.sh com.yourcompany.mmt

set -e

if [ -z "$1" ]; then
    echo "❌ Error: No bundle identifier provided"
    echo ""
    echo "Usage: ./update_bundle_id.sh <new-bundle-id>"
    echo "Example: ./update_bundle_id.sh com.yourcompany.mmt"
    echo ""
    echo "Current bundle ID: com.example.mmt"
    exit 1
fi

NEW_BUNDLE_ID="$1"
OLD_BUNDLE_ID="com.example.mmt"

echo "🔄 Updating iOS Bundle Identifier..."
echo "   Old: $OLD_BUNDLE_ID"
echo "   New: $NEW_BUNDLE_ID"
echo ""

# Validate bundle ID format
if ! [[ "$NEW_BUNDLE_ID" =~ ^[a-z0-9]+(\.[a-z0-9]+)+$ ]]; then
    echo "❌ Error: Invalid bundle identifier format"
    echo "   Bundle IDs must:"
    echo "   - Use reverse domain notation (e.g., com.company.app)"
    echo "   - Contain only lowercase letters, numbers, and dots"
    echo "   - Have at least two segments"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "app/ios/Runner.xcodeproj/project.pbxproj" ]; then
    echo "❌ Error: Must run from repository root (where app/ directory exists)"
    exit 1
fi

cd app/ios

# Update project.pbxproj
echo "📝 Updating Runner.xcodeproj/project.pbxproj..."
sed -i.bak "s/$OLD_BUNDLE_ID/$NEW_BUNDLE_ID/g" Runner.xcodeproj/project.pbxproj
rm Runner.xcodeproj/project.pbxproj.bak 2>/dev/null || true

# Update Runner tests bundle ID
OLD_TEST_ID="${OLD_BUNDLE_ID}.RunnerTests"
NEW_TEST_ID="${NEW_BUNDLE_ID}.RunnerTests"
sed -i.bak "s/$OLD_TEST_ID/$NEW_TEST_ID/g" Runner.xcodeproj/project.pbxproj
rm Runner.xcodeproj/project.pbxproj.bak 2>/dev/null || true

echo "✅ Bundle identifier updated successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Open Xcode: open ios/Runner.xcworkspace"
echo "   2. Verify bundle ID in Runner target → General tab"
echo "   3. Select your Apple Developer Team in Signing & Capabilities"
echo "   4. Register bundle ID in Apple Developer Portal:"
echo "      https://developer.apple.com/account/resources/identifiers/list"
echo "   5. Create matching app in App Store Connect:"
echo "      https://appstoreconnect.apple.com"
echo ""
echo "🔐 New Bundle ID: $NEW_BUNDLE_ID"
