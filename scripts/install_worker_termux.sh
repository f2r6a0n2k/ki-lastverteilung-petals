#!/bin/bash
# llama.cpp Worker Installation für Android (Termux)
# Verwendung: bash install_worker_termux.sh [PORT]
# Beispiel: bash install_worker_termux.sh 8080
#
# HINWEIS: Android/Termux unterstützt KEIN Petals (nur llama.cpp).
# Dieser Installer baut llama.cpp mit CMake und lädt Modelle per wget.

PORT=${1:-8080}
MODEL_NAME="Llama-3.2-3B-Instruct-Q4_K_M.gguf"
MODEL_URL="https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/${MODEL_NAME}"

echo "=== llama.cpp Worker Installation (Termux) ==="

# Abhängigkeiten installieren
echo "Installiere Abhängigkeiten..."
pkg update && pkg install -y git cmake clang wget

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

# CMake Build (Makefile wurde durch CMake ersetzt)
mkdir -p build && cd build
cmake .. -DLLAMA_BUILD_SERVER=ON -DCMAKE_BUILD_TYPE=Release
cmake --build . -j$(nproc) --target llama-server

# Modell-Verzeichnis erstellen
mkdir -p ~/llama.cpp/models

# Modell herunterladen (wget, NICHT huggingface-hub – hf-xet baut nicht auf Termux)
if [ ! -f "models/${MODEL_NAME}" ]; then
    echo "Modell herunterladen (${MODEL_NAME}, ~2GB)..."
    wget --continue "${MODEL_URL}" -O "models/${MODEL_NAME}"
    echo "Modell gespeichert: models/${MODEL_NAME}"
else
    echo "Modell bereits vorhanden: models/${MODEL_NAME}"
fi

# Start-Skript erstellen
cat > "$HOME/start_worker.sh" << 'EOF'
#!/bin/bash
PORT=${1:-8080}
MODEL_NAME="Llama-3.2-3B-Instruct-Q4_K_M.gguf"

# Prüfen ob schon läuft
if pgrep -f "llama-server.*${PORT}" > /dev/null 2>&1; then
    echo "⚠ Worker auf Port ${PORT} läuft bereits. Erst stoppen: pkill -f llama-server.*${PORT}"
    exit 1
fi

cd ~/llama.cpp
if [ ! -f "./build/bin/llama-server" ]; then
    echo "❌ llama-server nicht gefunden. Erst installieren: bash install_worker_termux.sh"
    exit 1
fi

echo "Starte llama-server auf Port ${PORT}..."
./build/bin/llama-server \
  -m "models/${MODEL_NAME}" \
  -c 1024 \
  --port "${PORT}" \
  --host 0.0.0.0 \
  -t $(nproc) \
  > ~/llama-worker-${PORT}.log 2>&1 &

sleep 3
if curl -s --connect-timeout 3 "http://localhost:${PORT}/health" >/dev/null 2>&1; then
    echo "✅ Worker läuft auf Port ${PORT}"
    echo "   Log: ~/llama-worker-${PORT}.log"
else
    echo "❌ Start fehlgeschlagen. Log prüfen: tail -20 ~/llama-worker-${PORT}.log"
fi
EOF
chmod +x "$HOME/start_worker.sh"

# Stopp-Skript erstellen
cat > "$HOME/stop_worker.sh" << 'EOF'
#!/bin/bash
PORT=${1:-8080}
echo "Stoppe Worker auf Port ${PORT}..."
pkill -f "llama-server.*${PORT}"
if [ $? -eq 0 ]; then
    echo "✅ Worker gestoppt"
else
    echo "ℹ Kein Worker auf Port ${PORT} gefunden"
fi
EOF
chmod +x "$HOME/stop_worker.sh"

# Status-Skript erstellen
cat > "$HOME/worker_status.sh" << 'EOF'
#!/bin/bash
PORT=${1:-8080}
if curl -s --connect-timeout 3 "http://localhost:${PORT}/health" >/dev/null 2>&1; then
    echo "✅ Worker läuft auf Port ${PORT}"
else
    echo "❌ Worker auf Port ${PORT} ist nicht erreichbar"
fi
EOF
chmod +x "$HOME/worker_status.sh"

# Worker starten
bash "$HOME/start_worker.sh" "${PORT}"
