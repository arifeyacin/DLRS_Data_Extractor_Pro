@echo off
TITLE DLRS Data Extractor Pro - One-Click Executable Builder
echo =======================================================================
echo            DLRS Data Extractor Pro - PyInstaller Builder
echo =======================================================================
echo.

REM Activate virtual environment if available
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo [INFO] Cleaning up previous build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [INFO] Building standalone executable DLRS_Data_Extractor.exe...
pyinstaller --clean DLRS_Data_Extractor.spec

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo =======================================================================
echo [SUCCESS] Executable built successfully!
echo Binary path: dist\DLRS_Data_Extractor.exe
echo =======================================================================
echo.
pause
