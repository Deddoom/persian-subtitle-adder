@echo off
chcp 65001 > nul
cls
echo ========================================================
echo      Persian Subtitle App Installer (Windows)
echo      Nasar va Rahandazi - Nasb-e Ketabkhane-ha
echo ========================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Lotfan Python ra nasb konid va gozine "Add to PATH" ra bezanid.
    pause
    exit /b
)

echo [1/4] Creating Virtual Environment (venv)...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create venv.
    pause
    exit /b
)

echo [2/4] Activating Virtual Environment...
call venv\Scripts\activate

echo [3/4] Upgrading pip and installing requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [4/4] Checking for FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] FFmpeg is NOT found in your PATH!
    echo --------------------------------------------------------
    echo Baraye kar kardane in barname, shoma bayad FFmpeg ra nasb konid.
    echo 1. Be in site beravid: https://ffmpeg.org/download.html
    echo 2. File ha ra download va estekhraj konid.
    echo 3. Pushe 'bin' ra be Environment Variables (Path) ezafe konid.
    echo --------------------------------------------------------
) else (
    echo [OK] FFmpeg is installed correctly.
)

echo.
echo ========================================================
echo      Nasb ba movafaghiat anjam shod!
echo      Baraye ejra, file 'run_app.bat' ra besazid 
echo      ya dastur: 'venv\Scripts\python persian_subtitle_app.py' ra bezanid.
echo ========================================================
pause