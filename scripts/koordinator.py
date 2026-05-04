#!/usr/bin/env python3
"""
Koordinator für KI-Lastverteilung - API Gateway mit Petals + llama.cpp Unterstützung

Betriebsmodi:
  1. Petals Gateway: Verbindet sich mit dem öffentlichen oder privaten Petals-Swarm
     und nutzt verteilte Inferenz über alle verfügbaren Worker.
  2. llama.cpp Load Balancer: Verteilt Anfragen an lokale llama.cpp Worker (Port 8080-8089).

Petals-Worker koordinieren sich SELBST über das DHT-Swarm-System.
Der Koordinator ist das Frontend/API-Gateway für Clients.

Start:
  python3 scripts/koordinator.py              # llama.cpp Modus
  python3 scripts/koordinator.py --petals     # Petals Gateway Modus
  python3 scripts/koordinator.py --petals --private-swarm  # Privater Swarm
"""

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

STATS_FILE = Path("/tmp/llama_stats.json")
MODE_FILE = Path("/tmp/llama_mode.json")
INSTALL_LOCK = Path("/tmp/llama_install.lock")
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
CREDENTIALS_FILE = PROJECT_DIR / "credentials.json"
CONFIG_FILE = SCRIPT_DIR / "nodes.json"

LOCAL_IP = subprocess.check_output(["hostname", "-I"], text=True).strip().split()[0]
LOCAL_SUBNET = ".".join(LOCAL_IP.split(".")[:3])

# === Petals-Modus Konfiguration ===
PETALS_MODEL = os.environ.get("PETALS_MODEL", "bigscience/bloom-petals")
PETALS_TOKEN = os.environ.get("PETALS_TOKEN", None)

# Öffentliche Petals Bootstrap-Server
PUBLIC_INITIAL_PEERS = [
    "/dns/bootstrap1.petals.dev/tcp/31337/p2p/QmedTaZXmULqwspJXz44SsPZyTNKxhnnFvYRajfH7MGhCY",
    "/dns/bootstrap2.petals.dev/tcp/31338/p2p/QmQGTqmM7NKjV6ggU1ZCap8zWiyKR89RViDXiqehSiCpY5",
]

# === Globale Variablen für Petals-Client ===
_petals_client = {
    "model": None,
    "tokenizer": None,
    "initializing": False,
    "initialized": False,
    "error": None,
    "lock": threading.Lock(),
}

app = FastAPI(title="KI-Lastverteilung Koordinator")

state = {
    "session_start": datetime.now().isoformat(),
    "mode": "llama.cpp",
    "mode_reason": "Prüfung läuft...",
    "workers": {},
    "petals_nodes": [],
    "petals_swarm_connected": False,
    "total_requests": 0,
    "install_status": {},
}
state_lock = threading.Lock()

# CLI Argumente
parser = argparse.ArgumentParser(description="KI-Lastverteilung Koordinator")
parser.add_argument("--petals", action="store_true", help="Petals Gateway Modus aktivieren")
parser.add_argument("--private-swarm", action="store_true", help="Privaten Swarm betreiben (kein public)")
parser.add_argument("--port", type=int, default=5000, help="API Port (default: 5000)")
parser.add_argument("--model", type=str, default=None, help="Petals Modell (default: bigscience/bloom-petals)")
parser.add_argument("--token", type=str, default=None, help="Hugging Face Token für gated models")
args = parser.parse_args()

if args.model:
    PETALS_MODEL = args.model
if args.token:
    PETALS_TOKEN = args.token


def load_config():
    config = {
        "default_user": "user",
        "default_pass": "",
        "nodes": {}
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config["nodes"] = json.load(f).get("nodes", {})
        except Exception:
            pass

    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE) as f:
                creds = json.load(f)
                config["default_user"] = creds.get("default_user", config["default_user"])
                config["default_pass"] = creds.get("default_pass", config["default_pass"])
                config["nodes"].update(creds.get("nodes", {}))
        except Exception:
            print(f"WARNING: Could not load {CREDENTIALS_FILE}. SSH access will fail.")

    return config


def get_creds(ip):
    config = load_config()
    node_creds = config.get("nodes", {}).get(ip, {})
    return node_creds.get("user", config.get("default_user", "user")), \
           node_creds.get("pass", config.get("default_pass", ""))


