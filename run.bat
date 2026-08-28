@echo off
setlocal
REM Run Music Downloader (Streamlit) with the bundled venv
REM Usage: double-click run.bat or call from terminal

set "PORT=8501"
set "SCRIPT_DIR=%~dp0"
set "VENV_PY=%SCRIPT_DIR%.venv\Scripts\python.exe"

echo ======================================
echo   Music Downloader - Streamlit
echo   Port: %PORT%
echo   Python: %VENV_PY%
echo ======================================
echo.

if not exist "%VENV_PY%" (
    echo [!] Python venv tidak ditemukan di "%VENV_PY%"
    echo     Buat venv dulu dan install dependensi:
    echo     python -m venv .venv ^&^& .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

REM optional: ensure deps are installed (quiet, fast if already present)
echo [i] Memeriksa dependensi...
"%VENV_PY%" -m pip install -r "%SCRIPT_DIR%requirements.txt" --quiet
if errorlevel 1 (
    echo [!] Gagal install dependensi. Periksa koneksi internet / requirements.txt
    pause
    exit /b 1
)

REM Kill any existing process on the same port (common after VS Code Streamlit runs)
echo [i] Memeriksa port %PORT% ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
    echo     Menutup proses lama di port %PORT% (PID %%a) ...
    taskkill /PID %%a /F >nul 2>&1
)
REM small wait for port to free
ping 127.0.0.1 -n 2 >nul 2>&1

echo [i] Menjalankan aplikasi di http://localhost:%PORT%
echo     Tutup jendela ini untuk menghentikan server.
echo.
"%VENV_PY%" -m streamlit run "%SCRIPT_DIR%app.py" --server.port %PORT% --server.headless true
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
    echo.
    echo [!] Streamlit berhenti dengan exit code %EXITCODE%
    pause
)

endlocal
