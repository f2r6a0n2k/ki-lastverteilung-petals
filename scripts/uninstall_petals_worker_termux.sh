#!/bin/bash
# llama.cpp Worker Deinstallation für Termux
# Verwendung: bash uninstall_petals_worker_termux.sh [PORT]
# Beispiel: bash uninstall_petals_worker_termux.sh 8080

PORT=${1:-8080}
echo "=== llama.cpp Worker Deinstallation (Termux) ==="

# Worker stoppen
pkill -f "llama-server.*$PORT"
sleep 2

# Start-Skripte entfernen
rm -f ~/start_llama-Worker-Termux-*.sh

echo "✅ Worker auf Port $PORT gestoppt"
echo "   Hinweis: llama.cpp-Verzeichnis (~/llama.cpp) und Modelle wurden nicht entfernt."
echo "   Zum vollständigen Entfernen: rm -rf ~/llama.cpp"
