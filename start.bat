@echo off
:: 1. 인코딩 설정
chcp 65001 >nul

:: 2. uv 경로 설정 (일단 uv가 있다고 가정)
set "UV_EXE=uv"

:: 3. 만약 uv가 명령어로 안 먹히면 직접 경로 찾기
where uv >nul 2>&1
if %errorlevel% neq 0 set "UV_EXE=%LOCALAPPDATA%\uv\bin\uv.exe"

:: 4. 실행 전 파일 체크
echo [1/2] Syncing...
%UV_EXE% sync
if %errorlevel% neq 0 (
    echo Sync failed. Check your pyproject.toml
    pause
    exit /b
)

echo [2/2] Running app...
%UV_EXE% run main.py
if %errorlevel% neq 0 (
    echo App crashed. Check the error message above.
    pause
    exit /b
)

echo.
echo Done.
pause