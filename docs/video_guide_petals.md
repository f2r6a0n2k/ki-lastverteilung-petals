# Video-Guide: KI-Lastverteilung (für NotebookLM)

## Skript für das Video (ca. 10-15 Minuten)

### Einleitung (45 Sek)
"Willkommen zu diesem Tutorial! Heute zeige ich euch, wie ihr ein echtes KI-Netzwerk aufbaut, bei dem Anfragen automatisch auf mehrere Rechner verteilt werden. Das System erkennt eure Hardware und wählt optimal zwischen Petals (verteilte Modell-Partitionierung) und llama.cpp (parallele Worker)."

### Schritt 1: Projektverständnis (1.5 Min)
- Zeige `README.md` – Architektur-Übersicht
- Erkläre zwei Modi:
  - **Petals**: Modell-Schichten auf verschiedene PCs verteilt (≥2 Nodes, gute Latenz)
  - **llama.cpp**: Jeder Node hat ein vollständiges Modell, Auswahl nach Score (Latenz + CPU + RAM)
- Vorteil: Automatisch optimiert für eure Hardware

### Schritt 2: Linux Worker installieren (2 Min)
- Terminal öffnen: `bash scripts/install_worker_linux.sh 8080`
- Erkläre: PyTorch + Petals werden installiert
- Zeige laufenden Worker: `ps aux | grep petals`
- Test: `curl http://localhost:8080/health`

### Schritt 3: Weitere Worker hinzufügen (1.5 Min)
- **Windows**: `.\scripts\install_worker_windows.ps1 8081` (Petals, siehe `docs/WINDOWS_GUIDE.md`)
- **Android/Termux**: `bash scripts/install_worker_termux.sh 8082` (nur llama.cpp – Petals auf Android nicht möglich)
- Erkläre: Android-Termux nutzt llama.cpp mit CMake, Modell-Download per wget

### Schritt 4: Koordinator starten (1.5 Min)
- `python3 scripts/koordinator.py &`
- Erkläre: Koordinator scannt Netzwerk, erkennt Nodes, wählt automatisch Petals oder llama.cpp
- **Wichtig:** `python3` (System-Python) verwenden, NICHT `petals-env`

### Schritt 5: Anfragen senden (2 Min)
- CLI: `python3 scripts/llama_client.py "Hallo, wie geht es dir?"`
- API: `curl -X POST http://127.0.0.1:5000/v1/chat/completions -H "Content-Type: application/json" -d '{"messages": [{"role": "user", "content": "Hallo!"}]}'`
- OpenCode: `opencode --model ki-lastverteilung/ki-lastverteilung-auto`

### Schritt 6: Monitoring (1.5 Min)
- Starte: `bash scripts/monitor.sh`
- Zeige Echtzeit-CPU/RAM-Last auf allen Geräten
- Zeige aktuellen Modus (Petals oder llama.cpp) mit Begründung

### Schritt 7: Deinstallation (45 Sek)
- Linux: `bash scripts/uninstall_worker_linux.sh 8080`
- Windows: `.\scripts\uninstall_worker_windows.ps1 8081`
- Termux: `bash scripts/uninstall_worker_termux.sh 8082`

### Abschluss (30 Sek)
"Jetzt habt ihr ein voll funktionsfähiges KI-Netzwerk! Anfragen werden automatisch auf mehrere Rechner verteilt – mit Petals für große Modelle auf starken Nodes, oder llama.cpp für alles andere. Alle Daten bleiben lokal. Viel Spaß beim Experimentieren!"

## Hinweise für NotebookLM:
- Upload den gesamten Ordner `KI_Lastverteilung_Petals`
- Nutze `video_guide_petals.md` als Hauptquelle
- Füge `docs/LINUX_GUIDE.md`, `docs/ANDROID_GUIDE.md`, `docs/WINDOWS_GUIDE.md` als Zusatzquellen hinzu
- Lass dir ein detailliertes Skript mit timestamps generieren
- Benutze die Audio-Option für Voiceover
- Zeige während des Videos die Skripte und Konfigurationsdateien
