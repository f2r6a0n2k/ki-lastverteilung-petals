#!/usr/bin/env bash
# start_koordinator.sh - Startet den KI-Lastverteilung Koordinator
#
# Verwendung:
#   bash scripts/start_koordinator.sh              # llama.cpp Modus
#   bash scripts/start_koordinator.sh --petals     # Petals Gateway
#   bash scripts/start_koordinator.sh --petals --private-swarm  # Privater Swarm
#   bash scripts/start_koordinator.sh --petals --model bigscience/bloom-petals
#   bash scripts/start_koordinator.sh --petals --token hf_xxx
#
# Als Hintergrunddienst:
#   bash scripts/start_koordinator.sh --petals &> /tmp/koordinator.log &

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Prüfe welche Python-Umgebung verfügbar ist
PYTHON=""
if [ -d "$HOME/petals-env" ]; then
    PYTHON="$HOME/petals-env/bin/python"
    echo "[Koordinator] Verwende Petals venv: $PYTHON"
elif [ -d "$HOME/llama-env" ]; then
    PYTHON="$HOME/llama-env/bin/python"
    echo "[Koordinator] Verwende llama venv: $PYTHON"
else
    PYTHON="python3"
    echo "[Koordinator] Verwende System-Python: $PYTHON"
fi

# Prüfe Abhängigkeiten
echo "[Koordinator] Prüfe Abhängigkeiten..."
$PYTHON -c "import fastapi, uvicorn" 2>/dev/null || {
    echo "[Koordinator] Installiere fehlende Abhängigkeiten..."
    $PYTHON -m pip install fastapi uvicorn requests pydantic 2>/dev/null || sudo $PYTHON -m pip install fastapi uvicorn requests pydantic
}

if [ "$1" = "--petals" ] || echo "$*" | grep -q "petals"; then
    $PYTHON -c "import petals" 2>/dev/null || {
        echo "[Koordinator] WARNUNG: Petals nicht installiert!"
        echo "[Koordinator] Installation mit: bash scripts/install_petals_worker.sh"
        echo ""
    }
fi

echo "[Koordinator] Starte auf Port 5000..."
echo "[Koordinator] Optionen: $*"
echo ""

cd "$PROJECT_DIR"
exec $PYTHON scripts/koordinator.py "$@"
