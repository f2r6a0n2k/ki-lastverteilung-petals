#!/usr/bin/env python3
"""
Einfacher Client für KI-Lastverteilung
Verwendet den Koordinator (Port 5000) für intelligente Lastverteilung.
Fallback: Direkte Worker-Auswahl wenn Koordinator nicht verfügbar.
Verwendung: python3 scripts/llama_client.py "Deine Frage hier" [--max-tokens ZAHL]
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

from datetime import datetime

STATS_FILE = "/tmp/llama_requests.json"
KOORDINATOR = "http://127.0.0.1:5000"


def log_request(worker, prompt, latency_ms):
    try:
        data = {"worker": worker, "prompt": prompt[:50], "latency_ms": round(latency_ms, 1), "time": datetime.now().isoformat()}
        stats = {"session_total": 0, "per_worker": {}, "last_requests": []}
        if Path(STATS_FILE).exists():
            with open(STATS_FILE) as f:
                stats = json.load(f)
        stats["session_total"] = stats.get("session_total", 0) + 1
        worker_key = worker.split("//")[1].split(":")[0] if "//" in worker else worker
        stats["per_worker"][worker_key] = stats["per_worker"].get(worker_key, 0) + 1
        stats["last_requests"].append(data)
        if len(stats["last_requests"]) > 10:
            stats["last_requests"] = stats["last_requests"][-10:]
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception:
        pass


def discover_workers():
    local_ip = subprocess.check_output(
        ["hostname", "-I"], text=True
    ).strip().split()[0]
    subnet = ".".join(local_ip.split(".")[:3]) + ".0/24"

    result = subprocess.run(
        ["nmap", "-p", "8080-8089", "--open", "-T4", subnet],
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
            port = port_match.group(1)
            workers.append(f"http://{current_ip}:{port}")

    return sorted(set(workers))


def select_worker(workers):
    healthy = []
    for w in workers:
        try:
            import requests
            start = time.time()
            resp = requests.get(f"{w}/health", timeout=3)
            latency = (time.time() - start) * 1000
            if resp.status_code == 200:
                healthy.append((w, latency))
        except:
            pass

    if not healthy:
        return None

    if len(healthy) == 1:
        return healthy[0][0]

    fastest = min(healthy, key=lambda x: x[1])[1]
    candidates = [w for w, lat in healthy if lat <= fastest * 1.5]
    return random.choice(candidates)


def main():
    import requests

    parser = argparse.ArgumentParser(description="llama.cpp Client für KI-Lastverteilung")
    parser.add_argument("prompt", nargs="?", default="Hello!", help="Der Prompt für die KI")
    parser.add_argument("--max-tokens", type=int, default=1024, help="Maximale Anzahl Token")
    args = parser.parse_args()

    # Versuche zuerst den Koordinator
    try:
        resp = requests.post(
            f"{KOORDINATOR}/ask",
            json={"prompt": args.prompt, "max_tokens": args.max_tokens},
            timeout=180,
        )
        result = resp.json()
        worker = result["worker"]
        response = result["response"]

        print(f"=== llama.cpp Client (Koordinator) ===")
        print(f"Worker: {worker}")
        print(f"Prompt: {args.prompt}")
        print(f"\n=== Antwort ===")
        print(response)
        log_request(worker, args.prompt, 0)
        return
    except Exception:
        pass

    # Fallback: Direkte Worker-Auswahl
    workers = discover_workers()
    if not workers:
        print("Keine Worker gefunden. Bitte stelle sicher, dass mindestens ein llama-server läuft (Port 8080-8089).")
        sys.exit(1)

    worker = select_worker(workers)
    if not worker:
        print("Kein verfügbarer Worker gefunden!")
        sys.exit(1)

    print(f"=== llama.cpp Client (direkt) ===")
    print(f"Worker: {worker}")
    print(f"Prompt: {args.prompt}")
    print(f"Sende Anfrage...")

    try:
        start = time.time()
        resp = requests.post(
            f"{worker}/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": args.prompt}],
                "max_tokens": args.max_tokens,
                "temperature": 0.7
            },
            timeout=120
        )
        latency = (time.time() - start) * 1000
        result = resp.json()
        print(f"\n=== Antwort ===")
        print(result["choices"][0]["message"]["content"])
        log_request(worker, args.prompt, latency)
    except Exception as e:
        print(f"Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