def ssh_exec(ip, cmd, timeout=30):
    user, pwd = get_creds(ip)
    try:
        r = subprocess.run(
            f'sshpass -p "{pwd}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 '
            f'{user}@{ip} "{cmd}"',
            shell=True, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def ssh_install_petals(ip):
    user, pwd = get_creds(ip)
    install_script_url = "https://raw.githubusercontent.com/f2r6a0n2k/ki-lastverteilung-petals/main/scripts/install_petals_worker.sh"

    status = state["install_status"].get(ip, {})
    status["phase"] = "starting"
    state["install_status"][ip] = status
    save_stats()

    def do_install():
        try:
            state["install_status"][ip]["phase"] = "checking_python"
            save_stats()

            ok, out, _ = ssh_exec(ip, "python3.11 --version 2>/dev/null || python3 --version")
            if not ok:
                state["install_status"][ip] = {"phase": "failed", "error": "Python3 nicht gefunden"}
                save_stats()
                return False

            state["install_status"][ip]["phase"] = "downloading_installer"
            save_stats()
            ssh_exec(ip, f"curl -sL {install_script_url} -o /tmp/install_petals.sh || wget -q {install_script_url} -O /tmp/install_petals.sh", timeout=30)

            state["install_status"][ip]["phase"] = "installing_petals"
            save_stats()
            ok, out, err = ssh_exec(ip, "bash /tmp/install_petals.sh 2>&1 | tail -5", timeout=600)

            if ok:
                state["install_status"][ip] = {"phase": "installed", "detail": out[:200] if out else ""}
                save_stats()
                return True
            else:
                state["install_status"][ip] = {"phase": "failed", "error": err[:300] if err else out[:300]}
                save_stats()
                return False
        except Exception as e:
            state["install_status"][ip] = {"phase": "failed", "error": str(e)}
            save_stats()
            return False

    t = threading.Thread(target=do_install, daemon=True)
    t.start()
    return True


def ssh_start_petals_worker(ip, public_name=None):
    user, pwd = get_creds(ip)
    name = public_name or f"Worker-{ip}"
    cmd = f". ~/petals-env/bin/activate && " \
          f"nohup python -m petals.cli.run_server {PETALS_MODEL} " \
          f"--port 31330 --public_name '{name}' " \
          f"> /tmp/petals_server.log 2>&1 & echo $!"
    ok, pid, _ = ssh_exec(ip, cmd, timeout=10)
    return ok, pid


def discover_nodes():
    try:
        result = subprocess.run(
            ["nmap", "-sn", "-T4", f"{LOCAL_SUBNET}.0/24"],
            capture_output=True, text=True, timeout=60
        )
        ips = []
        for line in result.stdout.splitlines():
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
            if match:
                ip = match.group(1)
                if ip != LOCAL_IP:
                    ips.append(ip)
        return ips
    except Exception:
        return []


def test_ssh_access(ip):
    user, pwd = get_creds(ip)
    try:
        r = subprocess.run(
            f'sshpass -p "{pwd}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 '
            f'{user}@{ip} "echo ok"',
            shell=True, capture_output=True, text=True, timeout=10
        )
        return r.returncode == 0
    except Exception:
        return False


def measure_latency(ip1, ip2):
    try:
        if ip2 == LOCAL_IP or ip2 == "127.0.0.1":
            r = subprocess.run(f"ping {ip2} -c 3", shell=True, capture_output=True, text=True, timeout=10)
            match = re.search(r'rtt min/avg/max/mdev = [0-9.]+/([0-9.]+)/', r.stdout)
            if match:
                return float(match.group(1))
        else:
            user, pwd = get_creds(ip2)
            r = subprocess.run(
                f'sshpass -p "{pwd}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 '
                f'{user}@{ip2} "ping {ip1} -c 3 2>/dev/null" | grep rtt | awk -F/ \'{{print $5}}\'',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if r.stdout.strip():
                return float(r.stdout.strip())
    except Exception:
        pass
    return 999


def get_node_ram(ip):
    try:
        ok, out, _ = ssh_exec(ip, "free | awk '/^Mem:/{print $2}'")
        if ok and out.strip().isdigit():
            return int(out.strip())
    except Exception:
        pass
    return None


def init_petals_client():
    """Initialisiert den Petals-Client (Lazy Loading, thread-safe)"""
    if _petals_client["initialized"] or _petals_client["initializing"]:
        return _petals_client["initialized"]

    with _petals_client["lock"]:
        if _petals_client["initialized"] or _petals_client["initializing"]:
            return _petals_client["initialized"]

        _petals_client["initializing"] = True

        try:
            print(f"[Koordinator] Petals Client: Lade '{PETALS_MODEL}'...")
            state["mode"] = "petals"
            state["mode_reason"] = f"Initialisiere {PETALS_MODEL}..."
            save_stats()

            from petals import DistributedLlamaForCausalLM
            from transformers import AutoTokenizer

            load_kwargs = {}
            if PETALS_TOKEN:
                load_kwargs["token"] = PETALS_TOKEN

            if args.private_swarm:
                load_kwargs["initial_peers"] = [f"/ip4/{LOCAL_IP}/tcp/31330/p2p/*"]
                print(f"[Koordinator] Privater Swarm Modus: initial_peers = {LOCAL_IP}:31330")
            else:
                load_kwargs["initial_peers"] = PUBLIC_INITIAL_PEERS
                print(f"[Koordinator] Verbind mit öffentlichem Petals-Swarm")

            print(f"[Koordinator] Lade Tokenizer...")
            _petals_client["tokenizer"] = AutoTokenizer.from_pretrained(PETALS_MODEL, **load_kwargs)
            print(f"[Koordinator] Lade Modell (kann mehrere Minuten dauern)...")
            _petals_client["model"] = DistributedLlamaForCausalLM.from_pretrained(PETALS_MODEL, **load_kwargs)

            _petals_client["initialized"] = True
            _petals_client["error"] = None
            state["mode"] = "petals"
            state["mode_reason"] = f"Verbunden mit Petals-Swarm ({PETALS_MODEL})"
            state["petals_swarm_connected"] = True
            save_stats()
            print(f"[Koordinator] Petals Client bereit!")
            return True

        except Exception as e:
            error_msg = str(e)[:500]
            _petals_client["error"] = error_msg
            _petals_client["initializing"] = False
            state["mode"] = "llama.cpp"
            state["mode_reason"] = f"Petals-Fehler: {error_msg[:200]}"
            state["petals_swarm_connected"] = False
            save_stats()
            print(f"[Koordinator] Petals Client Fehler: {error_msg}")
            return False


def evaluate_petals_mode():
    """Prüft ob Petals-Modus verfügbar ist"""
    if not args.petals:
        return False, "Petals-Modus nicht aktiviert (starte mit --petals)"

    if _petals_client["initialized"]:
        return True, f"Petals aktiv: {PETALS_MODEL}"

    if _petals_client["initializing"]:
        return False, "Petals initialisiert noch..."

    if _petals_client["error"]:
        return False, f"Petals-Fehler: {_petals_client['error'][:100]}"

    return False, "Petals Client noch nicht initialisiert"


def auto_install_loop():
    if INSTALL_LOCK.exists():
        return

    state["install_status"] = {"phase": "scanning"}
    save_stats()

    nodes = discover_nodes()
    eligible = []

    for ip in nodes:
        if test_ssh_access(ip):
            ram = get_node_ram(ip)
            if ram and ram > 4000000:
                eligible.append({"ip": ip, "ram_kb": ram})
            state["install_status"][ip] = {"phase": "ssh_ok", "ram_kb": ram}

    save_stats()

    if len(eligible) >= 2:
        state["install_status"] = {"phase": "installing"}
        save_stats()

        installed_nodes = []

        for i, node in enumerate(eligible):
            ssh_install_petals(node["ip"])
            time.sleep(2)

            state["install_status"][node["ip"]]["phase"] = "waiting_install"
            save_stats()

            max_wait = 600
            waited = 0
            while waited < max_wait:
                with state_lock:
                    status = state["install_status"].get(node["ip"], {})
                if status.get("phase") == "installed":
                    name = f"Node-{i+1}"
                    ok, pid = ssh_start_petals_worker(node["ip"], name)
                    if ok:
                        installed_nodes.append({**node, "pid": pid, "name": name})
                    break
                time.sleep(5)
                waited += 5

        if len(installed_nodes) >= 2:
            with open(INSTALL_LOCK, "w") as f:
                json.dump(installed_nodes, f, indent=2)
            state["petals_nodes"] = installed_nodes


def health_check_workers():
    """Scannt das Netzwerk nach llama.cpp Workern"""
    workers = []
    try:
        result = subprocess.run(
            ["nmap", "-p", "8080-8089", "--open", "-T4", f"{LOCAL_SUBNET}.0/24"],
            capture_output=True, text=True, timeout=60
        )
        current_ip = None
        for line in result.stdout.splitlines():
            ip_match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)', line)
            if ip_match:
                current_ip = ip_match.group(1)
            port_match = re.match(r'^(\d{4,5})/tcp\s+open', line.strip())
            if port_match and current_ip:
                workers.append(f"http://{current_ip}:{port_match.group(1)}")
    except Exception:
        pass

    now = datetime.now().isoformat()
    petals_ok, petals_reason = evaluate_petals_mode()

    with state_lock:
        if petals_ok:
            state["mode"] = "petals"
            state["mode_reason"] = petals_reason
        else:
            state["mode"] = "llama.cpp"
            state["mode_reason"] = petals_reason

        for w in workers:
            try:
                start = time.time()
                resp = requests.get(f"{w}/health", timeout=3)
                latency = (time.time() - start) * 1000
                healthy = resp.status_code == 200
            except Exception:
                latency = 9999
                healthy = False

            ip = w.split("//")[1].split(":")[0]
            if w not in state["workers"]:
                state["workers"][w] = {
                    "ip": ip, "requests_total": 0, "requests_session": 0,
                    "latencies": [], "healthy": False
                }

            entry = state["workers"][w]
            entry["healthy"] = healthy
            entry["latency_ms"] = round(latency, 1)
            entry["latencies"].append(latency)
            if len(entry["latencies"]) > 10:
                entry["latencies"] = entry["latencies"][-10:]
            entry["avg_latency_ms"] = round(sum(entry["latencies"]) / len(entry["latencies"]), 1)
            entry["last_check"] = now


def select_best_worker():
    with state_lock:
        candidates = []
        for w, info in state["workers"].items():
            if not info.get("healthy", False):
                continue
            latency = info.get("avg_latency_ms", 9999)
            score = latency * 0.3 + info.get("cpu_percent", 50) * 0.4 + info.get("ram_percent", 50) * 0.3
            candidates.append((w, score, info))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1])
        best = candidates[0]
        state["total_requests"] += 1
        best[2]["requests_total"] += 1
        best[2]["requests_session"] += 1
        save_stats()
        return best[0]


