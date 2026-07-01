# Gera dist/PPK_Drone/ com PPK_Drone.exe e dependências
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Instalando dependencias de build..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "Limpando build anterior..." -ForegroundColor Cyan
if (Test-Path (Join-Path $PSScriptRoot "dist\PPK_Drone")) {
    Remove-Item -Recurse -Force (Join-Path $PSScriptRoot "dist\PPK_Drone") -ErrorAction SilentlyContinue
}

Write-Host "Gerando executavel com PyInstaller..." -ForegroundColor Cyan
pyinstaller --noconfirm ppk_drone.spec

$dist = Join-Path $PSScriptRoot "dist\PPK_Drone"
foreach ($file in @("rnx2rtkp.exe", "crx2rnx.exe", "config.conf")) {
    Copy-Item -Path (Join-Path $PSScriptRoot $file) -Destination $dist -Force
}

Write-Host ""
Write-Host "Pronto: $dist\PPK_Drone.exe" -ForegroundColor Green
Write-Host "Copie a pasta dist\PPK_Drone inteira para distribuir." -ForegroundColor Yellow
