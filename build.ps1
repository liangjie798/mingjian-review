$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$ModelPath = "models\qwen2.5-0.5b-instruct-q4_k_m.gguf"
$RuntimePath = "runtime\llama\llama-cli.exe"
if (-not (Test-Path $ModelPath)) {
    throw "Missing embedded model: $ModelPath"
}
if (-not (Test-Path $RuntimePath)) {
    throw "Missing llama.cpp runtime: $RuntimePath"
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -m venv .venv
}

& ".venv\Scripts\python.exe" -m pip install --upgrade pip
& ".venv\Scripts\python.exe" -m pip install -r requirements-desktop.txt
& ".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean mingjian.spec

$Hash = (Get-FileHash "dist\MingJian-AI.exe" -Algorithm SHA256).Hash
Set-Content -Encoding UTF8 "dist\MingJian-AI.exe.sha256.txt" "$Hash  MingJian-AI.exe"

Write-Host "Build complete: dist\MingJian-AI.exe"
Write-Host "SHA-256: $Hash"
