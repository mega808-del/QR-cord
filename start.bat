@echo off
title Contact QR Generator
cd /d "%~dp0"

rem ============================================================
rem  Opens the app directly from the docs folder.
rem  No server needed - it runs entirely in your browser.
rem
rem  Online 24/7 version (after enabling GitHub Pages):
rem  https://mega808-del.github.io/QR-cord/
rem ============================================================

echo.
echo  ==========================================
echo   Contact QR Code Generator
echo   Opening in your browser...
echo  ==========================================
echo.

start "" "%~dp0docs\index.html"

echo  The app opened in your browser (works offline).
echo  You can close this window.
echo.
pause
