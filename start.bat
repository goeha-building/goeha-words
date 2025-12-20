@echo off
chcp 65001 >nul
setlocal
:: 1. uv 설치 여부 확인
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] uv를 찾을 수 없습니다. 설치를 시작합니다...
    :: 파워쉘을 이용해 uv 공식 설치 스크립트 실행
    powershell -ExecutionPolicy ByRemoteSigning -Command "irm https://astral.sh/uv/install.ps1 | iex"
    
    :: 설치 직후에는 시스템 PATH가 바로 반영 안 되므로, 직접 경로를 지정해서 사용함
    set "UV_EXE=%LOCALAPPDATA%\uv\bin\uv.exe"
) else (
    set "UV_EXE=uv"
)

echo.
echo [1/2] 라이브러리 동기화 및 업데이트 확인 중...
:: %UV_EXE%를 사용해서 설치 직후에도 바로 실행 가능하게 함
"%UV_EXE%" sync

echo.
echo [2/2] 프로그램 실행 중: main.py
"%UV_EXE%" run main.py

echo.
echo 실행이 완료되었습니다.
pause