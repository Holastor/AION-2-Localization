@echo off
setlocal

:: The name of your Python script
set "PYTHON_SCRIPT=localization_tool.py"

:: ============================================================
:: 1. CHECK FOR PYTHON INSTALLATION
:: ============================================================
echo [Checking] Verifying Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python is not found on this system!
    echo.
    echo Please install Python from the official website:
    echo https://www.python.org/downloads/
    echo.
    echo During installation, be sure to check the box "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

:: Get Python version for display
for /f "delims=" %%i in ('python --version') do set PYTHON_VER=%%i
echo [OK] Found %PYTHON_VER%

:: ============================================================
:: 2. CHECK AND INSTALL REQUIRED MODULES
:: ============================================================
echo.
echo [Checking] Verifying required libraries...

:: List of external modules to check (standard ones like sys/os don't need checking)
set "MODULE_TO_CHECK=polib"

python -c "import %MODULE_TO_CHECK%" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Module '%MODULE_TO_CHECK%' is not installed.
    echo.
    set /p "INSTALL_CHOICE=Do you want to install '%MODULE_TO_CHECK%' now? (Y/N): "

    if /i "%INSTALL_CHOICE%"=="Y" (
        echo.
        echo [Installing] Installing %MODULE_TO_CHECK%...
        pip install %MODULE_TO_CHECK%

        if %errorlevel% neq 0 (
            echo.
            echo [ERROR] Failed to install the module. Check your internet or permissions.
            pause
            exit /b 1
        )
        echo [OK] Module installed successfully.
    ) else (
        echo.
        echo [STOP] The script cannot run without the '%MODULE_TO_CHECK%' module. Aborting.
        pause
        exit /b 1
    )
) else (
    echo [OK] Module '%MODULE_TO_CHECK%' is already installed.
)

:: ============================================================
:: 3. RUN THE PYTHON SCRIPT
:: ============================================================
echo.
echo [Running] Executing %PYTHON_SCRIPT%...
echo ========================================================
echo.

if exist "%PYTHON_SCRIPT%" (
    python "%PYTHON_SCRIPT%"
) else (
    echo [ERROR] The script "%PYTHON_SCRIPT%" was not found in this folder!
    pause
    exit /b 1
)

echo.
echo ========================================================
echo [Done] Script finished.
pause
