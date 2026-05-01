#!/usr/bin/env python3
"""
Einfacher Client für llama.cpp Lastverteilung (Round-Robin)
Verwendung: python3 scripts/llama_client.py "Deine Frage hier" [--max-tokens ZAHL]
"""

import argparse
import json
import sys
import itertools

# Verfügbare Worker (Round-Robin)
WORKERS = [
    "http://192.168.178.105:8080",  # Elitebook
    "http://192.168.178.109:8081"   # Lokal
]
worker_cycle = itertools.cycle(WORKERS)

def main():
    parser = argparse.ArgumentParser(description='llama.cpp Client für KI-Lastverteilung')
    parser.add_argument('prompt', nargs='?', default='Hello!', help='Der Prompt für die KI')
    parser.add_argument('--max-tokens', type=int, default=100, help='Maximale Anzahl Token')
    args = parser.parse_args()

    worker = next(worker_cycle)
    
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
        # Verschiedene mögliche Antwortformate behandeln
        if 'content' in result:
            print(result['content'])
        elif 'response' in result:
            print(result['response'])
        else:
            print(result)
    except ImportError:
        print("❌ requests nicht installiert. Installiere mit: pip install requests")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
