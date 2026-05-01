#!/bin/bash
# llama.cpp Worker Installation für Android (Termux)
# Verwendung: bash install_worker_termux.sh [PORT]
# Beispiel: bash install_worker_termux.sh 8080

PORT=${1:-8080}
MODEL_NAME="Llama-3.2-3B-Instruct-Q4_K_M.gguf"
WORKER_NAME="llama-Worker-Termux-$PORT"

echo "=== llama.cpp Worker Installation (Termux) ==="

# Abhängigkeiten installieren
echo "Installiere Abhängigkeiten..."
pkg update && pkg install -y git make clang wget

# llama.cpp herunterladen und kompilieren
echo "Kompiliere llama.cpp..."
cd ~
if [ -d "llama.cpp" ]; then
    echo "llama.cpp bereits vorhanden, aktualisiere..."
    cd llama.cpp && git pull
else
    git clone https://github.com/ggerganov/llama.cpp.git
    cd llama.cpp
fi

make -j$(nproc)

# Modell-Verzeichnis erstellen
mkdir -p models

# Modell herunterladen (falls noch nicht vorhanden)
if [ ! -f "models/${MODEL_NAME}" ]; then
    echo "Modell herunterladen (${MODEL_NAME}, ~2GB)..."
    pip install huggingface-hub
    hf download bartowski/Llama-3.2-3B-Instruct-GGUF \
        --include "${MODEL_NAME}" \
        --local-dir models/
    echo "Modell gespeichert: models/${MODEL_NAME}"
else
    echo "Modell bereits vorhanden: models/${MODEL_NAME}"
fi

# Start-Skript erstellen
cat > "$HOME/start_${WORKER_NAME}.sh" << INNER_EOF
#!/bin/bash
cd ~/llama.cpp
echo "Starte llama-server (llama.cpp) auf Port ${PORT}..."
./build/bin/llama-server \
  -m models/${MODEL_NAME} \
  -c 1024 \
  --port ${PORT} \
  --host 0.0.0.0 \
  -t \$(nproc) \
  > ~/llama-worker-${PORT}.log 2>&1 &
echo "Worker gestartet. Log: ~/llama-worker-${PORT}.log"
INNER_EOF
chmod +x "$HOME/start_${WORKER_NAME}.sh"

# Worker starten
bash "$HOME/start_${WORKER_NAME}.sh"

sleep 3
if curl -s --connect-timeout 3 "http://localhost:${PORT}/health" >/dev/null 2>&1; then
    echo "✅ Worker läuft auf Port ${PORT}"
    echo "   Modell: ${MODEL_NAME}"
    echo "   Name: ${WORKER_NAME}"
    echo "   Log: ~/llama-worker-${PORT}.log"
else
    echo "❌ Start fehlgeschlagen. Log prüfen: tail -20 ~/llama-worker-${PORT}.log"
fi
