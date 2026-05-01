#!/bin/bash
# KI Worker Deinstallation für Linux
# Verwendung: bash uninstall_worker_linux.sh [PORT]
# Beispiel: bash uninstall_worker_linux.sh 8080

PORT=${1:-8080}
echo "=== KI Worker Deinstallation (Linux) ==="

# Worker stoppen
pkill -f "petals.cli.run_server.*$PORT"
sleep 2

# Firewall-Regel entfernen
sudo ufw delete allow "$PORT/tcp" 2>/dev/null

# Petals und PyTorch deinstallieren (optional)
read -p "Petals/PyTorch deinstallieren? (y/n): " CONFIRM
if [ "$CONFIRM" = "y" ]; then
    # Installationsfunktion mit pipx-Fallback
    uninstall_pkg() {
        if pip3 uninstall -y "$1" 2>&1 | grep -q "externally-managed-environment"; then
            echo "pip blockiert, versuche pipx..."
            pipx uninstall "$1" || echo "Fehler: $1 konnte nicht deinstalliert werden"
        else
            echo "$1 erfolgreich deinstalliert"
        fi
    }
    uninstall_pkg petals
    uninstall_pkg torch
    echo "✅ Petals und PyTorch deinstalliert"
fi

# Start-Skript entfernen
rm -f ~/start_ki_worker.sh

echo "✅ KI Worker auf Port $PORT deinstalliert"
