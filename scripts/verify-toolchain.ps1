# Ensure Scoop shims are on PATH if tools were installed via Scoop.
$scoopShims = Join-Path $env:USERPROFILE "scoop\shims"
if (Test-Path $scoopShims) { $env:Path = "$scoopShims;$env:Path" }

Write-Host "=== kubectl ===" ; kubectl version --client 2>&1
Write-Host "=== minikube ===" ; minikube version 2>&1
Write-Host "=== helm ===" ; helm version 2>&1
Write-Host "=== k9s ===" ; k9s version 2>&1
