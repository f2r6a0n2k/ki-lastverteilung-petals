#!/bin/bash
# KI Worker Installation für Linux (Ubuntu/Debian)
# Verwendung: bash install_worker_linux.sh [PORT] [MODELL]
# Beispiel: bash install_worker_linux.sh 8080 bartowski/Llama-3.2-3B-Instruct-GGUF

PORT=${1:-8080}
MODEL=${2:-"bartowski/Llama-3.2-3B-Instruct-GGUF"}
WORKER_NAME="KI-Worker-$(hostname)-$PORT"
INSTALL_DIR="$HOME/ki_worker"

echo "=== KI Worker Installation (Linux) ==="

# Abhängigkeiten installieren
sudo apt update && sudo apt install -y python3-pip python3-venv git curl

# Installationsverzeichnis erstellen
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate

# Installationsfunktion mit pipx-Fallback
install_pkg() {
    if pip install "$1" 2>&1 | grep -q "externally-managed-environment"; then
        echo "pip blockiert, versuche pipx..."
        pipx install "$1" || echo "Fehler: $1 konnte nicht installiert werden"
    else
        echo "$1 erfolgreich installiert"
    fi
}

# Petals und PyTorch installieren (CPU-Version)
pip install --upgrade pip 2>&1 | grep -q "externally-managed-environment" && pipx install --upgrade pip || pip install --upgrade pip
install_pkg "torch --index-url https://download.pytorch.org/whl/cpu"
install_pkg petals

# Firewall öffnen
sudo ufw allow "$PORT/tcp"

# Start-Skript erstellen
cat > "$HOME/start_ki_worker.sh" << INNER_EOF
#!/bin/bash
source "$INSTALL_DIR/venv/bin/activate"
PORT=$PORT
MODEL="$MODEL"
WORKER_NAME="$WORKER_NAME"
echo "Starte KI Worker: \$WORKER_NAME auf Port \$PORT mit Modell: \$MODEL"
python3 -m petals.cli.run_server \$MODEL --port \$PORT --public_name "\$WORKER_NAME" > /tmp/ki-worker-\$PORT.log 2>&1 &
echo "Worker gestartet. Log: /tmp/ki-worker-\$PORT.log"
INNER_EOF
chmod +x "$HOME/start_ki_worker.sh"

# Worker starten
bash "$HOME/start_ki_worker.sh"

echo "✅ KI Worker läuft auf Port $PORT"
echo "   Modell: $MODEL"
echo "   Name: $WORKER_NAME"
echo "   Log: /tmp/ki-worker-$PORT.log"
echo "   Stoppen: pkill -f 'petals.cli.run_server.*$PORT'"
