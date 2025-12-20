@echo off
:: 1. 한글 깨짐 방지
chcp 65001 >nul
setlocal

echo [DEBUG] 현재 실행 경로: %CD%

:: 2. uv가 설치되어 있는지 확인
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] uv 명령어를 찾을 수 없습니다. 
    echo [!] %LOCALAPPDATA%\uv\bin\uv.exe 경로를 확인합니다...
    if exist "%LOCALAPPDATA%\uv\bin\uv.exe" (
        set "UV_EXE=%LOCALAPPDATA%\uv\bin\uv.exe"
        echo [OK] uv를 찾았습니다: %UV_EXE%
    ) else (
        echo [FAIL] uv가 아예 설치되지 않은 것 같습니다.
        echo 먼저 setup.ps1을 실행하거나 uv를 설치해주세요.
        pause
        exit /b
    )
) else (
    set "UV_EXE=uv"
)

:: 3. pyproject.toml 파일이 있는지 확인 (uv 실행 필수 파일)
if not exist "pyproject.toml" (
    echo [ERROR] 이 폴더에는 pyproject.toml 파일이 없습니다!
    echo [ERROR] 압축이 제대로 풀렸는지, 혹은 폴더 안의 폴더로 들어갔는지 확인하세요.
    pause
    exit /b
)

echo.
echo [1/2] 라이브러리 동기화 시작...
"%UV_EXE%" sync
if %errorlevel% neq 0 (
    echo [ERROR] uv sync 도중 에러가 발생했습니다.
    pause
    exit /b
)

echo.
echo [2/2] 프로그램 실행 중: main.py
"%UV_EXE%" run main.py
if %errorlevel% neq 0 (
    echo [ERROR] 파이썬 프로그램 실행 중 에러가 발생했습니다. 위 메시지를 확인하세요.
    pause
    exit /b
)

echo.
echo [SUCCESS] 프로그램이 정상 종료되었습니다.
pause