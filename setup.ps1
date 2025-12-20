# 1. 경로 설정 (내 문서\goeha-app 폴더 생성)
$targetRoot = Join-Path $HOME "Documents"
$projectDir = Join-Path $targetRoot "goeha-words-app"

# 폴더가 없으면 새로 만듦
if (!(Test-Path $projectDir)) {
    New-Item -ItemType Directory -Path $projectDir -Force
}

# 작업 위치를 내 문서의 프로젝트 폴더로 이동
cd $projectDir

# 2. 다운로드 및 압축 해제
$url = "https://github.com/goeha-building/goeha-words/archive/refs/heads/master.zip"
$zip = "source.zip"

Write-Host "[1/4] 내 문서에 소스 다운로드 중..." -ForegroundColor Cyan
iwr -Uri $url -OutFile $zip

Write-Host "[2/4] 압축 해제 중..." -ForegroundColor Cyan
# DestinationPath를 "."으로 하면 현재 폴더(내 문서\goeha-app)에 풀림
Expand-Archive -Path $zip -DestinationPath "." -Force
Remove-Item $zip

# 압축 풀리면 보통 폴더가 한 겹 더 생기니까 그 안으로 진입
$unzippedFolder = Get-ChildItem -Directory | Where-Object { $_.Name -like "goeha-words-*" } | Select-Object -First 1
if ($unzippedFolder) { cd $unzippedFolder.Name }

# 3. uv 설치 확인 (없으면 설치)
Write-Host "[3/4] uv 설치 확인 중..." -ForegroundColor Cyan
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    powershell -ExecutionPolicy ByRemoteSigning -Command "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path += ";$env:LOCALAPPDATA\uv\bin"
}

# 4. 앱 실행
Write-Host "[4/4] 라이브러리 설치 및 앱 실행..." -ForegroundColor Green
uv sync
uv run main.py