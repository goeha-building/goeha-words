@echo off
setlocal

:: 1. Check if uv is installed
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] uv not found. Starting installation...
    powershell -ExecutionPolicy ByRemoteSigning -Command "irm https://astral.sh/uv/install.ps1 | iex"
    
    :: Set path for immediate use after installation
    set "UV_EXE=%LOCALAPPDATA%\uv\bin\uv.exe"
) else (
    set "UV_EXE=uv"
)

echo.
echo [1/2] Syncing libraries and checking updates...
"%UV_EXE%" sync

echo.
echo [2/2] Running program: main.py
"%UV_EXE%" run main.py

echo.
echo Execution completed.
pause