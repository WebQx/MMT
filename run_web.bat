@echo off
echo Starting MMT Flutter Web App...
flutter run -d web-server --web-hostname 0.0.0.0 --web-port 3000
echo.
echo App running at:
echo - Local: http://localhost:3000
echo - Network: http://YOUR_IP:3000
pause