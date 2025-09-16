#!/bin/bash

# Simple test script for MMT Landing Page functionality

echo "🧪 Testing MMT Landing Page Functionality"
echo "======================================="

echo ""
echo "1. Testing Backend Health Endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health/live)
if [[ $HEALTH_RESPONSE == *"live"* ]]; then
    echo "✅ Backend health endpoint working"
else
    echo "❌ Backend health endpoint failed"
    echo "Response: $HEALTH_RESPONSE"
fi

echo ""
echo "2. Testing Demo Status Endpoint..."
DEMO_RESPONSE=$(curl -s http://localhost:8000/demo/status)
if [[ $DEMO_RESPONSE == *"demo_mode"* ]]; then
    echo "✅ Demo status endpoint working"
    echo "Response: $DEMO_RESPONSE"
else
    echo "❌ Demo status endpoint failed"
    echo "Response: $DEMO_RESPONSE"
fi

echo ""
echo "3. Testing Public Config Endpoint..."
CONFIG_RESPONSE=$(curl -s http://localhost:8000/config/public)
if [[ $CONFIG_RESPONSE == *"{"* ]]; then
    echo "✅ Public config endpoint working"
    echo "Response: $CONFIG_RESPONSE"
else
    echo "❌ Public config endpoint failed"
    echo "Response: $CONFIG_RESPONSE"
fi

echo ""
echo "4. Testing Landing Page HTTP Server..."
LANDING_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8090/)
if [[ $LANDING_RESPONSE == "200" ]]; then
    echo "✅ Landing page HTTP server working (HTTP $LANDING_RESPONSE)"
else
    echo "❌ Landing page HTTP server failed (HTTP $LANDING_RESPONSE)"
fi

echo ""
echo "5. Testing Landing Page Content..."
LANDING_CONTENT=$(curl -s http://localhost:8090/ | grep -o "MMT - Medical Transcription")
if [[ ! -z "$LANDING_CONTENT" ]]; then
    echo "✅ Landing page content loading correctly"
else
    echo "❌ Landing page content not found"
fi

echo ""
echo "🎯 Next Steps:"
echo "   • Open http://localhost:8090 in your browser"
echo "   • Check that service status indicators show 'online' for Django API"
echo "   • Test interactive features like demo buttons"
echo "   • Verify smooth scrolling and navigation"

echo ""
echo "📊 Service URLs:"
echo "   • Landing Page: http://localhost:8090"
echo "   • Backend API:  http://localhost:8000"
echo "   • Health Check: http://localhost:8000/health/live"
echo "   • Demo Status:  http://localhost:8000/demo/status"