#!/usr/bin/env python3
"""
Koordinator für KI-Lastverteilung mit auto-detect: Petals vs llama.cpp
FastAPI + uvicorn, startet auf Port 5000

Auto-Installationslogik:
  1. Scannt Netzwerk nach erreichbaren Nodes (SSH + HTTP-Ports)
  2. Installiert Petals automatisch auf Nodes mit SSH-Zugang
  3. Startet Petals-Server mit Layer-Partitionierung
  4. Prüft: >=2 Nodes, Latenz <20ms, RAM ähnlich
  5. Wenn erfüllt -> Petals-Modus, sonst -> llama.cpp-Fallback
"""

import json
import os
import re
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

STATS_FILE = Path("/tmp/llama_stats.json")
MODE_FILE = Path("/tmp/llama_mode.json")
INSTALL_LOCK = Path("/tmp/llama_install.lock")
CONFIG_FILE = Path("/home/frank/Dokumente/KI_Lastverteilung_Petals/scripts/nodes.json")
SCRIPT_DIR = Path("/home/frank/Dokumente/KI_Lastverteilung_Petals/scripts")

LOCAL_IP = subprocess.check_output(["hostname", "-I"], text=True).strip().split()[0]
LOCAL_SUBNET = ".".join(LOCAL_IP.split(".")[:3])

app = FastAPI(title="KI-Lastverteilung Koordinator")

state = {
    "session_start": datetime.now().isoformat(),
    "mode": "llama.cpp",
    "mode_reason": "Prüfung läuft...",
    "workers": {},
    "petals_nodes": [],
    "total_requests": 0,
    "install_status": {},
}
state_lock = threading.Lock()

MODEL_NAME = "bigscience/bloom-560m"


def load_config():
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "default_user": "user",
        "default_pass": "cornholio",
        "nodes": {}
    }


def get_creds(ip):
    config = load_config()
    node_creds = config.get("nodes", {}).get(ip, {})
    return node_creds.get("user", config.get("default_user", "user")), \
           node_creds.get("pass", config.get("default_pass", "cornholio"))


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
    status = state["install_status"].get(ip, {})
    status["phase"] = "starting"
    state["install_status"][ip] = status
    save_stats()

    def do_install():
        try:
            state["install_status"][ip]["phase"] = "checking_python"
            ok, out, _ = ssh_exec(ip, "python3 --version && which python3")
            if not ok:
                state["install_status"][ip] = {"phase": "failed", "error": "Python3 nicht gefunden"}
                save_stats()
                return False

            state["install_status"][ip]["phase"] = "installing_virtualevn"
            ssh_exec(ip, "pip3 install --user --break-system-packages virtualenv 2>/dev/null || true", timeout=60)

            state["install_status"][ip]["phase"] = "creating_venv"
            ssh_exec(ip, "mkdir -p ~/petals_env && rm -rf ~/petals_env/*")
            ok, _, _ = ssh_exec(ip, "~/.local/bin/virtualenv ~/petals_env 2>/dev/null || python3 -m venv ~/petals_env")
            if not ok:
                state["install_status"][ip]["phase"] = "installing_setuptools"
                ssh_exec(ip, "echo 'setuptools>=69,<70' > /tmp/requirements.txt && pip3 install --break-system-packages 'setuptools>=69,<70' 2>/dev/null || true", timeout=60)
                ok, _, _ = ssh_exec(ip, "python3 -m venv ~/petals_env")
                if not ok:
                    state["install_status"][ip] = {"phase": "failed", "error": "venv creation failed"}
                    save_stats()
                    return False

            state["install_status"][ip]["phase"] = "installing_petals"
            cmd = ". ~/petals_env/bin/activate && pip install --upgrade pip setuptools wheel && " \
                  f"pip install petals && python3 -c \"import petals; print(petals.__version__)\""
            ok, out, err = ssh_exec(ip, cmd, timeout=600)

            if ok:
                state["install_status"][ip] = {"phase": "installed", "version": out.split("\n")[-1]}
                save_stats()
                return True
            else:
                state["install_status"][ip] = {"phase": "failed", "error": err[:200]}
                save_stats()
                return False
        except Exception as e:
            state["install_status"][ip] = {"phase": "failed", "error": str(e)}
            save_stats()
            return False

    t = threading.Thread(target=do_install, daemon=True)
    t.start()
    return True


