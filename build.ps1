$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -m venv .venv
}

& ".venv\Scripts\python.exe" -m pip install --upgrade pip
& ".venv\Scripts\python.exe" -m pip install -r requirements-desktop.txt
& ".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean mingjian.spec

$Hash = (Get-FileHash "dist\MingJian.exe" -Algorithm SHA256).Hash
Set-Content -Encoding UTF8 "dist\MingJian.exe.sha256.txt" "$Hash  MingJian.exe"
Copy-Item "dist\MingJian.exe" "website\downloads\MingJian.exe" -Force
Copy-Item "dist\MingJian.exe.sha256.txt" "website\downloads\MingJian.exe.sha256.txt" -Force

Write-Host "Build complete: dist\MingJian.exe"
Write-Host "SHA-256: $Hash"
