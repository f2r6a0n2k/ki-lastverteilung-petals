# Android Worker installieren

## Voraussetzungen
- **Termux** aus F-Droid oder GitHub (**nicht** Play Store)
- ~3 GB freier Speicher
- Mindestens 2 GB RAM
- WLAN-Verbindung

## 1. Installation

In Termux eingeben:

```bash
curl -o install.sh \
  https://raw.githubusercontent.com/f2r6a0n2k/ki-lastverteilung-petals/main/scripts/install_petals_worker_termux.sh

bash install.sh 8080
```

Das Skript:
- Installiert Build-Tools (`git`, `make`, `clang`)
- Kompiliert llama.cpp aus dem Quellcode
- Lädt das Llama-3.2-3B-Modell herunter (~2 GB)
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
  https://raw.githubusercontent.com/f2r6a0n2k/ki-lastverteilung-petals/main/scripts/uninstall_petals_worker_termux.sh

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
| `make: command not found` | `pkg install make clang` |
| `hf: command not found` | `pip install huggingface-hub` |
| `curl: (7) Failed to connect` | Firewall prüfen, Port 8080 freischalten |
| Modell-Download abbricht | WLAN-Verbindung prüfen, Skript erneut starten |
| Worker startet nicht | `tail -20 ~/llama-worker-8080.log` für Fehlerdetails |