def ssh_start_petals_server(ip, layer_start, layer_end):
    user, pwd = get_creds(ip)
    cmd = f". ~/petals_env/bin/activate && " \
          f"nohup python3 -m petals.cli.run_server {MODEL_NAME} " \
          f"--num_layers {layer_start}-{layer_end} " \
          f"--host 0.0.0.0 --port 8080 > /tmp/petals_server.log 2>&1 & " \
          f"echo $!"
    ok, pid, _ = ssh_exec(ip, cmd, timeout=10)
    return ok, pid


def discover_nodes():
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


def evaluate_petals_mode():
    if not INSTALL_LOCK.exists():
        return False, "Keine Petals-Nodes installiert"

    nodes = []
    try:
        with open(INSTALL_LOCK) as f:
            nodes = json.load(f)
    except Exception:
        return False, "Install-Lock leer"

    if len(nodes) < 2:
        return False, f"Nur {len(nodes)} Node mit Petals (mind. 2 benötigt)"

    for n in nodes:
        ok, _, _ = ssh_exec(n["ip"], "python3 -c 'import petals'")
        if not ok:
            return False, f"Petals auf {n['ip']} nicht importierbar"

    for i, n1 in enumerate(nodes):
        for n2 in nodes[i+1:]:
            lat = measure_latency(n1["ip"], n2["ip"])
            if lat > 20:
                return False, f"Latenz {n1['ip']}<->{n2['ip']}: {lat:.1f}ms > 20ms"

    rams = [n.get("ram_kb") for n in nodes if n.get("ram_kb")]
    if len(rams) >= 2:
        if max(rams) > min(rams) * 1.5:
            return False, "Hardware zu unterschiedlich (RAM-Faktor >1.5)"

    state["petals_nodes"] = nodes
    return True, f"Petals aktiv: {len(nodes)} Nodes ({', '.join(n['ip'] for n in nodes)})"


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

        total_layers = 24
        layers_per_node = total_layers // len(eligible)
        installed_nodes = []

        for i, node in enumerate(eligible):
            layer_start = i * layers_per_node
            layer_end = (i + 1) * layers_per_node - 1
            if i == len(eligible) - 1:
                layer_end = total_layers - 1

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
                    ok, pid = ssh_start_petals_server(node["ip"], layer_start, layer_end)
                    if ok:
                        installed_nodes.append({**node, "pid": pid, "layers": f"{layer_start}-{layer_end}"})
                    break
                time.sleep(5)
                waited += 5

        if len(installed_nodes) >= 2:
            with open(INSTALL_LOCK, "w") as f:
                json.dump(installed_nodes, f, indent=2)
            state["petals_nodes"] = installed_nodes


def health_check_workers():
    workers = []
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

    now = datetime.now().isoformat()
    petals_ok, petals_reason = evaluate_petals_mode()

    with state_lock:
        state["mode"] = "petals" if petals_ok else "llama.cpp"
        state["mode_reason"] = petals_reason

        found = set()
        for w in workers:
            found.add(w)
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
                state["workers"][w] = {"ip": ip, "requests_total": 0, "requests_session": 0, "latencies": [], "healthy": False}

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
            auto_install_loop()
            health_check_workers()
        except Exception:
            pass
        time.sleep(5)


health_thread = threading.Thread(target=run_health_loop, daemon=True)
health_thread.start()


class ChatRequest(BaseModel):
    messages: list = []
    max_tokens: int = 1024
    temperature: float = 0.7


class PromptRequest(BaseModel):
    prompt: str
    max_tokens: int = 1024


@app.get("/health")
def health():
    return {"status": "ok"}


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
        return {"mode": state["mode"], "reason": state["mode_reason"], "petals_nodes": state.get("petals_nodes", [])}


@app.post("/install")
def install(ip: str):
    if ssh_install_petals(ip):
        return {"status": "installation_started"}
    return {"status": "failed"}


def _route_request(messages, max_tokens, temperature):
    mode = state["mode"]

    if mode == "petals":
        try:
            from petals import DistributedLlamaForCausalLM, AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            model = DistributedLlamaForCausalLM.from_pretrained(MODEL_NAME)
            inputs = tokenizer.apply_chat_template(messages, return_tensors="pt")
            outputs = model.generate(inputs, max_new_tokens=max_tokens, temperature=temperature)
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            return {"mode": "petals", "response": response}
        except Exception as e:
            state["mode"] = "llama.cpp"
            state["mode_reason"] = f"Petals-Fallback: {e}"
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
    uvicorn.run(app, host="0.0.0.0", port=5000)
