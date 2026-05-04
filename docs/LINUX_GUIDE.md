# Linux Worker installieren

## Voraussetzungen
- Ubuntu 20.04+, Debian 11+, oder vergleichbar
- ~3 GB freier Speicher
- Mindestens 2 GB RAM (4 GB empfohlen)
- `sudo`-Rechte für Firewall-Konfiguration
- **Hinweis:** NVIDIA-GPU empfohlen, CPU-only ist langsamer aber funktional

## Option A: llama.cpp Worker (empfohlen)

Dies ist die zuverlässigste Methode – funktioniert mit allen Clients im Projekt.

### 1. Abhängigkeiten installieren

```bash
sudo apt update
sudo apt install -y git build-essential cmake curl nmap
```

### 2. llama.cpp herunterladen und kompilieren

```bash
cd ~
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
cmake -B build
cmake --build build --config Release -j$(nproc)
```

### 3. Modell herunterladen

```bash
pip install --user huggingface-hub
mkdir -p models
hf download bartowski/Llama-3.2-3B-Instruct-GGUF \
  --include "Llama-3.2-3B-Instruct-Q4_K_M.gguf" \
  --local-dir models/
```

### 4. Worker starten

```bash
./build/bin/llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 1024 \
  --port 8080 \
  --host 0.0.0.0 \
  -t $(nproc)
```

Oder im Hintergrund:
```bash
nohup ./build/bin/llama-server \
  -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -c 1024 --port 8080 --host 0.0.0.0 -t $(nproc) \
  > ~/llama-worker.log 2>&1 &
```

### 5. Firewall öffnen

```bash
sudo ufw allow 8080/tcp
```

### 6. Status prüfen

```bash
curl http://localhost:8080/health
```

Sollte `{"status":"ok"}` zurückgeben.

### Automatisiert (mit Projekt-Skript)

```bash
bash scripts/install_worker_linux.sh 8080
```

**Hinweis:** Dieses Skript installiert Petals mit PyTorch. Für manuelles llama.cpp-Setup nutze Option A oben.

---

## Option B: Petals Worker

Petals-Worker bieten echte Lastverteilung (Modell-Schichten auf verschiedene Rechner), sind aber komplexer einzurichten und erfordern eine kompatible Python-Version (< 3.12).

### 1. Python-Version prüfen

```bash
python3 --version
```

Petals benötigt Python **< 3.12** (Python 3.10 oder 3.11). Falls Python 3.12+ installiert ist:

**Methode A: deadsnakes PPA (empfohlen, am einfachsten)**

```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Virtuelle Umgebung mit Python 3.11 erstellen
python3.11 -m venv ~/petals-env
source ~/petals-env/bin/activate

# Prüfen
python3 --version  # Sollte 3.11.x anzeigen
```

**Methode B: pyenv (Alternative)**

```bash
curl https://pyenv.run | bash

# Shell konfigurieren (~/.bashrc hinzufügen):
cat >> ~/.bashrc << 'PYENV_EOF'
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
PYENV_EOF

# Shell neu laden
source ~/.bashrc

# Python 3.11 installieren
pyenv install 3.11.8
pyenv global 3.11.8
```

> **Wichtig:** Nach der Installation stelle sicher, dass `python3 --version` **3.11.x** anzeigt, bevor du mit Schritt 2 fortfährst.

### 2. PyTorch installieren

**Wichtig:** Petals benötigt eine ältere PyTorch-Version (< 2.2) für Kompatibilität mit `hivemind`.

**Mit NVIDIA GPU:**
```bash
pip install 'torch>=2.0,<2.2' 'torchvision>=0.15,<0.17' 'torchaudio>=2.0,<2.2' --index-url https://download.pytorch.org/whl/cu121
```

**CPU-only (langsamer):**
```bash
pip install 'torch>=2.0,<2.2' 'torchvision>=0.15,<0.17' 'torchaudio>=2.0,<2.2' --index-url https://download.pytorch.org/whl/cpu
```

### 3. Petals installieren

```bash
# setuptools zuerst installieren (für hivemind Build)
pip install setuptools

# Petals mit allen Abhängigkeiten
pip install petals

# Fehlende Abhängigkeiten explizit installieren
pip install async-timeout bitsandbytes cpufeature Dijkstar humanfriendly
```

> **Falls `hivemind` Build fehlschlägt** (`ModuleNotFoundError: No module named 'pkg_resources'`):
> ```bash
> pip install --no-build-isolation hivemind==1.1.10.post2
> ```

### 4. Worker starten

```bash
python3 -m petals.cli.run_server \
  meta-llama/Meta-Llama-3.1-8B-Instruct \
  --port 31330 \
  --public_name "My-Worker"
```

**Wichtig:** Petals-Worker nutzen Port **31330** (nicht 8080-8089) und sind **nicht direkt** mit den llama.cpp-Clients kompatibel. Sie benötigen einen Petals-Koordinator.

### 5. Firewall öffnen

```bash
sudo ufw allow 31330/tcp
```

---

## Worker als System-Dienst (llama.cpp)

Damit der Worker automatisch beim Booten startet:

```bash
sudo tee /etc/systemd/system/llama-worker.service << 'EOF'
[Unit]
Description=llama.cpp Worker
After=network.target

[Service]
Type=simple
User=frank
WorkingDirectory=/home/frank/llama.cpp
ExecStart=/home/frank/llama.cpp/build/bin/llama-server -m /home/frank/llama.cpp/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf -c 1024 --port 8080 --host 0.0.0.0 -t 4
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable llama-worker
sudo systemctl start llama-worker
```

Status prüfen:
```bash
sudo systemctl status llama-worker
```

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| `cmake: command not found` | `sudo apt install cmake` |
| `hf: command not found` | `pip install --user huggingface-hub` |
| `ufw: command not found` | `sudo apt install ufw` und `sudo ufw enable` |
| Modell-Download zu langsam | WLAN/Kabel prüfen, mirror wechseln |
| Worker antwortet nicht | `tail -f ~/llama-worker.log` für Fehlerdetails |
| Port 8080 belegt | Anderen Port wählen: `--port 8082` |
