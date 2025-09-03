@echo off
echo Adding Flutter to PATH...
set PATH=%PATH%;C:\flutter\bin
echo Verifying Flutter installation...
flutter --version
echo.
echo Flutter is now available in this session.
echo To make permanent, add C:\flutter\bin to System PATH.
pause