def save_stats():
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(state, f, indent=2)
        with open(MODE_FILE, "w") as f:
            json.dump({"mode": state["mode"], "reason": state["mode_reason"]}, f)
    except Exception:
        pass


def run_health_loop():
    while True:
        try:
            if args.petals and not _petals_client["initialized"]:
                init_petals_client()
            auto_install_loop()
            health_check_workers()
        except Exception:
            pass
        time.sleep(5)


health_thread = threading.Thread(target=run_health_loop, daemon=True)
health_thread.start()


# === Request-Modelle ===

class ChatRequest(BaseModel):
    messages: list = []
    max_tokens: int = 1024
    temperature: float = 0.7


class PromptRequest(BaseModel):
    prompt: str
    max_tokens: int = 1024


class OpenAIChatRequest(BaseModel):
    messages: list = []
    model: str = "ki-lastverteilung-auto"
    max_tokens: int = 1024
    temperature: float = 0.7
    stream: bool = False


# === API Endpunkte ===

@app.get("/health")
def health():
    return {"status": "ok", "mode": state["mode"], "petals": _petals_client["initialized"]}


@app.get("/v1/models")
def list_models():
    with state_lock:
        models = []
        for w, info in state["workers"].items():
            ip = info.get("ip", w)
            models.append({
                "id": f"ki-lastverteilung-{ip.replace('.', '-')}",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "ki-lastverteilung",
            })
        if state["mode"] == "petals":
            models.insert(0, {
                "id": PETALS_MODEL,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "petals",
            })
        if not models:
            models.append({
                "id": "ki-lastverteilung-auto",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "ki-lastverteilung",
            })
        return {"object": "list", "data": models}


