# KI-Lastverteilung Petals - Verteilte KI-Inferenz

<iframe src="https://youtu.be/nH_zVxJemSU?rel=0" width="560" height="315" frameborder="0" allowfullscreen="" >

Vollständiges Projekt für echte Lastverteilung: Einzelne Prompts werden auf mehrere Rechner verteilt (nicht nur ganze Prompts an einzelne Worker).

## Projektstruktur

```
KI_Lastverteilung_Petals/
├── configs/                    # Konfigurationsdateien
│   └── models.json            # Modell-Konfiguration (anpassbar)
├── docs/                       # Dokumentation
│   ├── lastverteilung_ki_netzwerk.md  # Hauptkonzept
│   └── video_guide_petals.md         # Skript für NotebookLM-Video
└── scripts/                    # Installations- und Hilfsskripte
    ├── install_petals_worker_linux.sh     # Linux Worker
    ├── install_petals_worker_windows.ps1   # Windows Worker
    ├── install_petals_worker_termux.sh     # Android (Termux) Worker
    ├── uninstall_petals_worker_linux.sh   # Linux Deinstallation
    ├── uninstall_petals_worker_windows.ps1 # Windows Deinstallation
    ├── uninstall_petals_worker_termux.sh  # Termux Deinstallation
    ├── petals_client.py                   # Konfigurierbarer Client
    └── monitor_petals.sh                 # Echtzeit-Monitoring
```

## Schnellstart

### 1. Worker auf allen Geräten installieren

**Linux (Ubuntu/Debian):**
```bash
bash scripts/install_petals_worker_linux.sh 8080
# Mit eigenem Modell:
bash scripts/install_petals_worker_linux.sh 8080 meta-llama/Llama-2-7b-chat-hf
```

**Windows (PowerShell als Administrator):**
```powershell
.\scripts\install_petals_worker_windows.ps1 8080
# Mit eigenem Modell:
.\scripts\install_petals_worker_windows.ps1 8080 meta-llama/Llama-2-7b-chat-hf
```

**Android (Termux):**
```bash
bash scripts/install_petals_worker_termux.sh 8080
```

### 2. Modell konfigurieren

Bearbeite `configs/models.json`:
- Ändere `"default_model"` auf dein Wunschmodell
- Füge weitere Modelle hinzu (TinyLlama, Llama-2-7B, Llama-2-13B, etc.)

### 3. Client nutzen (Prompt senden)

```bash
# Standardmodell nutzen
python3 scripts/petals_client.py "Wie ist das Wetter?"

# Verfügbare Modelle anzeigen
python3 scripts/petals_client.py --list-models

# Bestimmtes Modell nutzen
python3 scripts/petals_client.py "Erkläre KI" --modell meta-llama/Llama-2-7b-chat-hf
```

### 4. Monitoring starten

```bash
bash scripts/monitor_petals.sh
```

## Verfügbare Modelle (in `configs/models.json`)

| Modell | Parameter | Geräte (min) | Speicher/Gerät | Petals-Support |
|--------|-----------|----------------|-----------------|---------------|
| TinyLlama-1.1B | 1.1B | 1 | ~0.7GB | ✅ |
| Llama-2-7B | 7B | 2-3 | ~3.5GB | ✅ |
| Llama-2-13B | 13B | 4+ | ~3.5GB | ✅ |

## Unterschied zur einfachen Lastverteilung

| Feature | Einfach (llama.cpp) | Petals (dieses Projekt) |
|---------|---------------------|------------------------|
| Prompt-Verteilung | ❌ Ganzer Prompt auf 1 Rechner | ✅ Prompt auf mehrere Rechner verteilt |
| Modellgröße | Nur kleine Modelle (1.1B) | Große Modelle (7B, 13B+) möglich |
| Hardware-Nutzung | Jeder lädt volles Modell | Jeder lädt nur Modell-Teile |
| Skalierbarkeit | Begrenzt | Sehr gut (Schwarm-Intelligenz) |

## Deinstallation

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

## Video-Erstellung mit NotebookLM

1. Lade den gesamten Ordner `KI_Lastverteilung_Petals` zu NotebookLM hoch
2. Nutze `docs/video_guide_petals.md` als Hauptquelle
3. Füge `configs/models.json` und `docs/lastverteilung_ki_netzwerk.md` als Zusatzquellen hinzu
4. Lass dir ein Skript mit Zeitstempeln generieren
5. Nutze die Audio-Option für Voiceover

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

- **Alle Geräte:** Python 3.8+, pip
- **Linux:** sudo-Rechte für Firewall
- **Windows:** PowerShell als Administrator
- **Android:** Termux (aus F-Droid)
- **Netzwerk:** Alle Geräte im gleichen LAN

## Hinweise

- Alle Daten bleiben lokal (keine Cloud-Abhängigkeit)
- Modell wird bei ersten Start heruntergeladen (einmalig)
- Mehrere Worker im Netzwerk erhöhen die Verfügbarkeit
- TinyLlama-1.1B ist Standard (läuft auf fast allem)
