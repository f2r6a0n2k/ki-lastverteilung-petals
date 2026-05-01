# KI-Lastverteilung - Nutzer-Informationen

## Projekt-Stand (Mai 2026)

### ✅ FUNKTIONIERT (einsatzbereit):
1. **llama.cpp Worker** (Round-Robin Lastverteilung)
   - **Worker:** Konfigurierbar über `configs/workers.json`
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
   - **Hinweis:** Worker werden aus `configs/workers.json` gelesen und automatisch im Round-Robin verteilt!

4. **Chat-Interface** (interaktiv)
   - **Datei:** `scripts/chat.sh`
   - **Start:** `bash scripts/chat.sh`
   - **Features:** Runde für Runde Eingabe, Worker-Wechsel automatisch

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

### 1. Worker konfigurieren

Bearbeite `configs/workers.json` und trage alle Worker ein:
```json
{
  "workers": [
    {"url": "http://192.168.1.100:8080", "name": "Server 1"},
    {"url": "http://192.168.1.101:8080", "name": "Server 2"}
  ]
}
```

### 2. Worker starten (auf jedem Gerät)

```bash
bash scripts/start_worker.sh 8080
```

### 3. Monitor starten (htop-Style):
```bash
bash scripts/monitor.sh
```
- Mit `Ctrl+C` beenden (stellt Bildschirm wieder her)

### 4. Prompt senden (Lastverteilung testen):
```bash
python3 scripts/llama_client.py "Wie ist das Wetter?"
python3 scripts/llama_client.py "Erkläre KI" --max-tokens 50
```
→ Prompts werden automatisch abwechselnd an alle konfigurierten Worker gesendet!

---

## WICHTIGE Hinweise:

1. **Worker konfigurieren:** Alle Worker-URLs werden in `configs/workers.json` eingetragen. Keine festen IPs im Code!
2. **pip-Problem auf Ubuntu 24.04:** Falls `pip install` mit `externally-managed-environment` fehlschlägt:
   - Installiere `pipx`: `sudo apt install pipx`
   - Oder verwende `--break-system-packages`: `python3 -m pip install --break-system-packages PAKET`
3. **Monitor zeigt alte Daten:** Falls der Monitor nicht aktualisiert, schließe ihn mit `Ctrl+C` und starte ihn neu.

---

## Video-Demo:
[![Monitor Demo](https://img.youtube.com/vi/nH_zVxJemSU/0.jpg)](https://youtu.be/nH_zVxJemSU)

---

## Projektstruktur:
```
KI_Lastverteilung_Petals/
├── configs/              # Konfigurationsdateien
│   ├── models.json       # Modell-Konfiguration
│   └── workers.json      # Worker-URLs (hier anpassen!)
├── docs/                 # Dokumentation
│   └── lastverteilung_ki_netzwerk.md  # Hauptkonzept
└── scripts/               # Skripte
    ├── install_petals_worker_linux.sh    # Linux Worker-Installation
    ├── install_petals_worker_termux.sh  # Android Worker-Installation
    ├── install_petals_worker_windows.ps1 # Windows Worker-Installation
    ├── uninstall_petals_worker_linux.sh # Linux Deinstallation
    ├── uninstall_petals_worker_termux.sh # Android Deinstallation
    ├── uninstall_petals_worker_windows.ps1 # Windows Deinstallation
    ├── start_worker.sh                   # Worker starten (Port wählbar)
    ├── monitor.sh                        # htop-Style Monitor ✅
    ├── llama_client.py                   # Round-Robin Client ✅
    └── chat.sh                           # Interaktives Chat-Interface ✅
```

✅ **System ist einsatzbereit!** Konfiguriere deine Worker in `configs/workers.json` und starte den Monitor.