def _run_petals_inference(messages, max_tokens, temperature):
    """Führt Inferenz über Petals-Swarm aus"""
    if not _petals_client["initialized"]:
        if not _petals_client["initializing"]:
            init_petals_client()
        if not _petals_client["initialized"]:
            raise RuntimeError(f"Petals nicht bereit: {_petals_client.get('error', 'initialisiert noch...')}")

    with _petals_client["lock"]:
        tokenizer = _petals_client["tokenizer"]
        model = _petals_client["model"]

        inputs = tokenizer.apply_chat_template(messages, return_tensors="pt", add_generation_prompt=True)
        outputs = model.generate(inputs, max_new_tokens=max_tokens, temperature=temperature)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Prompt aus der Response entfernen
    prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    if response.startswith(prompt_text):
        response = response[len(prompt_text):]

    return response.strip()


@app.post("/v1/chat/completions")
def openai_chat(req: OpenAIChatRequest):
    petals_ok, _ = evaluate_petals_mode()

    # Versuch: Petals-Swarm
    if petals_ok:
        try:
            response = _run_petals_inference(req.messages, req.max_tokens, req.temperature)
            if req.stream:
                return _stream_response(response, mode="petals")
            return _completion_response(response, mode="petals")
        except Exception as e:
            state["mode_reason"] = f"Petals-Fallback: {str(e)[:200]}"
            save_stats()

    # Fallback: llama.cpp Worker
    worker = select_best_worker()
    if not worker:
        raise HTTPException(status_code=503, detail="Kein Worker verfügbar")

    try:
        resp = requests.post(
            f"{worker}/v1/chat/completions",
            json={"messages": req.messages, "max_tokens": req.max_tokens, "temperature": req.temperature},
            timeout=180,
        )
        result = resp.json()
        content = result["choices"][0]["message"]["content"]

        if req.stream:
            return _stream_response(content, mode="llama.cpp", worker=worker)
        return _completion_response(content, mode="llama.cpp", worker=worker)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


