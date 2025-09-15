#!/bin/bash

# Railway Deployment Test Script
# This script helps test Railway deployment locally before GitHub Actions

set -e

echo "🚂 Railway Deployment Test Script"
echo "=================================="

# Check if Railway token is provided
if [ -z "$1" ]; then
    echo "❌ Usage: $0 <RAILWAY_TOKEN>"
    echo "   Example: $0 555b4cc4-e194-49a3-a722-d5b7ba02d6f9"
    exit 1
fi

RAILWAY_TOKEN="$1"
echo "✅ Railway token provided"

# Check if we're in the backend directory
if [ ! -f "main.py" ] && [ ! -f "backend/main.py" ]; then
    echo "❌ Error: Not in MMT project directory or backend files not found"
    exit 1
fi

# Navigate to backend directory if needed
if [ -f "backend/main.py" ]; then
    echo "📁 Changing to backend directory..."
    cd backend
fi

echo "📋 Current directory contents:"
ls -la

# Check for required files
echo "🔍 Checking required files..."
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found"
    exit 1
fi
echo "✅ Dockerfile found"

if [ ! -f "requirements.light.txt" ]; then
    echo "❌ requirements.light.txt not found"
    exit 1
fi
echo "✅ requirements.light.txt found"

if [ ! -f "main.py" ]; then
    echo "❌ main.py not found"
    exit 1
fi
echo "✅ main.py found"

# Test Python syntax
echo "🐍 Testing Python syntax..."
python3 -m py_compile main.py
echo "✅ Python syntax check passed"

# Check Docker build (optional, might take time)
echo "🐳 Testing Docker build (this might take a few minutes)..."
if command -v docker >/dev/null 2>&1; then
    docker build -t mmt-backend-test . --build-arg INCLUDE_ML=0
    echo "✅ Docker build successful"
    
    # Clean up test image
    docker rmi mmt-backend-test || true
else
    echo "⚠️  Docker not available, skipping Docker build test"
fi

echo ""
echo "🎉 All checks passed! Your backend is ready for Railway deployment."
echo ""
echo "📝 Next steps:"
echo "1. Add RAILWAY_TOKEN to GitHub repository secrets:"
echo "   - Go to https://github.com/WebQx/MMT/settings/secrets/actions"
echo "   - Click 'New repository secret'"
echo "   - Name: RAILWAY_TOKEN"
echo "   - Value: $RAILWAY_TOKEN"
echo ""
echo "2. Push changes to trigger automatic deployment:"
echo "   git add ."
echo "   git commit -m 'fix: configure Railway deployment'"
echo "   git push origin main"
echo ""
echo "3. Or manually trigger deployment:"
echo "   - Go to https://github.com/WebQx/MMT/actions"
echo "   - Select 'Deploy Backend to Railway'"
echo "   - Click 'Run workflow'"