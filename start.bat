@echo off
title Contact QR Generator - Web App
cd /d "%~dp0"

rem ============================================================
rem  This app is now a SERVERLESS static web app.
rem  No Python / Flask server is needed anymore.
rem  It is hosted free 24/7 on GitHub Pages (see DEPLOY.md).
rem
rem  >>> Your app is published on GitHub Pages at this URL:
rem  >>> https://mega808-del.github.io/QR-cord/
rem ============================================================

set "APPURL=https://mega808-del.github.io/QR-cord/"

echo.
echo  ==========================================
echo   Contact QR Code Generator (Web App)
echo   Opening: %APPURL%
echo  ==========================================
echo.

start "" "%APPURL%"

echo  A browser window should open now.
echo  You can close this window and turn off this PC -
echo  the app keeps running on GitHub Pages.
echo.
echo  (To use your own URL, edit APPURL inside start.bat)
echo.
pause
