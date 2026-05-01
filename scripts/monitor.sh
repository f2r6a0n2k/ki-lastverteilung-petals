#!/bin/bash
# Monitor für KI-Lastverteilung - HTOP-Style (flackerfrei, schnell)

GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
RESET="\033[0m"
BOLD="\033[1m"

cleanup() { tput rmcup 2>/dev/null; tput cnorm 2>/dev/null; exit 0; }
trap cleanup INT TERM
tput smcup 2>/dev/null
tput civis 2>/dev/null

LOCAL_IP=$(hostname -I | awk '{print $1}')
LOCAL_SUBNET=$(echo "$LOCAL_IP" | cut -d. -f1-3)

scan_network() {
    nmap -p 8080-8089 --open -T4 "${LOCAL_SUBNET}.0/24" 2>/dev/null | awk '
        /\([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\)/ { match($0,/\(([0-9.]+)\)/,a); ip=a[1] }
        /^[0-9]+\/tcp.*open/ { split($1,p,"/"); print ip, p[1] }
    '
}

# Schnelle lokale CPU aus /proc/stat (kein top!)
local_stats() {
    local u i t pct m
    read -r _ u _ _ i _ _ _ _ _ < /proc/stat
    t=$((u + i))
    pct=$((u * 100 / (t > 0 ? t : 1)))
    m=$(free | awk '/^Mem:/{printf "%.0f", $3/$2*100}')
    echo "$pct $m"
}

w() { printf "\033[2K\033[0G%b\n" "$1"; }

declare -A known_workers
SCAN_EVERY=5
cycle=0

while true; do
    cycle=$((cycle + 1))

    # Worker-Scan nur alle N Zyklen
    if [ $((cycle % SCAN_EVERY)) -eq 1 ]; then
        while read -r ip port; do
            [ -z "$ip" ] && continue
            known_workers["${ip}:${port}"]=1
        done <<< "$(scan_network)"
    fi

    # Header
    printf "\033[H"
    w "${BOLD}==========================================${RESET}"
    w "${BOLD}   KI-Lastverteilung Monitor${RESET}"
    w "${BOLD}   Zeit: $(date +%T)${RESET}"
    w "${BOLD}==========================================${RESET}"
    w ""

    [ ${#known_workers[@]} -eq 0 ] && w "${YELLOW}Keine Worker gefunden – Scan läuft...${RESET}"

    for key in "${!known_workers[@]}"; do
        IFS=':' read -r ip port <<< "$key"

        w "${BLUE}📍 ${ip}:${port}${RESET}"

        if curl -s --connect-timeout 0.3 "http://${ip}:${port}/health" >/dev/null 2>&1; then
            w "   Status: ${GREEN}✅ AKTIV${RESET}"

            if [ "$ip" = "$LOCAL_IP" ] || [ "$ip" = "127.0.0.1" ]; then
                read -r cpu ram <<< "$(local_stats)"
                w "   ${BLUE}CPU:${RESET} ${cpu}%  ${BLUE}RAM:${RESET} ${ram}%"
            else
                stats=$(timeout 2 sshpass -p "cornholio" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=1 "user@${ip}" \
                    'read -r _ u _ _ i _ _ _ _ _ < /proc/stat; t=$((u+i)); p=$((u*100/(t>0?t:1))); m=$(free | awk "/^Mem:/{printf \"%.0f\",\$3/\$2*100}"); echo "$p $m"' 2>/dev/null)
                if [ -n "$stats" ]; then
                    read -r cpu ram <<< "$stats"
                    w "   ${BLUE}CPU:${RESET} ${cpu}%  ${BLUE}RAM:${RESET} ${ram}%"
                else
                    w "   ${YELLOW}CPU: ${RED}✘ Nicht messbar${RESET}"
                fi
            fi
        else
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

    printf "\033[J"
    sleep 2
done
