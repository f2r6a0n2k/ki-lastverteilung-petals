#!/bin/bash
# Start-Skript für llama.cpp Worker
# Verwendung: bash start_worker.sh [PORT]
# Beispiel: bash start_worker.sh 8080

PORT=${1:-8080}

cd ~/llama.cpp
pkill -f llama-server 2>/dev/null
sleep 2

echo "Starte llama-server auf Port ${PORT}..."
nohup ./build/bin/llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 1024 \
  --port "${PORT}" \
  --host 0.0.0.0 \
  -t $(nproc) \
  > "/tmp/llama-${PORT}.log" 2>&1 &

sleep 3
if curl -s --connect-timeout 2 "http://localhost:${PORT}/health" >/dev/null 2>&1; then
  echo "✅ Worker läuft auf Port ${PORT}"
  echo "   Log: /tmp/llama-${PORT}.log"
else
  echo "❌ Start fehlgeschlagen. Log prüfen: tail -20 /tmp/llama-${PORT}.log"
fi
