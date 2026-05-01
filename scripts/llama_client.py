#!/usr/bin/env python3
"""
Einfacher Client für llama.cpp Lastverteilung (Round-Robin)
Verwendung: python3 scripts/llama_client.py "Deine Frage hier" [--max-tokens ZAHL]
"""

import argparse
import json
import os
import sys
import tempfile

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs", "workers.json")
STATE_FILE = os.path.join(tempfile.gettempdir(), "llama_rr_state")

def load_workers():
    if not os.path.exists(CONFIG_FILE):
        print(f"Fehler: Konfigurationsdatei nicht gefunden: {CONFIG_FILE}")
        sys.exit(1)
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    return [w["url"] for w in config["workers"]]

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

    workers = load_workers()
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
