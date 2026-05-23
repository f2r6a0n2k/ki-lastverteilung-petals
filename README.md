# KI-Lastverteilung – Petals-Forschung (Archiv)

> **Hinweis:** Die aktive Entwicklung dieses Projekts wurde in das Repository  
> **[github.com/f2r6a0n2k/ki-lastverteilung-worker](https://github.com/f2r6a0n2k/ki-lastverteilung-worker)** verlagert.  
> Dieses Repository dokumentiert die Petals-Integration und ältere Architekturkonzepte.

[![Watch the video](https://img.youtube.com/vi/nH_zVxJemSU/0.jpg)](https://youtu.be/nH_zVxJemSU)

Intelligentes System zur Lastverteilung von KI-Inferenz über mehrere Rechner im lokalen Netzwerk. Erkennt automatisch verfügbare Worker und entscheidet dynamisch, ob Anfragen über **llama.cpp** (parallele Worker) oder **Petals** (verteilte Modell-Partitionierung) verarbeitet werden.

## Projektstruktur

```
KI_Lastverteilung_Petals/
├── credentials.json              # SSH-Zugangsdaten (wird nicht getrackt!)
├── scripts/
│   ├── koordinator.py            # FastAPI-Server mit auto-detect: Petals vs llama.cpp
│   ├── llama_client.py           # CLI-Client für einzelne Prompts
│   ├── chat_interface.py         # Chat mit Verlauf
│   ├── monitor.sh                # Echtzeit-Monitoring (htop-Style)
│   ├── setup_credentials.sh      # Einmalige Einrichtung der SSH-Credentials
│   ├── install_worker_*.sh       # Worker-Installer (Linux/Termux)
│   └── uninstall_worker_*.sh     # Worker-Deinstallation
```

## Schnellstart

### 1. SSH-Credentials einrichten (einmalig)

```bash
bash scripts/setup_credentials.sh
```

Erstellt `credentials.json` (wird von Git ignoriert). Alternativ manuell erstellen:

```json
{
    "default_user": "user",
    "default_pass": "geheim",
    "nodes": {
        "10.0.0.42": {"user": "admin", "pass": "anders"}
    }
}
```

### 2. Koordinator starten

```bash
cd ~/Dokumente/KI_Lastverteilung_Petals
python3 scripts/koordinator.py &
```

**Hinweis:** Verwende `python3` (System-Python), NICHT `~/petals-env/bin/python` – die virtuelle Umgebung hat einen Pydantic-Konflikt (Petals braucht v1, FastAPI v2).

Der Koordinator scannt automatisch das Netzwerk und entscheidet:
- **≥2 Nodes mit Petals + gute Latenz** → Petals-Modus (verteilte Inferenz)
- **Sonst** → llama.cpp-Modus (parallele Worker mit Score-basierter Auswahl)

### 3. Worker installieren

#### Linux (Ubuntu/Debian) – Petals oder llama.cpp

```bash
bash scripts/install_worker_linux.sh [PORT] [MODELL]
# Beispiel:
bash scripts/install_worker_linux.sh 8080 bartowski/Llama-3.2-3B-Instruct-GGUF
```

Installiert Petals mit PyTorch (CPU). Der Worker stellt ein vollständiges Modell-Layer-Partitionierung bereit.

#### Android (Termux) – nur llama.cpp

> **Wichtig:** Android unterstützt KEIN Petals (nur llama.cpp). Verwende diesen Installer für Android-Geräte.

```bash
bash scripts/install_worker_termux.sh [PORT]
# Beispiel:
bash scripts/install_worker_termux.sh 8080
```

**Was passiert:**
1. Installiert `cmake`, `clang`, `git`, `wget` via `pkg`
2. Klont und kompiliert llama.cpp mit **CMake** (Makefile wurde ersetzt)
3. Lädt das Modell per **wget** direkt von HuggingFace (nicht `hf` CLI – hf-xet baut nicht auf Termux)
4. Erstellt `start_worker.sh`, `stop_worker.sh`, `worker_status.sh`

**Bekannte Probleme (umgangen):**
- ❌ `aarch64-unknown-linux-android` → Rust/hf-xet baut nicht auf Termux → Modell-Download per wget
- ❌ `Makefile build replaced by CMake` → Build-System auf CMake umgestellt
- ❌ Petals auf Android → Nicht möglich, nur llama.cpp

#### Windows

Windows-Unterstützung ist in Arbeit. Für Petals verwende WSL2.

### 4. OpenCode-Integration

Der Koordinator unterstützt OpenAI-kompatible Endpunkte und kann direkt mit OpenCode genutzt werden.

#### Option A: Projekt-Konfiguration

Kopiere die Beispielkonfiguration in dein Projekt:
```bash
cp opencode.json.example /dein/projekt/opencode.json
```

#### Option B: Globale Konfiguration

Erstelle `~/.config/opencode/opencode.json`:
```json
{
    "$schema": "https://opencode.ai/config.json",
    "provider": {
        "ki-lastverteilung": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "KI-Lastverteilung (lokal)",
            "options": {
                "baseURL": "http://127.0.0.1:5000/v1"
            },
            "models": {
                "ki-lastverteilung-auto": {
                    "name": "KI-Lastverteilung (Auto)",
                    "limit": { "context": 16000, "output": 4096 }
                }
            }
        }
    }
}
```

#### Nutzung

```bash
# Koordinator muss laufen
python3 scripts/koordinator.py &

# OpenCode im Projekt starten
cd /dein/projekt
opencode

# Oder direkt mit Modell
opencode --model ki-lastverteilung/ki-lastverteilung-auto
```

Im TUI: `/models` → Wähle `KI-Lastverteilung (Auto)`.

**Hinweis:** Der `/connect`-Befehl ist nicht nötig – der Koordinator benötigt keine API-Keys für den lokalen Zugriff.

### 5. Anfragen senden

```bash
# Über Koordinator (empfohlen)
python3 scripts/llama_client.py "Wie funktioniert KI?"

# Direkt via API
curl -X POST http://<koordinator-ip>:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Was ist Petals?", "max_tokens": 128}'

# OpenAI-kompatibel (für OpenCode, ChatGPT-Clients etc.)
curl -X POST http://<koordinator-ip>:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hallo!"}]}'
```

### 6. Monitoring

```bash
bash scripts/monitor.sh
```

Zeigt in Echtzeit: Worker-Status, CPU/RAM pro Node, aktueller Modus (Petals/llama.cpp), Anfrage-Statistik.

## Architektur

### Modus-Erkennung

Der Koordinator prüft alle 5 Sekunden automatisch:

| Kriterium | Schwellwert |
|-----------|-------------|
| Petals installiert | Auf ≥2 Nodes |
| Netzwerk-Latenz | < 20ms (Ping) |
| Hardware-Ähnlichkeit | RAM-Faktor ≤ 1.5 |

**Petals-Modus:** Modell-Layer werden auf Nodes partitioniert (z.B. Node A: Layer 0-11, Node B: Layer 12-23)

**llama.cpp-Modus:** Jeder Worker hat ein vollständiges Modell. Auswahl nach Score:
```
Score = Latenz × 0.3 + CPU% × 0.4 + RAM% × 0.3
```
Niedrigster Score gewinnt.

### Auto-Installation

Wenn ≥2 Nodes mit SSH-Zugang und ≥4 GB RAM gefunden werden:
1. `virtualenv` + `petals` automatisch installiert
2. Petals-Server mit Layer-Partitionierung gestartet
3. Latenz zwischen Nodes geprüft
4. Bei Erfolg: Switch zu Petals-Modus

## Voraussetzungen

- **Python 3.8+**, `nmap` (`sudo apt install nmap`), `sshpass`
- **SSH-Zugang** zu allen Worker-Nodes
- **Gleiches LAN** (alle Geräte im selben Subnetz)

## Sicherheit

- **Keine hardcoded Credentials** – Passwörter in `credentials.json`
- **`.gitignore`** schützt sensible Daten vor dem Einchecken
- **Berechtigung `600`** für credentials.json (nur Besitzer lesbar)

## Release-Änderungen

### v3.1 – Termux/Android-Installer korrigiert

**Fixes:**
- ❌ `hf-xet` Rust-Build-Fehler auf Termux → Modell-Download per `wget` statt `hf` CLI
- ❌ `Makefile replaced by CMake` → llama.cpp Build auf CMake umgestellt
- ❌ Android unterstützt kein Petals → Installer auf llama.cpp-only umgestellt
- ❌ Verwirrende Namensgebung "petals" bei Termux-Skripten → Umbenennung zu `install_worker_*.sh`
- ✅ Koordinator startet nun mit `python3` (System-Python) statt `petals-env`

### v3.0 – Intelligente Lastverteilung mit Auto-Erkennung

**Neu:**
- **Koordinator** (`koordinator.py`) mit FastAPI-Server auf Port 5000
- **Auto-Detect** Petals vs llama.cpp basierend auf Netzwerk-Latenz, Hardware und Verfügbarkeit
- **Auto-Installation** von Petals auf kompatiblen Nodes im Netzwerk
- **Score-basierte Worker-Auswahl** (Latenz + CPU + RAM) statt Round-Robin
- **Anfrage-Statistik** im Monitor: Anfragen pro Worker, Latenz, CPU/RAM
- **Credential-System** mit `credentials.json` – keine Passwörter im Repository
- **Monitor** zeigt aktuellen Modus (🌸 Petals / ⚙ llama.cpp) mit Begründung an

**Entwicklungshintergrund:**
Das Tool begann als einfaches Round-Robin-Setup mit zwei llama.cpp-Workern. Im Laufe der Entwicklung zeigten sich folgende Erkenntnisse:
- Die manuelle Konfiguration von Workern war fehleranfällig → **Auto-Erkennung via nmap**
- Round-Robin berücksichtigt nicht die aktuelle Auslastung → **Score-basierte Auswahl**
- Für große Modelle (>16 GB) ist eine einzelne Maschine limitiert → **Petals-Integration**
- Hardcodierte Passwörter sind ein Sicherheitsrisiko → **Credential-Datei mit .gitignore**
- Die Anzeige der CPU-Auslastung war unlesbar (`top`-Felder) → **CPU% und RAM%**
- Flackernder Monitor stört → **htop-Style mit Cursor-Positionierung**

Das System ist nun so designed, dass es bei der Arbeit mit vielen ähnlichen Maschinen automatisch das Optimum wählt: Petals für große Modelle auf leistungsfähigen Nodes mit niedriger Latenz, llama.cpp für alles andere.

### v2.0 – Petals-Integration
- Petals-Worker-Installer für Linux, Termux, Windows
- Netzwerk-basierte Worker-Erkennung
- htop-Style Monitor (flackerfrei)

### v1.0 – Grundlegende Lastverteilung
- Round-Robin-Verteilung über llama.cpp-Worker
- Einfacher Chat-Client
- Manuelles Worker-Setup
