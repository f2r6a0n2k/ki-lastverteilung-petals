#!/bin/bash
# Echtzeit-Monitoring für Petals KI-Netzwerk
# Verwendung: bash monitor_petals.sh
# Voraussetzung: pip install petals; sshpass installiert (sudo apt install sshpass)

CONFIG_FILE="$(dirname "$0")/../configs/models.json"

while true; do
  clear
  echo "=== Petals Lastverteilung Monitor $(date +%T) ==="
  
  # Konfiguration anzeigen
  if [ -f "$CONFIG_FILE" ]; then
    echo -e "\n📋 Aktive Modell-Konfiguration:"
    cat "$CONFIG_FILE" | grep -A2 '"default_model"' | head -3
  fi
  
  echo -e "\n📍 Lokaler Rechner ($(hostname)):"
  top -b -n1 | head -4 | grep -E "load|Cpu"
  if pgrep -f "petals.cli.run_server" > /dev/null; then
    echo "  Petals Worker: ✅ aktiv"
  else
    echo "  Petals Worker: ❌ inaktiv"
  fi
  
  echo -e "\n📍 Elitebook (192.168.178.105):"
  sshpass -p "cornholio" ssh -o StrictHostKeyChecking=no user@192.168.178.105 "top -b -n1 | head -4 | grep -E 'load|Cpu'" 2>/dev/null
  sshpass -p "cornholio" ssh -o StrictHostKeyChecking=no user@192.168.178.105 "pgrep -f 'petals.cli.run_server' > /dev/null && echo '  Petals Worker: ✅ aktiv' || echo '  Petals Worker: ❌ inaktiv'" 2>/dev/null
  
  echo -e "\n📊 Modell-Test (via Petals):"
  if command -v python3 &> /dev/null && python3 -c "import petals" 2>/dev/null; then
    python3 -c "
import sys
try:
    from petals import AutoDistributedConfig
    config = AutoDistributedConfig.from_pretrained('TinyLlama/TinyLlama-1.1B-Chat-v1.0')
    print(f'  Verbunden mit {len(config.initial_peers)} Petals-Peers')
except Exception as e:
    print(f'  Fehler: {e}')
" 2>/dev/null
  else
    echo "  Petals nicht installiert oder nicht konfiguriert"
  fi
  
  sleep 5
done
