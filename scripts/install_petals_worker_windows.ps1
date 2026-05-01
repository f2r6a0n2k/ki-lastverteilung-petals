# Petals Worker Installation für Windows (PowerShell - als Administrator)
# Verwendung: .\install_petals_worker_windows.ps1 [PORT] [MODELL]
# Beispiel: .\install_petals_worker_windows.ps1 8080 bartowski/Llama-3.2-3B-Instruct-GGUF

param(
    [int]$Port = 8080,
    [string]$Model = "bartowski/Llama-3.2-3B-Instruct-GGUF"
)

$WORKER_NAME = "Petals-Worker-Windows-$Port"

Write-Host "=== Petals Worker Installation (Windows) ==="

# Python prüfen
try {
    $pythonVersion = python --version
    Write-Host "Python gefunden: $pythonVersion"
} catch {
    Write-Host "❌ Python nicht gefunden. Bitte Python installieren: https://www.python.org/downloads/"
    exit 1
}

# Petals und PyTorch installieren (CPU-Version)
Write-Host "Installiere Petals und PyTorch..."
pip install --upgrade pip
pip install petals torch --index-url https://download.pytorch.org/whl/cpu

# Firewall-Regel
New-NetFirewallRule -DisplayName "Petals $Port" -Direction Inbound -LocalPort $Port -Protocol TCP -Action Allow -ErrorAction SilentlyContinue

# Start-Skript erstellen
$StartScript = "$env:USERPROFILE\start_petals_worker.ps1"
@"
# Petals Worker Start-Skript
`$Port = $Port
`$Model = "$Model"
`$WORKER_NAME = "$WORKER_NAME"
Write-Host "Starte Petals Worker: `$WORKER_NAME auf Port `$Port mit Modell: `$Model"
python -m petals.cli.run_server `$Model --port `$Port --public_name "`$WORKER_NAME"
"@ | Out-File -FilePath $StartScript -Encoding UTF8

# Worker starten
Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy Bypass -File $StartScript" -WindowStyle Hidden

Write-Host "✅ Petals Worker läuft auf Port $Port"
Write-Host "   Modell: $Model"
Write-Host "   Name: $WORKER_NAME"
