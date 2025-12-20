# setup.ps1
$url = "https://github.com/goeha-building/goeha-words/archive/refs/heads/main.zip"
$zip = "goeha.zip"
$dir = "goeha-words-main"

Write-Host "[1/4] 소스 코드 다운로드 중..." -ForegroundColor Cyan
iwr -Uri $url -OutFile $zip

Write-Host "[2/4] 압축 해제 중..." -ForegroundColor Cyan
Expand-Archive -Path $zip -DestinationPath "." -Force
Remove-Item $zip

cd $dir

Write-Host "[3/4] uv 설치 확인 중..." -ForegroundColor Cyan
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    powershell -ExecutionPolicy ByRemoteSigning -Command "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path += ";$env:LOCALAPPDATA\uv\bin"
}

Write-Host "[4/4] 의존성 설치 및 앱 실행..." -ForegroundColor Green
uv sync
uv run main.py