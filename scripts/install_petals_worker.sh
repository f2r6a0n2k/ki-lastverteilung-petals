#!/usr/bin/env bash
# install_petals_worker.sh - Petals Worker Installationsskript für Linux
#
# Dieses Skript installiert einen Petals Worker mit Python 3.11.
#
# Verwendung:
#   bash install_petals_worker.sh          # Installiert mit CPU-only
#   bash install_petals_worker.sh cuda     # Installiert mit CUDA-Unterstützung
#
# Nach der Installation:
#   source ~/petals-env/bin/activate
#   python -m petals.cli.run_server bigscience/bloom-petals --port 31330 --public_name "My-Worker"

set -e

CUDA_MODE="${1:-cpu}"
PYTHON_VERSION="3.11"
VENV_DIR="$HOME/petals-env"

echo "============================================="
echo "  Petals Worker Installation"
echo "============================================="
echo ""

# 1. Python 3.11 prüfen
echo "[1/6] Prüfe Python 3.11..."
if command -v python3.11 &>/dev/null; then
    echo "  Python 3.11 gefunden: $(python3.11 --version)"
else
    echo "  Python 3.11 nicht gefunden. Installation über deadsnakes PPA..."
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev
    echo "  Python 3.11 installiert: $(python3.11 --version)"
fi

# 2. Virtuelle Umgebung erstellen
echo ""
echo "[2/6] Erstelle virtuelle Umgebung..."
if [ -d "$VENV_DIR" ]; then
    echo "  Venv existiert bereits, wird neu erstellt..."
    rm -rf "$VENV_DIR"
fi
python3.11 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
echo "  Venv erstellt: $(python --version)"

# 3. PyTorch installieren
echo ""
echo "[3/6] Installiere PyTorch < 2.2 (für hivemind Kompatibilität)..."
if [ "$CUDA_MODE" = "cuda" ]; then
    echo "  Modus: CUDA"
    pip install 'torch>=2.0,<2.2' 'torchvision>=0.15,<0.17' 'torchaudio>=2.0,<2.2' \
        --index-url https://download.pytorch.org/whl/cu121
else
    echo "  Modus: CPU"
    pip install 'torch>=2.0,<2.2' 'torchvision>=0.15,<0.17' 'torchaudio>=2.0,<2.2' \
        --index-url https://download.pytorch.org/whl/cpu
fi

# 4. Build-Abhängigkeiten und hivemind
echo ""
echo "[4/6] Installiere hivemind..."
pip install 'setuptools<69' wheel 'grpcio-tools>=1.70'
pip install --no-build-isolation hivemind==1.1.10.post2

# 5. Petals und Abhängigkeiten
echo ""
echo "[5/6] Installiere Petals und Abhängigkeiten..."
pip install --no-deps petals
pip install peft==0.5.0 safetensors sentencepiece speedtest-cli==2.1.3 \
    tensor-parallel==1.0.23 tokenizers 'transformers>=4.32.0,<4.35.0' \
    'huggingface-hub>=0.11.1,<1.0' 'accelerate>=0.22.0,<0.25.0' \
    async-timeout bitsandbytes==0.41.1 cpufeature Dijkstar humanfriendly \
    'numpy<2.0'

# setuptools zurücksetzen
pip install --upgrade setuptools

# 6. Verifizieren
echo ""
echo "[6/6] Verifiziere Installation..."
if python -m petals.cli.run_server --help &>/dev/null; then
    echo "  Petals CLI: OK"
else
    echo "  FEHLER: Petals CLI nicht erreichbar!"
    exit 1
fi

echo ""
echo "============================================="
echo "  Installation abgeschlossen!"
echo "============================================="
echo ""
echo "Worker starten mit:"
echo ""
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "  # Mit GPU:"
echo "  python -m petals.cli.run_server bigscience/bloom-petals --port 31330 --public_name \"My-Worker\""
echo ""
echo "  # CPU-only (langsam):"
echo "  python -m petals.cli.run_server bigscience/bloom-petals --port 31330 --public_name \"My-Worker\" --num_blocks 4 --device cpu"
echo ""
echo "Firewall öffnen (falls nötig):"
echo ""
echo "  sudo ufw allow 31330/tcp"
echo ""
