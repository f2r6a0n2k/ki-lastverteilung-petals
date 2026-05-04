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

**llama.cpp Worker:**
```bash
bash scripts/install_worker_linux.sh 8080
```

**Petals Worker:**
```bash
bash scripts/install_petals_worker.sh        # CPU-only
bash scripts/install_petals_worker.sh cuda   # Mit CUDA
```

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

**Wichtig:** Petals benötigt PyTorch < 2.2 für Kompatibilität mit `hivemind`.

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
# 1. Build-Abhängigkeiten
pip install 'setuptools<69' wheel 'grpcio-tools>=1.70'

# 2. hivemind manuell bauen (wichtig!)
pip install --no-build-isolation hivemind==1.1.10.post2

# 3. Petals ohne Abhängigkeiten
pip install --no-deps petals

# 4. Alle fehlenden Abhängigkeiten installieren
pip install peft==0.5.0 safetensors sentencepiece speedtest-cli==2.1.3 \
  tensor-parallel==1.0.23 tokenizers 'transformers>=4.32.0,<4.35.0' \
  'huggingface-hub>=0.11.1,<1.0' 'accelerate>=0.22.0,<0.25.0' \
  async-timeout bitsandbytes==0.41.1 cpufeature Dijkstar humanfriendly \
  'numpy<2.0'

# 5. setuptools auf normale Version zurücksetzen
pip install --upgrade setuptools
```

> **Hinweis:** Diese Schritte sind notwendig weil `hivemind` 1.1.10.post2 nicht als fertiges Rad verfügbar ist und mit neueren setuptools-Versionen nicht baut.

### 3b. Hugging Face Authentifizierung (für gated models)

Meta-Llama-Modelle erfordern einen **Hugging Face Account** und **Zugriffsfreigabe**:

1. Account erstellen auf https://huggingface.co/signup
2. Zugang beantragen: https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct → "Agree and access repository"
3. Access Token erstellen: https://huggingface.co/settings/tokens → "New token" (Typ: Read)
4. Einloggen:

```bash
huggingface-cli login
# Token eingeben wenn gefragt
```

**Oder** Token direkt beim Start angeben (siehe Schritt 4).

### 4. Worker starten

**Mit GPU (empfohlen):**
```bash
python -m petals.cli.run_server \
  bigscience/bloom-petals \
  --port 31330 \
  --public_name "My-Worker"
```

**CPU-only (langsam, erfordert `--num_blocks`):**
```bash
python -m petals.cli.run_server \
  bigscience/bloom-petals \
  --port 31330 \
  --public_name "My-Worker" \
  --num_blocks 4 \
  --device cpu
```

> **Hinweis:** `--num_blocks` bestimmt, wie viele Modell-Blöcke dieser Worker bedient. Bei CPU: 2-4 Blöcke wählen. BLOOM hat insgesamt 70 Blöcke – mehr Blöcke = höherer RAM-Verbrauch.

Dies startet den Worker mit **BLOOM** (176B Parameter) – kein Token nötig, funktioniert sofort.

**Alternativ: Gated Model (z.B. Llama) mit Token:**
```bash
# Nur für gated models (Meta-Llama etc.):
huggingface-cli login  # einmalig einloggen

python -m petals.cli.run_server \
  meta-llama/Meta-Llama-3.1-8B-Instruct \
  --port 31330 \
  --public_name "My-Worker" \
  --token hf_DEIN_TOKEN_HIER
```

**Wichtig:** Petals-Worker nutzen Port **31330** (nicht 8080-8089) und koordinieren sich **selbst** über das Petals DHT-Swarm-System.

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
User=<benutzername>
WorkingDirectory=/home/<benutzername>/llama.cpp
ExecStart=/home/<benutzername>/llama.cpp/build/bin/llama-server -m /home/<benutzername>/llama.cpp/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf -c 1024 --port 8080 --host 0.0.0.0 -t 4
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
| Port 8080/31330 belegt | Anderen Port wählen: `--port 8082` |
| `401 Unauthorized` / `gated repo` | Hugging Face Token: `huggingface-cli login` oder `--token hf_...` |
| `ModuleNotFoundError: No module named 'petals'` | Virtuelle Umgebung aktivieren: `source ~/petals-env/bin/activate` |
| `hivemind` Build fehler | `pip install 'setuptools<69' wheel && pip install --no-build-isolation hivemind==1.1.10.post2` |
| NumPy API Error | `pip install 'numpy<2.0'` |
| `GPU is not available` / `AssertionError` | CPU: `--num_blocks 4 --device cpu` hinzufügen |

---

## Koordinator (API Gateway)

Der Koordinator ist das **zentrale API-Gateway** für Clients. Er bietet eine OpenAI-kompatible API und leitet Anfragen an Petals-Worker oder llama.cpp-Worker weiter.

> **Wichtig:** Petals-Worker koordinieren sich **selbst** über das DHT-Swarm-System. Der Koordinator ist **kein** Swarm-Controller, sondern ein **Client-Gateway**.

### Architektur

```
Client → Koordinator (:5000) → Petals-Swarm (Worker auf :31330)
                          ↘ llama.cpp Worker (auf :8080-8089)
```

### Koordinator starten

**llama.cpp Modus (Standard):**
```bash
bash scripts/start_koordinator.sh
```

**Petals Gateway Modus (verbindet sich mit öffentlichem Swarm):**
```bash
bash scripts/start_koordinator.sh --petals
```

**Mit Hugging Face Token (für gated models):**
```bash
bash scripts/start_koordinator.sh --petals --token hf_DEIN_TOKEN
```

**Alternativ mit Umgebungsvariablen:**
```bash
export PETALS_MODEL="bigscience/bloom-petals"
export PETALS_TOKEN="hf_xxx"
bash scripts/start_koordinator.sh --petals
```

### API-Endpunkte

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/health` | GET | Health Check |
| `/v1/models` | GET | Verfügbare Modelle auflisten |
| `/v1/chat/completions` | POST | OpenAI-kompatible Chat API |
| `/chat` | POST | Chat mit Messages-Format |
| `/ask` | POST | Einfache Frage-Antwort |
| `/stats` | GET | Worker-Statistiken |
| `/mode` | GET | Aktueller Modus (petals/llama.cpp) |

### Beispiel: Anfrage senden

```bash
curl http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hallo, wer bist du?"}],
    "max_tokens": 100
  }'
```
