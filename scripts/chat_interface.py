#!/usr/bin/env python3
"""
Chat-Interface für KI-Lastverteilung mit Konversationsverlauf
Worker werden automatisch via nmap erkannt, intelligente Lastverteilung.
Verwendung: python3 scripts/chat_interface.py
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import random

WORKER_METRICS = {}


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


def check_worker_health(worker):
    try:
        start = time.time()
        import requests
        resp = requests.get(f"{worker}/health", timeout=3)
        latency = (time.time() - start) * 1000
        data = resp.json()
        return {
            "healthy": True,
            "latency_ms": latency,
            "status": data.get("status", "unknown"),
            "message": ""
        }
    except Exception as e:
        return {
            "healthy": False,
            "latency_ms": 9999,
            "status": "error",
            "message": str(e)
        }


def select_worker(workers):
    healthy_workers = []
    for w in workers:
        health = check_worker_health(w)
        WORKER_METRICS[w] = health
        if health["healthy"]:
            healthy_workers.append((w, health))

    if not healthy_workers:
        return None

    if len(healthy_workers) == 1:
        return healthy_workers[0][0]

    fastest = min(healthy_workers, key=lambda x: x[1]["latency_ms"])
    fastest_latency = fastest[1]["latency_ms"]

    candidates = [
        (w, h) for w, h in healthy_workers
        if h["latency_ms"] <= fastest_latency * 1.5
    ]

    chosen = random.choice(candidates)[0]
    return chosen


class ChatSession:
    def __init__(self, system_prompt=None):
        self.messages = []
        self.system_prompt = system_prompt or "Du bist ein hilfreicher KI-Assistent. Antworte auf Deutsch, wenn der Nutzer Deutsch verwendet."
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})

    def add_user(self, text):
        self.messages.append({"role": "user", "content": text})

    def add_assistant(self, text):
        self.messages.append({"role": "assistant", "content": text})

    def clear(self):
        self.messages = []
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})

    def set_system(self, text):
        self.system_prompt = text
        self.messages = [m for m in self.messages if m["role"] != "system"]
        self.messages.insert(0, {"role": "system", "content": text})


def send_request(worker, messages, max_tokens):
    import requests
    resp = requests.post(
        f"{worker}/v1/chat/completions",
        json={
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        },
        timeout=120
    )
    result = resp.json()
    return result["choices"][0]["message"]["content"]


BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[1;32m"
RED = "\033[1;31m"
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
RESET = "\033[0m"


def print_banner(workers):
    print(f"{BOLD}{'=' * 50}{RESET}")
    print(f"{BOLD}   KI-Lastverteilung Chat-Interface{RESET}")
    print(f"{DIM}   Intelligente Lastverteilung • {len(workers)} Worker{RESET}")
    print(f"{BOLD}{'=' * 50}{RESET}")
    print()
    print(f"{BLUE}Gefundene Worker:{RESET}")
    for i, w in enumerate(workers, 1):
        print(f"   {GREEN}•{RESET} Worker {i}: {w}")
    print()
    print(f"{YELLOW}Befehle:{RESET}")
    print(f"   {DIM}/help{RESET}       - Diese Hilfe anzeigen")
    print(f"   {DIM}/clear{RESET}      - Konversation zurücksetzen")
    print(f"   {DIM}/workers{RESET}    - Verfügbare Worker zeigen")
    print(f"   {DIM}/status{RESET}     - Worker-Gesundheitsstatus")
    print(f"   {DIM}/system [text]{RESET} - System-Prompt setzen")
    print(f"   {DIM}/history{RESET}    - Nachrichtenanzahl zeigen")
    print(f"   {DIM}/quit{RESET}       - Beenden")
    print()


def print_worker_status():
    if not WORKER_METRICS:
        print(f"{YELLOW}Noch keine Worker-Status verfügbar.{RESET}")
        return
    print(f"{BLUE}Worker-Status:{RESET}")
    for w, h in WORKER_METRICS.items():
        status = f"{GREEN}OK{RESET}" if h["healthy"] else f"{RED}Fehler{RESET}"
        print(f"   {w}: {status} ({h['latency_ms']:.0f}ms)")


def main():
    parser = argparse.ArgumentParser(description="Chat-Interface für KI-Lastverteilung")
    parser.add_argument("--max-tokens", type=int, default=1024, help="Maximale Token pro Antwort")
    parser.add_argument("--system", type=str, default=None, help="System-Prompt")
    args = parser.parse_args()

    workers = discover_workers()
    if not workers:
        print(f"{RED}Keine Worker gefunden. Bitte llama-server auf Port 8080-8089 starten.{RESET}")
        sys.exit(1)

    print_banner(workers)

    session = ChatSession(system_prompt=args.system)

    while True:
        try:
            user_input = input(f"{MAGENTA}Du › {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{YELLOW}Beende...{RESET}")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            parts = user_input.split(None, 1)
            cmd = parts[0].lower()

            if cmd in ("/quit", "/exit"):
                print(f"{YELLOW}Beende...{RESET}")
                break
            elif cmd == "/clear":
                session.clear()
                print(f"{GREEN}Konversation zurückgesetzt.{RESET}")
            elif cmd == "/workers":
                print(f"{BLUE}Verfügbare Worker:{RESET}")
                for i, w in enumerate(workers, 1):
                    print(f"   {GREEN}•{RESET} Worker {i}: {w}")
            elif cmd == "/status":
                print_worker_status()
            elif cmd == "/system":
                if len(parts) > 1:
                    session.set_system(parts[1])
                    print(f"{GREEN}System-Prompt gesetzt.{RESET}")
                else:
                    print(f"{YELLOW}Aktueller System-Prompt: {session.system_prompt}{RESET}")
            elif cmd == "/history":
                count = len([m for m in session.messages if m["role"] != "system"])
                print(f"{BLUE}{count} Nachrichten im Verlauf.{RESET}")
            elif cmd == "/help":
                print(f"{YELLOW}Befehle:{RESET}")
                print(f"   {DIM}/clear{RESET}      - Konversation zurücksetzen")
                print(f"   {DIM}/workers{RESET}    - Verfügbare Worker zeigen")
                print(f"   {DIM}/status{RESET}     - Worker-Gesundheitsstatus")
                print(f"   {DIM}/system [text]{RESET} - System-Prompt setzen")
                print(f"   {DIM}/history{RESET}    - Nachrichtenanzahl zeigen")
                print(f"   {DIM}/quit{RESET}       - Beenden")
            else:
                print(f"{RED}Unbekannter Befehl: {cmd}. Tippe /help für Hilfe.{RESET}")
            continue

        worker = select_worker(workers)
        if not worker:
            print(f"{RED}Kein verfügbarer Worker gefunden!{RESET}")
            continue

        session.add_user(user_input)

        print()
        print(f"{CYAN}Sende an {worker}...{RESET}")

        try:
            start = time.time()
            response = send_request(worker, session.messages, args.max_tokens)
            elapsed = time.time() - start

            session.add_assistant(response)

            print()
            print(f"{GREEN}Assistant{RESET} {DIM}({worker}, {elapsed:.1f}s){RESET}")
            print(f"{DIM}{'─' * 50}{RESET}")
            print(response)
            print(f"{DIM}{'─' * 50}{RESET}")
            print()

        except Exception as e:
            print(f"{RED}Fehler: {e}{RESET}")
            session.messages.pop()

    print(f"{YELLOW}Auf Wiedersehen!{RESET}")


if __name__ == "__main__":
    main()
