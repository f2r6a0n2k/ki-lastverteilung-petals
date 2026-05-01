#!/usr/bin/env python3
"""
Koordinator für KI-Lastverteilung mit intelligenter Worker-Auswahl
FastAPI + uvicorn, startet auf Port 5000
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
LOCAL_IP = subprocess.check_output(["hostname", "-I"], text=True).strip().split()[0]
LOCAL_SUBNET = ".".join(LOCAL_IP.split(".")[:3])
SSH_PASS = "cornholio"

app = FastAPI(title="KI-Lastverteilung Koordinator")

state = {
    "session_start": datetime.now().isoformat(),
    "workers": {},
    "total_requests": 0,
}
state_lock = threading.Lock()


def load_stats():
    global state
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE) as f:
                state = json.load(f)
        except Exception:
            pass


def save_stats():
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def discover_workers():
    result = subprocess.run(
        ["nmap", "-p", "8080-8089", "--open", "-T4", f"{LOCAL_SUBNET}.0/24"],
        capture_output=True, text=True, timeout=60
    )
    workers = []
    current_ip = None
    ip_pattern = re.compile(r"\((\d+\.\d+\.\d+\.\d+)\)")
    port_pattern = re.compile(r"^(\d{4,5})/tcp\s+open")
    for line in result.stdout.splitlines():
        ip_match = ip_pattern.search(line)
        if ip_match:
            current_ip = ip_match.group(1)
        port_match = port_pattern.match(line.strip())
        if port_match and current_ip:
            workers.append(f"http://{current_ip}:{port_match.group(1)}")
    return sorted(set(workers))


def get_remote_stats(ip):
    try:
        cmd = (
            f"sshpass -p {SSH_PASS} ssh -o StrictHostKeyChecking=no "
            f"-o ConnectTimeout=1 user@{ip} "
            "\"idle=$(top -b -n1 2>/dev/null | grep '^%%Cpu' | grep -oP '[0-9,]+(?=\\s*id)' | tr ',' '.'); "
            "idle=${idle:-100}; idle=${idle%%.*}; "
            "cpu=$((100-idle)); [ $cpu -lt 0 ] && cpu=0; "
            "ram=$(free | awk '/^Mem:/{printf \"%.0f\",$3/$2*100}'); "
            "echo \\\"$cpu $ram\\\"\""
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        parts = result.stdout.strip().split()
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except Exception:
        pass
    return None, None


def get_local_stats():
    try:
        line = subprocess.run(
            "top -b -n1 | grep '^%Cpu'", shell=True, capture_output=True, text=True, timeout=5
        ).stdout.strip()
        idle_match = re.search(r'([0-9,]+)\s*id', line)
        if idle_match:
            idle = float(idle_match.group(1).replace(',', '.'))
            cpu = max(0, int(100 - idle))
        else:
            cpu = 0
        ram_line = subprocess.run(
            "free | awk '/^Mem:/{printf \"%.0f\",$3/$2*100}'", shell=True,
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
        ram = int(ram_line) if ram_line.isdigit() else 0
        return cpu, ram
    except Exception:
        return None, None


def health_check_workers():
    workers = discover_workers()
    now = datetime.now().isoformat()

    with state_lock:
        known = set(state["workers"].keys())
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
            if ip == LOCAL_IP or ip == "127.0.0.1":
                cpu, ram = get_local_stats()
            else:
                cpu, ram = get_remote_stats(ip)

            if w not in state["workers"]:
                state["workers"][w] = {
                    "ip": ip,
                    "requests_total": 0,
                    "requests_session": 0,
                    "latencies": [],
                    "healthy": False,
                }

            entry = state["workers"][w]
            entry["healthy"] = healthy
            entry["latency_ms"] = round(latency, 1)
            entry["latencies"].append(latency)
            if len(entry["latencies"]) > 10:
                entry["latencies"] = entry["latencies"][-10:]
            entry["avg_latency_ms"] = round(sum(entry["latencies"]) / len(entry["latencies"]), 1)
            entry["cpu_percent"] = cpu
            entry["ram_percent"] = ram
            entry["last_check"] = now

        for old in known - found:
            if old in state["workers"]:
                state["workers"][old]["healthy"] = False
                state["workers"][old]["latency_ms"] = 9999

        save_stats()


def select_best_worker():
    with state_lock:
        candidates = []
        for w, info in state["workers"].items():
            if not info.get("healthy", False):
                continue
            latency = info.get("avg_latency_ms", 9999)
            cpu = info.get("cpu_percent", 100)
            ram = info.get("ram_percent", 100)
            score = (latency / 100) * 0.3 + cpu * 0.4 + ram * 0.3
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


def run_health_loop():
    while True:
        try:
            health_check_workers()
        except Exception:
            pass
        time.sleep(5)


health_thread = threading.Thread(target=run_health_loop, daemon=True)
health_thread.start()
load_stats()


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


@app.post("/chat")
def chat(req: ChatRequest):
    worker = select_best_worker()
    if not worker:
        raise HTTPException(status_code=503, detail="Kein Worker verfügbar")

    try:
        resp = requests.post(
            f"{worker}/v1/chat/completions",
            json={
                "messages": req.messages,
                "max_tokens": req.max_tokens,
                "temperature": req.temperature,
            },
            timeout=180,
        )
        result = resp.json()
        return {
            "worker": worker,
            "response": result["choices"][0]["message"]["content"],
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/ask")
def ask(req: PromptRequest):
    worker = select_best_worker()
    if not worker:
        raise HTTPException(status_code=503, detail="Kein Worker verfügbar")

    try:
        resp = requests.post(
            f"{worker}/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": req.prompt}],
                "max_tokens": req.max_tokens,
                "temperature": 0.7,
            },
            timeout=180,
        )
        result = resp.json()
        return {
            "worker": worker,
            "response": result["choices"][0]["message"]["content"],
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
