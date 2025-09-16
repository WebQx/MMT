#!/bin/bash

# Test the improved landing page transcription functionality

echo "🧪 Testing Landing Page Transcription Button Fix"
echo "==============================================="

echo ""
echo "✅ Changes Applied:"
echo "  • Fixed service port detection (8001 -> 8000)"
echo "  • Added dedicated transcription service handler"
echo "  • Updated 'Start Transcribing' button to use backend API"
echo "  • Created modal with transcription options"

echo ""
echo "🔍 Testing Backend Connectivity:"
HEALTH_CHECK=$(curl -s http://localhost:8000/health/live)
if [[ $HEALTH_CHECK == *"live"* ]]; then
    echo "✅ Backend is online and responding"
else
    echo "❌ Backend is not responding"
    echo "   Please start with: cd backend && uvicorn main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

echo ""
echo "🔍 Testing Landing Page:"
LANDING_CHECK=$(curl -s http://localhost:8090/ | grep -c "Start Transcribing")
if [[ $LANDING_CHECK -gt 0 ]]; then
    echo "✅ Landing page is serving correctly"
    echo "   Found $LANDING_CHECK 'Start Transcribing' button(s)"
else
    echo "❌ Landing page is not responding"
    echo "   Please start with: cd frontend-landing && python3 -m http.server 8090"
    exit 1
fi

echo ""
echo "🎯 How to Test the Fix:"
echo "  1. Open: http://localhost:8090"
echo "  2. Click the blue 'Start Transcribing' button"
echo "  3. You should see a modal with transcription options instead of the repo clone message"
echo "  4. Try 'Open API Documentation' to access the backend API"

echo ""
echo "📋 Expected Behavior:"
echo "  ✅ Modal opens with 3 options:"
echo "     • Open API Documentation (links to backend API docs)"
echo "     • Visit Backend Home (links to backend root)"
echo "     • Record Audio (shows coming soon message)"
echo "  ✅ No more 'clone the repo' popup"
echo "  ✅ Proper backend integration"

echo ""
echo "🔗 Quick Links:"
echo "  • Landing Page: http://localhost:8090"
echo "  • Backend API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • Health Check: http://localhost:8000/health/live"

echo ""
echo "🎉 Landing page transcription button should now work properly!"