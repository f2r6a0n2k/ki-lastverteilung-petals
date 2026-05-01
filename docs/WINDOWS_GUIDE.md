# Windows Worker installieren

## Voraussetzungen
- Windows 10/11 (64-bit)
- ~3 GB freier Speicher
- Mindestens 2 GB RAM (4 GB empfohlen)
- **NVIDIA-GPU empfohlen** – CPU-only ist deutlich langsamer
- PowerShell mit Administrator-Rechten

---

## Option A: llama.cpp Worker (empfohlen)

### 1. Build-Tools installieren

**Möglichkeit 1 – Vorab kompilierte Binärdateien (am einfachsten):**
1. Lade die neueste llama.cpp Release herunter: https://github.com/ggerganov/llama.cpp/releases
2. Wähle die Windows-Version mit CUDA (falls NVIDIA GPU vorhanden) oder CPU-only
3. Entpacke nach `C:\llama.cpp`

**Möglichkeit 2 – Selbst kompilieren (für Fortgeschrittene):**
1. Visual Studio Build Tools installieren: https://visualstudio.microsoft.com/downloads/
   - "C++ CMake tools for Windows" und "MSVC Build Tools" auswählen
2. CMake installieren: https://cmake.org/download/
3. Git installieren: https://git-scm.com/download/win
4. Kompilieren:
   ```powershell
   cd C:\
   git clone https://github.com/ggerganov/llama.cpp.git
   cd llama.cpp
   cmake -B build
   cmake --build build --config Release -j 8
   ```

### 2. Modell herunterladen

PowerShell (als normaler Benutzer):
```powershell
pip install huggingface-hub
mkdir -p models

# Modell herunterladen (~2 GB)
hf download bartowski/Llama-3.2-3B-Instruct-GGUF `
  --include "Llama-3.2-3B-Instruct-Q4_K_M.gguf" `
  --local-dir models/
```

Alternativ direkt im Browser: https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/tree/main
→ `Llama-3.2-3B-Instruct-Q4_K_M.gguf` herunterladen und in den `models/` Ordner verschieben.

### 3. Worker starten

**Mit CUDA (NVIDIA GPU):**
```powershell
cd C:\llama.cpp
.\build\bin\llama-server.exe `
  -m models\Llama-3.2-3B-Instruct-Q4_K_M.gguf `
  -c 1024 --port 8080 --host 0.0.0.0 -ngl 35
```
`-ngl 35` lädt 35 Layer auf die GPU. Bei weniger VRAM reduzieren.

**CPU-only:**
```powershell
cd C:\llama.cpp
.\build\bin\llama-server.exe `
  -m models\Llama-3.2-3B-Instruct-Q4_K_M.gguf `
  -c 1024 --port 8080 --host 0.0.0.0 -t 4
```
`-t 4` = Anzahl CPU-Kerne. Anpassen an das System.

### 4. Firewall öffnen

PowerShell **als Administrator**:
```powershell
New-NetFirewallRule -DisplayName "llama.cpp Worker" `
  -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
```

### 5. Status prüfen

```powershell
curl http://localhost:8080/health
```

Oder im Browser: `http://localhost:8080`

---

## Option B: Petals Worker

### 1. Python installieren

1. Python 3.11 herunterladen: https://www.python.org/downloads/release/python-3119/
2. **Wichtig:** Bei Installation "Add Python to PATH" anhaken
3. Python 3.12+ ist mit Petals **nicht kompatibel**

### 2. PyTorch installieren

**Mit NVIDIA GPU:**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**CPU-only:**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 3. Petals installieren

```powershell
pip install petals
```

### 4. Worker starten

```powershell
python -m petals.cli.run_server `
  meta-llama/Meta-Llama-3.1-8B-Instruct `
  --port 31330 `
  --public_name "Windows-Worker"
```

### 5. Firewall öffnen

```powershell
New-NetFirewallRule -DisplayName "Petals Worker" `
  -Direction Inbound -LocalPort 31330 -Protocol TCP -Action Allow
```

---

## Worker als Windows-Dienst (llama.cpp)

Damit der Worker automatisch startet:

1. Batch-Datei erstellen (`C:\llama.cpp\start_worker.bat`):
   ```batch
   @echo off
   cd /d C:\llama.cpp
   .\build\bin\llama-server.exe ^
     -m models\Llama-3.2-3B-Instruct-Q4_K_M.gguf ^
     -c 1024 --port 8080 --host 0.0.0.0 -ngl 35
   ```

2. Als geplante Aufgabe einrichten:
   - Taskplaner öffnen (`taskschd.msc`)
   - "Aufgabe erstellen" → Allgemein: "llama.cpp Worker"
   - "Unabhängig von Benutzeranmeldung ausführen" anhaken
   - Trigger: "Bei Systemstart"
   - Aktion: Programm `C:\llama.cpp\start_worker.bat`
   - Einstellungen: "Aufgabe bei Fehler neu starten" → 3 Versuche

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| `python: command not found` | Python nicht in PATH – Neuinstallation mit PATH-Option |
| `pip install` blockiert | `py -m pip install ...` statt `pip install` |
| CUDA nicht gefunden | NVIDIA-Treiber aktualisieren, `nvcc --version` prüfen |
| `llama-server.exe` startet nicht | Visual Studio Redistributable installieren: https://aka.ms/vs/17/release/vc_redist.x64.exe |
| Firewall blockiert | Windows Defender Firewall → Eingehende Regeln → Port 8080 freigeben |
| Worker antwortet nicht | `type llama-worker.log` im CMD für Fehlerdetails |
| VRAM zu klein | `-ngl` reduzieren (z.B. `-ngl 20` statt 35) |
