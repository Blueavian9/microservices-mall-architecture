# Installs kubectl, minikube, helm, k9s without Administrator (Scoop user install).
# Prerequisites: Scoop (https://scoop.sh). For Minikube with --driver=docker: Docker Desktop on PATH.
Set-ExecutionPolicy Bypass -Scope Process -Force
$ErrorActionPreference = "Stop"

if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Scoop to user profile..." -ForegroundColor Yellow
    Invoke-Expression (New-Object System.Net.WebClient).DownloadString("https://get.scoop.sh")
}
$env:Path = "$env:USERPROFILE\scoop\shims;$env:Path"

scoop install kubectl minikube helm k9s

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker not found on PATH. Install Docker Desktop, then re-run Minikube start:" -ForegroundColor Yellow
    Write-Host "  https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor Cyan
    exit 0
}

minikube start --driver=docker --cpus=4 --memory=8192 --disk-size=20g
minikube addons enable ingress
minikube addons enable metrics-server
Write-Host "Toolchain ready." -ForegroundColor Green
