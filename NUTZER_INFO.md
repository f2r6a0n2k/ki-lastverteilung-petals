# KI-Lastverteilung - Nutzer-Informationen

## Projekt-Stand (Mai 2026)

### ✅ FUNKTIONIERT (einsatzbereit):
1. **llama.cpp Worker** (Round-Robin Lastverteilung)
   - **Worker:** Automatisch erkannt via `nmap` (Ports 8080-8089)
   - **Modell:** Llama-3.2-3B-Instruct (Q4_K_M, ~2 GB)
   - **System:** Ganze Prompts werden abwechselnd an Worker gesendet

2. **Monitor** (htop-Style, flackerfrei)
   - **Datei:** `scripts/monitor.sh`
   - **Start:** `bash scripts/monitor.sh`
   - **Features:** Scannt automatisch das Netzwerk, zeigt CPU-Last, Worker-Status; aktualisiert alle 2s
   - **Beenden:** `Ctrl+C` (stellt Originalbildschirm wieder her)

3. **Client** (Round-Robin)
   - **Datei:** `scripts/llama_client.py`
   - **Verwendung:** `python3 scripts/llama_client.py "Deine Frage" [--max-tokens ZAHL]`
   - **Hinweis:** Worker werden automatisch via `nmap` erkannt und im Round-Robin verteilt!

4. **Chat-Interface** (empfohlen – wie OpenCode)
   - **Datei:** `scripts/chat_interface.py`
   - **Start:** `python3 scripts/chat_interface.py`
   - **Features:** Konversationsverlauf, System-Prompt, Befehle (/clear, /system, /workers, /history)
   - **Vorteil:** Jeder Worker erhält den vollen Kontext der Unterhaltung

---

### ❌ FUNKTIONIERT (noch) NICHT:
- **Petals** (echte Lastverteilung – Prompt auf mehrere Rechner aufgeteilt)
  - **Grund:** Inkompatibilität mit Python 3.12 und PyTorch
  - **Status:** Projekt ist fertig gebaut, aber nicht lauffähig
  - **GitHub:** https://github.com/f2r6a0n2k/ki-lastverteilung-petals

---

## Worker starten:

Auf jedem Worker-Gerät:
```bash
bash scripts/start_worker.sh [PORT]
# Beispiel:
bash scripts/start_worker.sh 8080
```

Oder manuell:
```bash
cd ~/llama.cpp && nohup ./build/bin/llama-server -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf -c 1024 --port 8080 --host 0.0.0.0 -t $(nproc) > /tmp/llama-8080.log 2>&1 &
```

## Schnellstart (so nutzt Du das System):

### 1. Worker starten (auf jedem Gerät)

```bash
bash scripts/start_worker.sh 8080
```

### 2. Monitor starten (htop-Style):
```bash
bash scripts/monitor.sh
```
- Mit `Ctrl+C` beenden (stellt Bildschirm wieder her)

### 3. Prompt senden (Lastverteilung testen):
```bash
python3 scripts/llama_client.py "Wie ist das Wetter?"
python3 scripts/llama_client.py "Erkläre KI" --max-tokens 50
```
→ Worker werden automatisch via `nmap` erkannt! Prompts werden abwechselnd verteilt.

---

## WICHTIGE Hinweise:

1. **Automatische Worker-Erkennung:** Keine Konfiguration nötig – Worker werden via `nmap` im lokalen Netzwerk erkannt (Ports 8080-8089).
2. **Voraussetzung:** `nmap` muss installiert sein (`sudo apt install nmap`).
3. **pip-Problem auf Ubuntu 24.04:** Falls `pip install` mit `externally-managed-environment` fehlschlägt:
   - Installiere `pipx`: `sudo apt install pipx`
   - Oder verwende `--break-system-packages`: `python3 -m pip install --break-system-packages PAKET`
4. **Monitor zeigt alte Daten:** Falls der Monitor nicht aktualisiert, schließe ihn mit `Ctrl+C` und starte ihn neu.

---

## Video-Demo:
[![Monitor Demo](https://img.youtube.com/vi/nH_zVxJemSU/0.jpg)](https://youtu.be/nH_zVxJemSU)

---

## Projektstruktur:
```
KI_Lastverteilung_Petals/
├── configs/              # Konfigurationsdateien
│   └── models.json       # Modell-Konfiguration
├── docs/                 # Dokumentation
│   └── lastverteilung_ki_netzwerk.md  # Hauptkonzept
└── scripts/               # Skripte
    ├── install_worker_linux.sh           # Linux Worker-Installation (Petals)
    ├── install_worker_termux.sh          # Android Worker-Installation (llama.cpp)
    ├── install_worker_windows.ps1        # Windows Worker-Installation (Petals)
    ├── uninstall_worker_linux.sh         # Linux Deinstallation
    ├── uninstall_worker_termux.sh        # Android Deinstallation
    ├── uninstall_worker_windows.ps1      # Windows Deinstallation
    ├── start_worker.sh                   # Worker starten (Port wählbar)
    ├── monitor.sh                        # htop-Style Monitor ✅
    ├── llama_client.py                   # Einzelne Prompts (CLI)
    ├── chat.sh                           # Bash Chat (ohne Verlauf)
    └── chat_interface.py                 # Chat-Interface mit Verlauf ✅ Empfohlen
```

✅ **System ist einsatzbereit!** Starte Worker und nutze die automatische Erkennung.
