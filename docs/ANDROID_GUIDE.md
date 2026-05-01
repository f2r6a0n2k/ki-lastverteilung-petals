# Android Worker installieren

> **Hinweis:** Android unterstützt KEIN Petals. Dieser Guide nutzt ausschließlich **llama.cpp**.

## Voraussetzungen
- **Termux** aus F-Droid oder GitHub (**nicht** Play Store)
- ~3 GB freier Speicher
- Mindestens 2 GB RAM
- WLAN-Verbindung

## 1. Installation

In Termux eingeben:

```bash
curl -o install.sh \
  https://raw.githubusercontent.com/f2r6a0n2k/ki-lastverteilung-petals/main/scripts/install_worker_termux.sh

bash install.sh 8080
```

Das Skript:
- Installiert Build-Tools (`git`, `cmake`, `clang`, `wget`) via `pkg`
- Kompiliert llama.cpp mit **CMake** (Makefile wurde ersetzt)
- Lädt das Llama-3.2-3B-Modell per **wget** direkt von HuggingFace (~2 GB)
- Erstellt die Skripte `start_worker.sh`, `stop_worker.sh`, `worker_status.sh`
- Startet den Worker automatisch

**Dauer:** 10-30 Minuten je nach Gerät und Internet.

## 2. Worker starten / stoppen

```bash
bash ~/start_worker.sh 8080    # Starten
bash ~/stop_worker.sh 8080     # Stoppen
bash ~/worker_status.sh 8080   # Status prüfen
```

## 3. Worker im Hintergrund laufen lassen

Damit der Worker auch bei geschlossenem Termux weiterläuft, muss Wake Lock aktiviert werden:

1. In Termux von links nach rechts wischen → Termux:Widget wird angezeigt
2. Oder: Benachrichtigung antippen → "Acquire wakelock"

Alternativ im Termux-Terminal:
```bash
termux-wake-lock
```

## 4. Deinstallation

```bash
curl -o uninstall.sh \
  https://raw.githubusercontent.com/f2r6a0n2k/ki-lastverteilung-petals/main/scripts/uninstall_worker_termux.sh

bash uninstall.sh 8080
```

Um llama.cpp und Modell komplett zu entfernen:
```bash
pkill -f llama-server
rm -rf ~/llama.cpp
rm -f ~/start_worker.sh ~/stop_worker.sh ~/worker_status.sh
rm -f ~/llama-worker-*.log
```

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| `cmake: command not found` | `pkg install cmake` |
| `wget: command not found` | `pkg install wget` |
| `curl: (7) Failed to connect` | Firewall prüfen, Port 8080 freischalten |
| Modell-Download abbricht | WLAN-Verbindung prüfen, `wget --continue` nutzt teilgeladene Dateien |
| Worker startet nicht | `tail -20 ~/llama-worker-8080.log` für Fehlerdetails |
| `Makefile:6: Build system changed` | Nicht mehr relevant – Installer nutzt jetzt CMake |
| `hf-xet` / `maturin` Build-Fehler | Nicht mehr relevant – Modell-Download per `wget` statt `hf` CLI |
