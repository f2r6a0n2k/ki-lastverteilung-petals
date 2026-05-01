# KI-Lastverteilung Petals - Nutzer-Informationen

## Projekt-Stand (Mai 2026)

### ✅ FUNKTIONIERT (einsatzbereit):
1. **llama.cpp Worker** (Round-Robin Lastverteilung)
   - **Elitebook** (192.168.178.105:8080) – ✅ AKTIV
   - **Lokal** (192.168.178.109:8081) – ✅ AKTIV
   - **Modell:** TinyLlama-1.1B-Chat (Q4_K_M, ~700MB)
   - **System:** Ganze Prompts werden abwechselnd an Worker gesendet

2. **Monitor** (htop-Style, flackerfrei)
   - **Datei:** `scripts/monitor.sh`
   - **Start:** `bash /home/frank/Dokumente/KI_Lastverteilung_Petals/scripts/monitor.sh`
   - **Features:** Zeigt CPU-Last, Worker-Status, Inferenz-Zeiten; aktualisiert alle 2s
   - **Beenden:** `Ctrl+C` (stellt Originalbildschirm wieder her)

3. **Client** (Round-Robin)
   - **Datei:** `scripts/llama_client.py` ← **WICHTIG: Nicht `petals_client.py` nutzen!**
   - **Verwendung:** `python3 /home/frank/Dokumente/KI_Lastverteilung_Petals/scripts/llama_client.py "Deine Frage" [--max-tokens ZAHL]`
   - **Beispiel:** `python3 scripts/llama_client.py "Wie ist das Wetter?"`
   - **Hinweis:** Prompts werden automatisch zwischen Elitebook (8080) und Lokal (8081) verteilt!

---

### ❌ FUNKTIONIERT (noch) NICHT:
- **Petals** (echte Lastverteilung – Prompt auf mehrere Rechner aufgeteilt)
  - **Grund:** Inkompatibilität mit Python 3.12 und PyTorch 2.11
  - **Status:** Projekt ist fertig gebaut, aber nicht lauffähig
  - **GitHub:** https://github.com/f2r6a0n2k/ki-lastverteilung-petals

---

## GitHub-Repositories:
1. **ki-lastverteilung-worker** (llama.cpp Lösung – einfache Lastverteilung)  
   https://github.com/f2r6a0n2k/ki-lastverteilung-worker
   
2. **ki-lastverteilung-petals** (Petals – echte Lastverteilung) ← **aktuelles Projekt**  
   https://github.com/f2r6a0n2k/ki-lastverteilung-petals  
   - Enthält: Installationsskripte (Linux, Windows, Android), Deinstallationsskripte, Monitor, Client, Video-Guide

---

## Schnellstart (so nutzt Du das System):

### 1. Worker starten (falls nicht aktiv):
**Lokal (192.168.178.109:8081):**
```bash
cd ~/llama.cpp && nohup ./build/bin/llama-server -m models/tinyllama-q4.gguf -c 1024 --port 8081 --host 0.0.0.0 -t $(nproc) > /tmp/llama-8081.log 2>&1 &
```

**Elitebook (192.168.178.105:8080):**
```bash
# Auf Elitebook ausführen:
cd ~/llama.cpp && nohup ./build/bin/llama-server -m models/tinyllama-q4.gguf -c 1024 --port 8080 --host 0.0.0.0 -t $(nproc) > /tmp/llama-8080.log 2>&1 &
# Oder einfach das Start-Skript nutzen:
bash ~/start_elitebook_worker.sh
```

### 2. Monitor starten (htop-Style):
```bash
bash /home/frank/Dokumente/KI_Lastverteilung_Petals/scripts/monitor.sh
```
- Mit `Ctrl+C` beenden (stellt Bildschirm wieder her)

### 3. Prompt senden (Lastverteilung testen):
```bash
# WICHTIG: llama_client.py verwenden (nie petals_client.py!)
python3 /home/frank/Dokumente/KI_Lastverteilung_Petals/scripts/llama_client.py "Wie ist das Wetter?"
python3 /home/frank/Dokumente/KI_Lastverteilung_Petals/scripts/llama_client.py "Erkläre KI" --max-tokens 50
```
→ Prompts werden automatisch abwechselnd an Elitebook (8080) und Lokal (8081) gesendet!

---

## WICHTIGE Hinweise:

1. **Immer `llama_client.py` verwenden** – `petals_client.py` existiert nicht mehr bzw. ist nicht funktionsfähig!
2. **pip-Problem auf Ubuntu 24.04:** Falls `pip install` mit `externally-managed-environment` fehlschlägt:
   - Installiere `pipx`: `sudo apt install pipx`
   - Oder verwende `--break-system-packages`: `python3 -m pip install --break-system-packages PAKET`
3. **Elitebook-Worker neustarten:** Falls er inaktiv ist:
   ```bash
   sshpass -p "cornholio" ssh user@192.168.178.105 "cd ~/llama.cpp && pkill -f llama-server; nohup ./build/bin/llama-server -m models/tinyllama-q4.gguf -c 1024 --port 8080 --host 0.0.0.0 -t \$(nproc) > /tmp/llama-8080.log 2>&1 &"
   ```
4. **Monitor zeigt alte Daten:** Falls der Monitor nicht aktualisiert, schließe ihn mit `Ctrl+C` und starte ihn neu.

---

## Video-Demo:
[![Monitor Demo](https://img.youtube.com/vi/nH_zVxJemSU/0.jpg)](https://youtu.be/nH_zVxJemSU)

---

## Projektstruktur:
```
KI_Lastverteilung_Petals/
├── configs/              # Modell-Konfiguration (für Petals)
│   └── models.json
├── docs/                 # Dokumentation
│   ├── lastverteilung_ki_netzwerk.md  # Hauptkonzept
│   └── PROJEKT_STATUS.md             # Status-Übersicht
└── scripts/               # Skripte
    ├── install_petals_worker_linux.sh    # Linux Worker-Installation
    ├── install_petals_worker_termux.sh  # Android Worker-Installation
    ├── install_petals_worker_windows.ps1 # Windows Worker-Installation
    ├── uninstall_petals_worker_linux.sh # Linux Deinstallation
    ├── uninstall_petals_worker_termux.sh # Android Deinstallation
    ├── uninstall_petals_worker_windows.ps1 # Windows Deinstallation
    ├── monitor.sh                 # htop-Style Monitor ✅
    └── llama_client.py             # Round-Robin Client ✅ (nicht petals_client.py!)
```

✅ **System ist einsatzbereit!** Starte den Monitor und teste die Lastverteilung.
