@echo off
echo ========================================
echo MT5 Expert Advisors Installation Script
echo ========================================
echo.

echo This script will help you install the Expert Advisors to MetaTrader 5.
echo.

REM Find MT5 installation path
set "MT5_PATH="
for /f "tokens=*" %%i in ('reg query "HKCU\Software\MetaQuotes\Terminal" /s /f "Common" 2^>nul') do (
    set "MT5_PATH=%%i"
    goto :found
)

:found
if "%MT5_PATH%"=="" (
    echo ❌ Could not find MetaTrader 5 installation.
    echo Please install MetaTrader 5 first.
    pause
    exit /b 1
)

echo ✅ Found MetaTrader 5 installation.
echo.

REM Extract the path
for /f "tokens=3" %%i in ("%MT5_PATH%") do set "MT5_PATH=%%i"

REM Navigate to Experts folder
set "EXPERTS_PATH=%MT5_PATH%\MQL5\Experts"

if not exist "%EXPERTS_PATH%" (
    echo ❌ Experts folder not found at: %EXPERTS_PATH%
    echo Please ensure MetaTrader 5 is properly installed.
    pause
    exit /b 1
)

echo 📁 Target folder: %EXPERTS_PATH%
echo.

REM Copy files
echo 📋 Copying Expert Advisors...
copy "PropFirmBot.mq5" "%EXPERTS_PATH%\" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ PropFirmBot.mq5 copied successfully
) else (
    echo ❌ Failed to copy PropFirmBot.mq5
)

copy "RegularBot.mq5" "%EXPERTS_PATH%\" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ RegularBot.mq5 copied successfully
) else (
    echo ❌ Failed to copy RegularBot.mq5
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Open MetaTrader 5
echo 2. Press Ctrl+N to open Navigator
echo 3. Go to Expert Advisors tab
echo 4. Right-click on the EA and select "Modify"
echo 5. Press F7 to compile
echo 6. Enable automated trading in Tools > Options > Expert Advisors
echo.
echo For detailed instructions, see README.md
echo.
pause 