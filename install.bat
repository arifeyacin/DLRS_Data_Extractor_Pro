@echo off
TITLE DLRS Data Extractor Pro - Installer
echo =======================================================================
echo              DLRS Data Extractor Pro - Environment Setup
echo =======================================================================
echo.

REM Step 1: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.12+ is not installed or not in system PATH!
    echo Please install Python 3.12 or later from https://www.python.org/
    pause
    exit /b 1
)

REM Step 2: Create virtual environment
if not exist "venv" (
    echo [INFO] Creating Python virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Virtual environment 'venv' already exists.
)

REM Step 3: Activate virtual environment & Upgrade pip
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Step 4: Install dependencies
echo [INFO] Installing required dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation failed!
    pause
    exit /b 1
)

REM Step 5: Install Playwright browsers
echo [INFO] Installing Playwright Chromium browser...
playwright install chromium
if %errorlevel% neq 0 (
    echo [WARNING] Playwright browser installation encountered an issue. Scraping fallback will use requests.
)

REM Step 6: Create Output directory structure
echo [INFO] Creating output directory structure...
if not exist "Output\PDFs" mkdir "Output\PDFs"
if not exist "Output\JSON" mkdir "Output\JSON"
if not exist "Output\CSV" mkdir "Output\CSV"
if not exist "Output\Excel" mkdir "Output\Excel"
if not exist "Output\SQLite" mkdir "Output\SQLite"
if not exist "Output\Logs" mkdir "Output\Logs"
if not exist "Output\OCR" mkdir "Output\OCR"

REM Step 7: Check Tesseract OCR
echo [INFO] Checking Tesseract OCR installation...
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo [OK] Tesseract OCR found at C:\Program Files\Tesseract-OCR\tesseract.exe
) else (
    echo [WARNING] Tesseract OCR is not detected at default location (C:\Program Files\Tesseract-OCR\tesseract.exe).
    echo For Bengali OCR support, please install Tesseract-OCR and Bengali language pack (ben.traineddata).
)

echo.
echo =======================================================================
echo [SUCCESS] DLRS Data Extractor Pro setup completed successfully!
echo Run main.py or execute build.bat to generate standalone EXE.
echo =======================================================================
echo.
pause
