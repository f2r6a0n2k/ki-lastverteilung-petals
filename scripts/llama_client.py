#!/usr/bin/env python3
"""
Einfacher Client für llama.cpp Lastverteilung (Round-Robin)
Worker werden automatisch via nmap im lokalen Netzwerk erkannt.
Verwendung: python3 scripts/llama_client.py "Deine Frage hier" [--max-tokens ZAHL]
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile

STATE_FILE = os.path.join(tempfile.gettempdir(), "llama_rr_state")


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


def get_next_worker(workers):
    idx = 0
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                idx = int(f.read().strip())
        except (ValueError, IOError):
            idx = 0
    worker = workers[idx % len(workers)]
    with open(STATE_FILE, "w") as f:
        f.write(str((idx + 1) % len(workers)))
    return worker


def main():
    parser = argparse.ArgumentParser(description="llama.cpp Client für KI-Lastverteilung")
    parser.add_argument("prompt", nargs="?", default="Hello!", help="Der Prompt für die KI")
    parser.add_argument("--max-tokens", type=int, default=100, help="Maximale Anzahl Token")
    args = parser.parse_args()

    workers = discover_workers()
    if not workers:
        print("Keine Worker gefunden. Bitte stelle sicher, dass mindestens ein llama-server läuft (Port 8080-8089).")
        sys.exit(1)

    worker = get_next_worker(workers)

    print(f"=== llama.cpp Client ===")
    print(f"Worker: {worker}")
    print(f"Prompt: {args.prompt}")
    print(f"Sende Anfrage...")

    try:
        import requests
        resp = requests.post(
            f"{worker}/completion",
            json={"prompt": args.prompt, "max_tokens": args.max_tokens},
            timeout=30
        )
        result = resp.json()
        print(f"\n=== Antwort ===")
        if "content" in result:
            print(result["content"])
        elif "response" in result:
            print(result["response"])
        else:
            print(result)
    except ImportError:
        print("Fehler: requests nicht installiert. Installiere mit: pip install requests")
        sys.exit(1)
    except Exception as e:
        print(f"Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
