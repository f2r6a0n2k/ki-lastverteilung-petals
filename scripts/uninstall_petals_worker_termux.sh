#!/bin/bash
# Petals Worker Deinstallation für Termux
# Verwendung: bash uninstall_petals_worker_termux.sh [PORT]
# Beispiel: bash uninstall_petals_worker_termux.sh 8080

PORT=${1:-8080}
echo "=== Petals Worker Deinstallation (Termux) ==="

# Worker stoppen
pkill -f "petals.cli.run_server.*$PORT"
sleep 2

# Petals und PyTorch deinstallieren (optional)
read -p "Petals/PyTorch deinstallieren? (y/n): " CONFIRM
if [ "$CONFIRM" = "y" ]; then
    pip uninstall -y petals torch
    echo "✅ Petals und PyTorch deinstalliert"
fi

echo "✅ Petals Worker auf Port $PORT deinstalliert"
