# KI-Lastverteilung - Verteilte KI-Inferenz

[![Watch the video](https://img.youtube.com/vi/nH_zVxJemSU/0.jpg)](https://youtu.be/nH_zVxJemSU)

Letztverteilung über mehrere Rechner: Prompts werden abwechselnd (Round-Robin) an Worker gesendet.

## Projektstruktur

```
KI_Lastverteilung_Petals/
├── configs/                    # Konfigurationsdateien
│   └── models.json            # Modell-Konfiguration (anpassbar)
├── docs/                       # Dokumentation
│   └── lastverteilung_ki_netzwerk.md  # Hauptkonzept
└── scripts/                    # Installations- und Hilfsskripte
    ├── install_petals_worker_linux.sh     # Linux Worker
    ├── install_petals_worker_windows.ps1   # Windows Worker
    ├── install_petals_worker_termux.sh     # Android (Termux) Worker
    ├── uninstall_petals_worker_linux.sh   # Linux Deinstallation
    ├── uninstall_petals_worker_windows.ps1 # Windows Deinstallation
    ├── uninstall_petals_worker_termux.sh  # Termux Deinstallation
    ├── llama_client.py                    # Round-Robin Client
    ├── chat.sh                            # Chat-Interface
    └── monitor.sh                         # Echtzeit-Monitoring (htop-Style)
```

## Schnellstart

### 1. Worker auf allen Geräten starten

**Lokal (Port 8081):**
```bash
bash ~/start_local_worker.sh
```

**Elitebook (Port 8080):**
```bash
ssh user@192.168.178.105 'bash ~/start_elitebook_worker.sh'
```

Oder manuell:
```bash
cd ~/llama.cpp && nohup ./build/bin/llama-server -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf -c 1024 --port 8081 --host 0.0.0.0 -t $(nproc) > /tmp/llama-8081.log 2>&1 &
```

### 2. Client nutzen (Prompt senden)

```bash
# Standardmodell nutzen (Round-Robin)
python3 scripts/llama_client.py "Wie ist das Wetter?"

# Mit maximaler Token-Anzahl
python3 scripts/llama_client.py "Erkläre KI" --max-tokens 50
```

### 3. Chat-Interface (interaktiv)

```bash
bash scripts/chat.sh
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

Das Skript nutzt den alternativen Bildschirm-Puffer – **kein Flackern**, Cursor versteckt, reagiert sofort auf `Ctrl+C` (stellt den Originalbildschirm wieder her).

### Eingebettetes Video (Demo):
[![Monitor Demo](https://img.youtube.com/vi/nH_zVxJemSU/0.jpg)](https://youtu.be/nH_zVxJemSU)

Oder direkt: https://youtu.be/nH_zVxJemSU

## Voraussetzungen

- **llama.cpp Worker:** Alle Geräte im gleichen LAN
- **Client:** Python 3.8+, `requests` Library (`pip install requests`)
- **Monitor:** Bash, sshpass (für Remote-CPU-Auslesung)

## Hinweise

- Alle Daten bleiben lokal (keine Cloud-Abhängigkeit)
- Modell wird bei ersten Start heruntergeladen (einmalig)
- Mehrere Worker im Netzwerk erhöhen die Verfügbarkeit
- Llama-3.2-3B-Instruct ist Standardmodell (Q4_K_M, ~2GB)
- Prompts werden abwechselnd an Worker gesendet (Round-Robin)
