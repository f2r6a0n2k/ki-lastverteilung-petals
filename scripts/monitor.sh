#!/bin/bash
# Monitor für KI-Lastverteilung (Petals-Projekt)
# Zeigt Status der Worker (llama.cpp als Fallback, da Petals noch nicht läuft)
# Ausführen: bash /home/frank/Dokumente/KI_Lastverteilung_Petals/scripts/monitor_petals.sh

while true; do
  clear
  echo "=========================================="
  echo "   KI-Lastverteilung Monitor (Petals-Projekt)"
  echo "   Zeit: $(date +%T)"
  echo "=========================================="
  
  # Elitebook Worker (105:8080)
  echo ""
  echo "📍 Elitebook (192.168.178.105:8080)"
  if curl -s --connect-timeout 2 http://192.168.178.105:8080/health >/dev/null 2>&1; then
    echo "   Status: ✅ AKTIV (llama.cpp)"
    # CPU-Last Elitebook
    sshpass -p "cornholio" ssh -o StrictHostKeyChecking=no user@192.168.178.105 "top -b -n1 | head -4 | tail -1" 2>/dev/null | sed 's/^/   /'
    # Inferenz-Test
    start=$SECONDS
    curl -s --connect-timeout 3 -X POST "http://192.168.178.105:8080/completion" \
      -H "Content-Type: application/json" \
      -d '{"prompt":"Hi","max_tokens":5}' >/dev/null 2>&1
    dauer=$((SECONDS - start))
    echo "   Test-Inferenz: ${dauer}s"
  else
    echo "   Status: ❌ INAKTIV"
    echo "   Start-Befehl (auf Elitebook):"
    echo "   cd ~/llama.cpp && nohup ./build/bin/llama-server -m models/tinyllama-q4.gguf -c 1024 --port 8080 --host 0.0.0.0 -t \\$(nproc) &"
  fi
  
  # Lokal Worker (109:8081)
  echo ""
  echo "📍 Lokal (192.168.178.109:8081)"
  if curl -s --connect-timeout 2 http://192.168.178.109:8081/health >/dev/null 2>&1; then
    echo "   Status: ✅ AKTIV (llama.cpp)"
    # CPU-Last Lokal
    top -b -n1 | head -4 | tail -1 | sed 's/^/   /'
    # Inferenz-Test
    start=$SECONDS
    curl -s --connect-timeout 3 -X POST "http://192.168.178.109:8081/completion" \
      -H "Content-Type: application/json" \
      -d '{"prompt":"Hi","max_tokens":5}' >/dev/null 2>&1
    dauer=$((SECONDS - start))
    echo "   Test-Inferenz: ${dauer}s"
  else
    echo "   Status: ❌ INAKTIV"
    echo "   Start-Befehl (lokal):"
    echo "   cd ~/llama.cpp && nohup ./build/bin/llama-server -m models/tinyllama-q4.gguf -c 1024 --port 8081 --host 0.0.0.0 -t \\$(nproc) &"
  fi
  
  # Koordinator (Round-Robin) - läuft lokal auf Port 5000
  echo ""
  echo "📊 Koordinator (Round-Robin)"
  if ps aux | grep -q "[u]vicorn koordinator"; then
    echo "   Status: ✅ AKTIV (http://192.168.178.109:5000)"
  else
    echo "   Status: ❌ INAKTIV"
    echo "   Start-Befehl (lokal):"
    echo "   cd ~/llama.cpp && nohup python3 -m uvicorn koordinator:app --host 0.0.0.0 --port 5000 &"
  fi
  
  # Hinweis auf Petals
  echo ""
  echo "ℹ️  Petals-Projekt: Für echte Lastverteilung (Modell-Splitting)"
  echo "   Status: ⚠️  Noch nicht lauffähig (Python 3.12 Inkompatibilität)"
  
  echo ""
  echo "Drücke Ctrl+C zum Beenden"
  sleep 5
done
