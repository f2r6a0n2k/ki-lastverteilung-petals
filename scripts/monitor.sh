#!/bin/bash
# Monitor für KI-Lastverteilung - HTOP-Style (flackerfrei)

GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
RESET="\033[0m"
BOLD="\033[1m"

cleanup() {
    tput rmcup 2>/dev/null
    tput cnorm 2>/dev/null
    exit 0
}
trap cleanup INT TERM

tput smcup 2>/dev/null
tput civis 2>/dev/null

LOCAL_IP=$(hostname -I | awk '{print $1}')
LOCAL_SUBNET=$(echo "$LOCAL_IP" | cut -d. -f1-3)

scan_network() {
    nmap -p 8080-8089 --open -T4 "${LOCAL_SUBNET}.0/24" 2>/dev/null | awk '
        /\([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\)/ {
            match($0, /\(([0-9.]+)\)/, a)
            ip = a[1]
        }
        /^[0-9]+\/tcp.*open/ {
            split($1, p, "/")
            print ip, p[1]
        }
    '
}

w() { printf "\033[2K\033[0G%b\n" "$1"; }

# Initial: bekannte Worker-Liste (persistent über Session)
declare -A known_workers

while true; do
    # Cursor nach oben, KEIN komplettes Löschen
    printf "\033[H"

    # Header
    w "${BOLD}==========================================${RESET}"
    w "${BOLD}   KI-Lastverteilung Monitor${RESET}"
    w "${BOLD}   Zeit: $(date +%T)${RESET}"
    w "${BOLD}==========================================${RESET}"
    w ""

    # Neue Worker finden und zur persistenten Liste hinzufügen
    while read -r ip port; do
        [ -z "$ip" ] && continue
        if [ -z "${known_workers["${ip}:${port}"]}" ]; then
            known_workers["${ip}:${port}"]=1
        fi
    done <<< "$(scan_network)"

    # Alle bekannten Worker anzeigen (auch wenn jetzt offline)
    if [ ${#known_workers[@]} -eq 0 ]; then
        w "${YELLOW}Keine Worker gefunden – Scan läuft...${RESET}"
    fi

    for key in "${!known_workers[@]}"; do
        IFS=':' read -r ip port <<< "$key"

        if curl -s --connect-timeout 0.5 "http://${ip}:${port}/health" >/dev/null 2>&1; then
            if [ "$ip" = "$LOCAL_IP" ] || [ "$ip" = "127.0.0.1" ]; then
                CPU=$(top -b -n1 2>/dev/null | grep '^%Cpu')
            else
                CPU=$(ssh -o StrictHostKeyChecking=no -o ConnectTimeout=1 "${ip}" "top -b -n1 2>/dev/null | grep '^%Cpu'" 2>/dev/null)
            fi

            w "${BLUE}📍 ${ip}:${port}${RESET}"
            w "   Status: ${GREEN}✅ AKTIV${RESET}"
            if [ -n "$CPU" ]; then
                w "   ${BLUE}CPU-Last:${RESET} $CPU"
            else
                w "   ${YELLOW}CPU-Last: ${RED}✘ Nicht messbar${RESET}"
            fi
        else
            w "${BLUE}📍 ${ip}:${port}${RESET}"
            w "   Status: ${RED}❌ INAKTIV${RESET}"
        fi
        w ""
    done

    # Koordinator
    w "${BLUE}📊 Koordinator (Round-Robin)${RESET}"
    if ps aux 2>/dev/null | grep -q "[u]vicorn koordinator"; then
        w "   Status: ${GREEN}✅ AKTIV${RESET}"
    else
        w "   Status: ${RED}❌ INAKTIV${RESET}"
    fi
    w ""
    w "${YELLOW}Drücke Ctrl+C zum Beenden${RESET}"

    # Restliche Zeilen leeren
    printf "\033[J"

    sleep 2
done
