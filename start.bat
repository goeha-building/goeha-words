@echo off
:: 터미널 인코딩을 UTF-8로 변경 (한글 깨짐 방지)
chcp 65001 >nul
setlocal

:: 1. uv 설치 여부 확인
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] uv를 찾을 수 없습니다. 설치를 시작합니다...
    powershell -ExecutionPolicy ByRemoteSigning -Command "irm https://astral.sh/uv/install.ps1 | iex"
    set "UV_EXE=%LOCALAPPDATA%\uv\bin\uv.exe"
) else (
    set "UV_EXE=uv"
)

echo.
echo [1/2] 라이브러리 동기화 및 업데이트 확인 중...
"%UV_EXE%" sync

echo.
echo [2/2] 프로그램 실행 중: main.py
"%UV_EXE%" run main.py

echo.
echo 실행이 완료되었습니다.
pause