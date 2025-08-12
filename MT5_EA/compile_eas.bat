@echo off
echo ========================================
echo MT5 Expert Advisors Compilation Script
echo ========================================

echo.
echo This script will help compile the Expert Advisors.
echo.

REM Find MetaEditor
set "METAEDITOR_PATH="
for /f "tokens=*" %%i in ('dir /s /b "%APPDATA%\MetaQuotes\Terminal\*\terminal64.exe" 2^>nul') do (
    set "METAEDITOR_PATH=%%~dpi..\metaeditor64.exe"
    goto :found
)

:found
if not exist "%METAEDITOR_PATH%" (
    echo ❌ Could not find MetaEditor
    echo Please compile manually:
    echo 1. Press F4 in MT5 to open MetaEditor
    echo 2. Open PropFirmBot.mq5 and RegularBot.mq5
    echo 3. Press F7 to compile each
    pause
    exit /b 1
)

echo ✅ Found MetaEditor: %METAEDITOR_PATH%
echo.

REM Set paths
set "EXPERTS_PATH=%APPDATA%\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts"
set "PROPFIRM_SOURCE=%CD%\PropFirmBot.mq5"
set "REGULAR_SOURCE=%CD%\RegularBot.mq5"

echo 📁 Experts Path: %EXPERTS_PATH%
echo 📄 PropFirmBot Source: %PROPFIRM_SOURCE%
echo 📄 RegularBot Source: %REGULAR_SOURCE%
echo.

REM Compile PropFirmBot
echo 🔨 Compiling PropFirmBot.mq5...
"%METAEDITOR_PATH%" /compile:"%PROPFIRM_SOURCE%" /log:"%TEMP%\propfirm_compile.log"
if %ERRORLEVEL% EQU 0 (
    echo ✅ PropFirmBot compiled successfully
) else (
    echo ❌ PropFirmBot compilation failed
    echo Check log: %TEMP%\propfirm_compile.log
)

echo.

REM Compile RegularBot
echo 🔨 Compiling RegularBot.mq5...
"%METAEDITOR_PATH%" /compile:"%REGULAR_SOURCE%" /log:"%TEMP%\regular_compile.log"
if %ERRORLEVEL% EQU 0 (
    echo ✅ RegularBot compiled successfully
) else (
    echo ❌ RegularBot compilation failed
    echo Check log: %TEMP%\regular_compile.log
)

echo.
echo ========================================
echo Compilation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Open MetaTrader 5
echo 2. Press Ctrl+N to open Navigator
echo 3. Click on Expert Advisors tab
echo 4. You should see PropFirmBot and RegularBot
echo.
pause 