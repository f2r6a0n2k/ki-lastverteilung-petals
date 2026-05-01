# Video-Guide: KI-Lastverteilung mit Petals (für NotebookLM)

## Skript für das Video (ca. 10-15 Minuten)

### Einleitung (45 Sek)
"Willkommen zu diesem Tutorial! Heute zeige ich euch, wie ihr ein echtes KI-Netzwerk aufbaut, bei dem einzelne Prompts auf mehrere Rechner verteilt werden. Mit Petals könnt ihr große Sprachmodelle nutzen – verteilt auf eure vorhandene Hardware."

### Schritt 1: Projektverständnis (1.5 Min)
- Zeige `docs/lastverteilung_ki_netzwerk.md`
- Erkläre Petals-Konzept: Modell wird in Schichten aufgeteilt
- Zeige `configs/models.json` – konfigurierbare Modelle
- Vorteil: Ein 7B-Modell läuft auf 2-3 normalen PCs

### Schritt 2: Linux Petals Worker installieren (2 Min)
- Terminal öffnen: `bash scripts/install_petals_worker_linux.sh 8080`
- Erkläre: PyTorch + Petals werden installiert
- Zeige laufenden Worker: `ps aux | grep petals`
- Test: `curl http://localhost:8080/health` (falls verfügbar)

### Schritt 3: Weitere Worker hinzufügen (1.5 Min)
- Windows: `.\scripts\install_petals_worker_windows.ps1 8081`
- Android/Termux: `bash scripts/install_petals_worker_termux.sh 8082`
- Zeige `configs/models.json` – Modell anpassen

### Schritt 4: Modell konfigurieren (1.5 Min)
- Zeige `configs/models.json`
- Erkläre die Modelle:
  - TinyLlama-1.1B (1 Gerät)
  - Llama-2-7B (2-3 Geräte)
  - Llama-2-13B (4+ Geräte)
- Ändere `default_model` in der JSON

### Schritt 5: Client nutzen (2 Min)
- Teste: `python3 scripts/petals_client.py "Hallo, wie geht es dir?"`
- Zeige `--list-models` Option
- Zeige `--modell` Flag für benutzerdefiniertes Modell
- Erkläre: Prompt wird auf alle Worker verteilt!

### Schritt 6: Monitoring (1.5 Min)
- Starte: `bash scripts/monitor_petals.sh`
- Zeige Echtzeit-CPU-Last auf allen Geräten
- Erkläre: Jeder Worker verarbeitet einen Teil des Modells

### Schritt 7: Deinstallation (45 Sek)
- Linux: `bash scripts/uninstall_petals_worker_linux.sh 8080`
- Windows: `.\scripts\uninstall_petals_worker_windows.ps1 8081`
- Termux: `bash scripts/uninstall_petals_worker_termux.sh 8082`

### Abschluss (30 Sek)
"Jetzt habt ihr ein voll funktionsfähiges KI-Netzwerk! Prompts werden auf mehrere Rechner verteilt, ihr könnt große Modelle auf schwächerer Hardware nutzen. Alle Daten bleiben bei euch lokal. Viel Spaß beim Experimentieren!"

## Hinweise für NotebookLM:
- Upload den gesamten Ordner `KI_Lastverteilung_Petals`
- Nutze `video_guide_petals.md` als Hauptquelle
- Füge `configs/models.json` und `docs/lastverteilung_ki_netzwerk.md` als Zusatzquellen hinzu
- Lass dir ein detailliertes Skript mit timestamps generieren
- Benutze die Audio-Option für Voiceover
- Zeige während des Videos die Skripte und Konfigurationsdateien
