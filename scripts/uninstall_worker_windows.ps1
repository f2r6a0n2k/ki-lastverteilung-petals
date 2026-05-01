# KI Worker Deinstallation für Windows (PowerShell - als Administrator)
# Verwendung: .\uninstall_worker_windows.ps1 [PORT]
# Beispiel: .\uninstall_worker_windows.ps1 8080

param([int]$Port = 8080)

Write-Host "=== KI Worker Deinstallation (Windows) ==="

# Worker stoppen
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*petals*"} | Stop-Process -Force

# Firewall-Regel entfernen
Remove-NetFirewallRule -DisplayName "KI-Worker $Port" -ErrorAction SilentlyContinue

# Petals und PyTorch deinstallieren (optional)
$CONFIRM = Read-Host "Petals/PyTorch deinstallieren? (y/n)"
if ($CONFIRM -eq "y") {
    pip uninstall -y petals torch
    Write-Host "✅ Petals und PyTorch deinstalliert"
}

Write-Host "✅ KI Worker auf Port $Port deinstalliert"
