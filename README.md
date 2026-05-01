# KI-Lastverteilung - Verteilte KI-Inferenz

[![Watch the video](https://img.youtube.com/vi/nH_zVxJemSU/0.jpg)](https://youtu.be/nH_zVxJemSU)

Lastverteilung über mehrere Rechner: Prompts werden abwechselnd (Round-Robin) an Worker gesendet.
Worker werden automatisch via `nmap` im lokalen Netzwerk erkannt (Ports 8080–8089).

## Projektstruktur

```
KI_Lastverteilung_Petals/
├── configs/                    # Konfigurationsdateien
│   └── models.json            # Modell-Konfiguration (anpassbar)
├── docs/                       # Dokumentation
│   └── lastverteilung_ki_netzwerk.md  # Hauptkonzept
└── scripts/                    # Skripte
    ├── install_petals_worker_linux.sh     # Linux Worker-Installation
    ├── install_petals_worker_windows.ps1   # Windows Worker
    ├── install_petals_worker_termux.sh     # Android (Termux) Worker
    ├── uninstall_petals_worker_linux.sh   # Linux Deinstallation
    ├── uninstall_petals_worker_windows.ps1 # Windows Deinstallation
    ├── uninstall_petals_worker_termux.sh  # Termux Deinstallation
    ├── start_worker.sh                    # Worker starten (Port wählbar)
    ├── llama_client.py                    # Einzelne Prompts (CLI)
    ├── chat.sh                            # Bash Chat-Interface (ohne Verlauf)
    ├── chat_interface.py                  # Chat-Interface mit Verlauf ✅ Empfohlen
    └── monitor.sh                         # Echtzeit-Monitoring (htop-Style)
```

## Schnellstart

### 1. Worker auf allen Geräten starten

Auf jedem Worker-Gerät:
```bash
bash scripts/start_worker.sh [PORT]
```

Oder manuell:
```bash
cd ~/llama.cpp && nohup ./build/bin/llama-server -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf -c 1024 --port 8080 --host 0.0.0.0 -t $(nproc) > /tmp/llama-8080.log 2>&1 &
```

### 2. Chat-Interface (empfohlen)

Vollständiges Chat-Erlebnis mit Konversationsverlauf, System-Prompt und Befehlen:
```bash
python3 scripts/chat_interface.py
```

Befehle im Chat:
- `/clear` – Konversation zurücksetzen
- `/system [text]` – System-Prompt ändern
- `/workers` – Verfügbare Worker zeigen
- `/history` – Nachrichtenanzahl
- `/quit` – Beenden

### 3. Einzelne Prompts senden

```bash
python3 scripts/llama_client.py "Wie ist das Wetter?"
python3 scripts/llama_client.py "Erkläre KI" --max-tokens 50
```

### 4. Monitoring starten

```bash
bash scripts/monitor.sh
```

## Verfügbare Modelle

| Modell | Parameter | Geräte (min) | Speicher/Gerät | Status |
|--------|-----------|----------------|-----------------|--------|
| Llama-3.2-3B-Instruct | 3B | 1 | ~2GB (Q4_K_M) | ✅ Standard |
| TinyLlama-1.1B | 1.1B | 1 | ~0.7GB | ⬜ Veraltet |

## Deinstallation (Petals Worker)

**Linux:**
```bash
bash scripts/uninstall_petals_worker_linux.sh 8080
```

**Windows:**
```powershell
.\scripts\uninstall_petals_worker_windows.ps1 8080
```

**Android (Termux):**
```bash
bash scripts/uninstall_petals_worker_termux.sh 8080
```

## Monitor-Skript (htop-Style)

Für eine flackerfreie Echtzeit-Anzeige (wie htop):

```bash
bash scripts/monitor.sh
```

Das Skript scannt automatisch das lokale Netzwerk nach offenen Worker-Ports (8080-8089) und zeigt CPU-Last sowie Status jedes Workers.

### Eingebettetes Video (Demo):
[![Monitor Demo](https://img.youtube.com/vi/nH_zVxJemSU/0.jpg)](https://youtu.be/nH_zVxJemSU)

Oder direkt: https://youtu.be/nH_zVxJemSU

## Voraussetzungen

- **llama.cpp Worker:** Alle Geräte im gleichen LAN
- **Client:** Python 3.8+, `requests`, `nmap` (`sudo apt install nmap`)
- **Monitor:** Bash, `nmap` (für Netzwerk-Scan)

## Hinweise

- Alle Daten bleiben lokal (keine Cloud-Abhängigkeit)
- Worker werden automatisch via `nmap` erkannt (Ports 8080-8089)
- Mehrere Worker im Netzwerk erhöhen die Verfügbarkeit
- Llama-3.2-3B-Instruct ist Standardmodell (Q4_K_M, ~2GB)
- Prompts werden abwechselnd an Worker gesendet (Round-Robin)
- `chat_interface.py` sendet den gesamten Konversationsverlauf mit – jeder Worker hat vollen Kontext
