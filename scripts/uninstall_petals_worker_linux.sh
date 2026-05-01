#!/bin/bash
# Petals Worker Deinstallation für Linux
# Verwendung: bash uninstall_petals_worker_linux.sh [PORT]
# Beispiel: bash uninstall_petals_worker_linux.sh 8080

PORT=${1:-8080}
echo "=== Petals Worker Deinstallation (Linux) ==="

# Worker stoppen
pkill -f "petals.cli.run_server.*$PORT"
sleep 2

# Firewall-Regel entfernen
sudo ufw delete allow "$PORT/tcp" 2>/dev/null

# Petals und PyTorch deinstallieren (optional)
read -p "Petals/PyTorch deinstallieren? (y/n): " CONFIRM
if [ "$CONFIRM" = "y" ]; then
    pip3 uninstall -y petals torch
    echo "✅ Petals und PyTorch deinstalliert"
fi

echo "✅ Petals Worker auf Port $PORT deinstalliert"
