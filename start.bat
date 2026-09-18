@echo off
title Contact QR Code Generator
cd /d "%~dp0"

echo.
echo  ==========================================
echo   Contact QR Code Generator
echo   Browser will open automatically...
echo  ==========================================
echo.

where python >nul 2>nul
if %errorlevel%==0 (
    python app.py
    goto end
)

where py >nul 2>nul
if %errorlevel%==0 (
    py app.py
    goto end
)

echo  [ERROR] Python not found!
echo  Please install Python from https://www.python.org/downloads/
echo  and check "Add python.exe to PATH" during install.
pause
exit /b 1

:end
echo.
echo  Server stopped. You can close this window.
pause