def _completion_response(content, mode="llama.cpp", worker=None):
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": PETALS_MODEL if mode == "petals" else "ki-lastverteilung",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
        "metadata": {"mode": mode, "worker": worker},
    }


def _stream_response(content, mode="llama.cpp", worker=None):
    def generate():
        chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        for chunk in content.split(" "):
            data = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": PETALS_MODEL if mode == "petals" else "ki-lastverteilung",
                "choices": [{
                    "index": 0,
                    "delta": {"role": "assistant", "content": chunk + " "},
                    "finish_reason": None,
                }],
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(0.01)
        data = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": PETALS_MODEL if mode == "petals" else "ki-lastverteilung",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(data)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/stats")
def stats():
    with state_lock:
        return dict(state)


@app.get("/workers")
def workers():
    with state_lock:
        return {w: {k: v for k, v in info.items() if k != "latencies"}
                for w, info in state["workers"].items()}


@app.get("/mode")
def mode():
    with state_lock:
        return {
            "mode": state["mode"],
            "reason": state["mode_reason"],
            "petals_model": PETALS_MODEL,
            "petals_swarm": _petals_client["initialized"],
            "petals_nodes": state.get("petals_nodes", []),
        }


@app.post("/install")
def install_node(ip: str):
    if ssh_install_petals(ip):
        return {"status": "installation_started"}
    return {"status": "failed"}


def _route_request(messages, max_tokens, temperature):
    """Interne Routing-Funktion für /chat und /ask Endpunkte"""
    petals_ok, _ = evaluate_petals_mode()

    if petals_ok:
        try:
            response = _run_petals_inference(messages, max_tokens, temperature)
            return {"mode": "petals", "model": PETALS_MODEL, "response": response}
        except Exception as e:
            state["mode_reason"] = f"Petals-Fallback: {str(e)[:200]}"
            save_stats()

    worker = select_best_worker()
    if not worker:
        return None

    try:
        resp = requests.post(
            f"{worker}/v1/chat/completions",
            json={"messages": messages, "max_tokens": max_tokens, "temperature": temperature},
            timeout=180,
        )
        result = resp.json()
        return {"mode": "llama.cpp", "worker": worker, "response": result["choices"][0]["message"]["content"]}
    except Exception:
        return None


@app.post("/chat")
def chat(req: ChatRequest):
    result = _route_request(req.messages, req.max_tokens, req.temperature)
    if not result:
        raise HTTPException(status_code=503, detail="Kein Worker verfügbar")
    return result


@app.post("/ask")
def ask(req: PromptRequest):
    result = _route_request([{"role": "user", "content": req.prompt}], req.max_tokens, 0.7)
    if not result:
        raise HTTPException(status_code=503, detail="Kein Worker verfügbar")
    return result


if __name__ == "__main__":
    print(f"{'='*50}")
    print(f"  KI-Lastverteilung Koordinator")
    print(f"{'='*50}")
    print(f"  Port: {args.port}")
    print(f"  Petals-Modus: {'Ja' if args.petals else 'Nein'}")
    if args.petals:
        print(f"  Modell: {PETALS_MODEL}")
        print(f"  Privater Swarm: {'Ja' if args.private_swarm else 'Nein (public)'}")
        print(f"  HF Token: {'Ja' if PETALS_TOKEN else 'Nein'}")
    print(f"{'='*50}")
    print()

    uvicorn.run(app, host="0.0.0.0", port=args.port)
