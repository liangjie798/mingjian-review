$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$localDotnet = Join-Path $root ".tools\dotnet\dotnet.exe"
$dotnet = if (Test-Path $localDotnet) { $localDotnet } else { "dotnet" }

if (-not (Get-Command $dotnet -ErrorAction SilentlyContinue)) {
    $sdkDir = Join-Path $root ".tools\dotnet"
    $installer = Join-Path $env:TEMP "dotnet-install.ps1"
    Invoke-WebRequest -UseBasicParsing "https://dot.net/v1/dotnet-install.ps1" -OutFile $installer
    & powershell -NoProfile -ExecutionPolicy Bypass -File $installer -Channel 8.0 -InstallDir $sdkDir -NoPath
    $dotnet = Join-Path $sdkDir "dotnet.exe"
}

$project = Join-Path $root "src\MingJian.Desktop\MingJian.Desktop.csproj"
$output = Join-Path $root "dist-wpf"
if (Test-Path $output) { Remove-Item -LiteralPath $output -Recurse -Force }

$env:DOTNET_CLI_TELEMETRY_OPTOUT = "1"
& $dotnet test (Join-Path $root "MingJian.sln") -c Release
if ($LASTEXITCODE -ne 0) { throw "测试未通过" }

& $dotnet publish $project -c Release -r win-x64 --self-contained true -o $output `
    -p:PublishSingleFile=true `
    -p:IncludeNativeLibrariesForSelfExtract=true `
    -p:IncludeAllContentForSelfExtract=true `
    -p:EnableCompressionInSingleFile=true `
    -p:DebugType=None `
    -p:DebugSymbols=false
if ($LASTEXITCODE -ne 0) { throw "发布失败" }

$exe = Join-Path $output "MingJian-AI.exe"
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash
"$hash  MingJian-AI.exe" | Set-Content -LiteralPath "$exe.sha256.txt" -Encoding ascii
Write-Host "WPF 版本已生成：$exe"
Write-Host "SHA-256：$hash"
