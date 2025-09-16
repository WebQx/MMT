#!/bin/bash

# Test the GitHub Pages deployment functionality

echo "🌐 Testing GitHub Pages Deployment"
echo "=================================="

echo ""
echo "🚀 Recent Changes:"
echo "  ✅ Fixed landing page transcription button"
echo "  ✅ Updated GitHub Pages workflow configuration"
echo "  ✅ Fixed backend URL replacement for production"
echo "  ✅ Triggered automatic deployment"

echo ""
echo "📋 What was deployed:"
echo "  • Landing page from frontend-landing/ folder"
echo "  • Updated 'Start Transcribing' button functionality"
echo "  • Professional modal interface"
echo "  • Backend connectivity to Railway production API"

echo ""
echo "🔗 Testing URLs:"
GITHUB_PAGES_URL="https://webqx.github.io/MMT/"
RAILWAY_BACKEND="https://mmt-backend-production.up.railway.app"

echo "  • GitHub Pages: $GITHUB_PAGES_URL"
echo "  • Railway Backend: $RAILWAY_BACKEND"

echo ""
echo "🧪 Testing Railway Backend connectivity:"
if curl -s --max-time 10 "$RAILWAY_BACKEND/health/live" | grep -q "live"; then
    echo "  ✅ Railway backend is responding"
else
    echo "  ❌ Railway backend is not responding"
    echo "     This may affect GitHub Pages functionality"
fi

echo ""
echo "🔍 Testing GitHub Pages availability:"
if curl -s --max-time 10 "$GITHUB_PAGES_URL" | grep -q "MMT"; then
    echo "  ✅ GitHub Pages is serving content"
else
    echo "  ⏳ GitHub Pages may still be deploying"
    echo "     Deployment usually takes 2-5 minutes after push"
fi

echo ""
echo "📊 Expected GitHub Pages behavior:"
echo "  1. Landing page loads with updated design"
echo "  2. 'Start Transcribing' button opens modal (not popup)"
echo "  3. Backend connectivity to Railway production API"
echo "  4. Service status shows Railway backend connection"
echo "  5. API documentation links work"

echo ""
echo "⏰ If changes don't appear immediately:"
echo "  • GitHub Pages deployment takes 2-5 minutes"
echo "  • Check GitHub Actions tab for deployment status"
echo "  • Clear browser cache and try again"
echo "  • Deployment URL: $GITHUB_PAGES_URL"

echo ""
echo "🎯 Manual test steps:"
echo "  1. Visit: $GITHUB_PAGES_URL"
echo "  2. Click blue 'Start Transcribing' button"
echo "  3. Verify modal opens (not clone repo popup)"
echo "  4. Test 'Open API Documentation' link"
echo "  5. Check service status indicator on right side"

echo ""
echo "🎉 GitHub Pages should be updated within 2-5 minutes!"