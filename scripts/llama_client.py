#!/usr/bin/env python3
"""
Einfacher Client für KI-Lastverteilung
Worker werden automatisch via nmap erkannt, intelligente Lastverteilung.
Verwendung: python3 scripts/llama_client.py "Deine Frage hier" [--max-tokens ZAHL]
"""

import argparse
import os
import random
import re
import subprocess
import sys
import time


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
    parser = argparse.ArgumentParser(description="llama.cpp Client für KI-Lastverteilung")
    parser.add_argument("prompt", nargs="?", default="Hello!", help="Der Prompt für die KI")
    parser.add_argument("--max-tokens", type=int, default=1024, help="Maximale Anzahl Token")
    args = parser.parse_args()

    workers = discover_workers()
    if not workers:
        print("Keine Worker gefunden. Bitte stelle sicher, dass mindestens ein llama-server läuft (Port 8080-8089).")
        sys.exit(1)

    worker = select_worker(workers)
    if not worker:
        print("Kein verfügbarer Worker gefunden!")
        sys.exit(1)

    print(f"=== llama.cpp Client ===")
    print(f"Worker: {worker}")
    print(f"Prompt: {args.prompt}")
    print(f"Sende Anfrage...")

    try:
        import requests
        resp = requests.post(
            f"{worker}/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": args.prompt}],
                "max_tokens": args.max_tokens,
                "temperature": 0.7
            },
            timeout=120
        )
        result = resp.json()
        print(f"\n=== Antwort ===")
        print(result["choices"][0]["message"]["content"])
    except ImportError:
        print("Fehler: requests nicht installiert. Installiere mit: pip install requests")
        sys.exit(1)
    except Exception as e:
        print(f"Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
