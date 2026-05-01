# Release Notes - v1.0.0

## Änderungen

### Android/Termux Support
- **Petals → llama.cpp:** Android-Worker nutzen jetzt llama.cpp statt Petals
- **Grund:** Petals/PyTorch sind auf Android/Termux nicht kompatibel (keine ARM-Wheels, fehlende System-Bibliotheken)
- **Neu:** Vollautomatische Installation – Skript kompiliert llama.cpp, lädt Modell herunter, startet Worker
- **Neu:** `uninstall_petals_worker_termux.sh` für saubere Deinstallation

### Linux & Windows
- **Unverändert:** Petals-basierte Installation bleibt bestehen
- Petals funktioniert auf Desktop-Systemen mit Python < 3.12 und kompatibler PyTorch-Version

### Clients & Interface
- `chat_interface.py`: Chat-Interface mit Konversationsverlauf und intelligenter Worker-Auswahl
- `llama_client.py`: Einzelne Prompts mit automatischer Worker-Erkennung
- Worker-Erkennung via `nmap` (Ports 8080-8089)
- Intelligente Lastverteilung: Health-Checks + Latenz-basierte Auswahl

## Android-Installation

Auf dem Android-Gerät in Termux:
```bash
bash install_petals_worker_termux.sh 8080
```

Oder manuell:
```bash
pkg install git make clang
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make -j$(nproc)
hf download bartowski/Llama-3.2-3B-Instruct-GGUF --include "Llama-3.2-3B-Instruct-Q4_K_M.gguf" --local-dir models/
./build/bin/llama-server -m models/Llama-3.2-3B-Instruct-Q4_K_M.gguf -c 1024 --port 8080 --host 0.0.0.0 -t $(nproc)
```

## Voraussetzungen

| System | Voraussetzung |
|--------|--------------|
| Android (Termux) | ~3 GB Speicher, 2 GB RAM |
| Linux | Python < 3.12 für Petals, llama.cpp für manuelle Worker |
| Windows | Python < 3.12 für Petals, PowerShell als Administrator |
| Client | Python 3.8+, `requests`, `nmap` |
