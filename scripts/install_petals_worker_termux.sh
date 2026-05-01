#!/bin/bash
# Petals Worker Installation für Android (Termux)
# Verwendung: bash install_petals_worker_termux.sh [PORT] [MODELL]
# Beispiel: bash install_petals_worker_termux.sh 8080 meta-llama/Llama-2-7b-chat-hf

PORT=${1:-8080}
MODEL=${2:-"TinyLlama/TinyLlama-1.1B-Chat-v1.0"}
WORKER_NAME="Petals-Worker-Termux-$PORT"

echo "=== Petals Worker Installation (Termux) ==="
pkg update && pkg install -y python git curl

# Petals und PyTorch installieren (CPU-Version)
pip install --upgrade pip
pip install petals torch --index-url https://download.pytorch.org/whl/cpu

# Start-Skript erstellen
cat > "$HOME/start_petals_worker.sh" << INNER_EOF
#!/bin/bash
PORT=$PORT
MODEL="$MODEL"
WORKER_NAME="$WORKER_NAME"
echo "Starte Petals Worker: \$WORKER_NAME auf Port \$PORT mit Modell: \$MODEL"
python -m petals.cli.run_server \$MODEL --port \$PORT --public_name "\$WORKER_NAME" > /tmp/petals-worker-\$PORT.log 2>&1 &
echo "Worker gestartet. Log: /tmp/petals-worker-\$PORT.log"
INNER_EOF
chmod +x "$HOME/start_petals_worker.sh"

# Worker starten
bash "$HOME/start_petals_worker.sh"

echo "✅ Petals Worker läuft auf Port $PORT"
echo "   Modell: $MODEL"
echo "   Name: $WORKER_NAME"
echo "   Log: /tmp/petals-worker-$PORT.log"
