#!/bin/bash
# Start-Skript für Elitebook Worker (llama.cpp)
# Ausführen auf Elitebook: bash start_elitebook_worker.sh

cd ~/llama.cpp
pkill -f llama-server 2>/dev/null
sleep 2

echo "Starte llama-server (TinyLlama-1.1B) auf Port 8080..."
nohup ./build/bin/llama-server \
  -m models/tinyllama-q4.gguf \
  -c 1024 \
  --port 8080 \
  --host 0.0.0.0 \
  -t $(nproc) \
  > /tmp/llama-8080.log 2>&1 &

sleep 3
if curl -s --connect-timeout 2 http://localhost:8080/health >/dev/null 2>&1; then
  echo "✅ Worker läuft auf Port 8080"
  echo "   Log: /tmp/llama-8080.log"
else
  echo "❌ Start fehlgeschlagen. Log prüfen: tail -20 /tmp/llama-8080.log"
fi
