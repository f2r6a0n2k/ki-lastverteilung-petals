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

# Credentials laden (aus credentials.json oder nodes.json)
PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
CREDS_FILE="$PROJECT_DIR/credentials.json"
NODES_FILE="$PROJECT_DIR/scripts/nodes.json"

get_pass() {
    local ip=$1
    local def_pass=""
    local def_user="user"
    local node_pass=""
    local node_user=""
    
    # Default aus credentials.json
    if [ -f "$CREDS_FILE" ]; then
        def_pass=$(python3 -c "import json; print(json.load(open('$CREDS_FILE')).get('default_pass',''))" 2>/dev/null)
        def_user=$(python3 -c "import json; print(json.load(open('$CREDS_FILE')).get('default_user','user'))" 2>/dev/null)
    fi
    
    # Node-spezifisch aus nodes.json
    if [ -f "$NODES_FILE" ]; then
        node_user=$(python3 -c "import json; d=json.load(open('$NODES_FILE')); print(d.get('nodes',{}).get('$ip',{}).get('user',''))" 2>/dev/null)
        node_pass=$(python3 -c "import json; d=json.load(open('$NODES_FILE')); print(d.get('nodes',{}).get('$ip',{}).get('pass',''))" 2>/dev/null)
    fi
    
    echo "${node_pass:-$def_pass}"
}

scan_network() {
    nmap -p 8080-8089 --open -T4 "${LOCAL_SUBNET}.0/24" 2>/dev/null | awk '
        /\([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\)/ { match($0,/\(([0-9.]+)\)/,a); ip=a[1] }
        /^[0-9]+\/tcp.*open/ { split($1,p,"/"); print ip, p[1] }
    '
}

# CPU aus top (parse idle-Wert -> 100-idle = Auslastung)
local_stats() {
    local idle=$(top -b -n1 2>/dev/null | grep '^%Cpu' | grep -oP '[0-9,]+(?=\s*id)' | tr ',' '.' | awk '{printf "%.0f", $1}')
    idle=${idle:-100}
    local cpu=$((100 - idle))
    [ $cpu -lt 0 ] && cpu=0
    local ram=$(free | awk '/^Mem:/{printf "%.0f", $3/$2*100}')
    echo "$cpu $ram"
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

        if [ "$ip" = "$LOCAL_IP" ] || [ "$ip" = "127.0.0.1" ]; then
            w "${BLUE}📍 ${ip}:${port} (lokal)${RESET}"
        else
            w "${BLUE}📍 ${ip}:${port}${RESET}"
        fi

        if curl -s --connect-timeout 0.3 "http://${ip}:${port}/health" >/dev/null 2>&1; then
            w "   Status: ${GREEN}✅ AKTIV${RESET}"

            if [ "$ip" = "$LOCAL_IP" ] || [ "$ip" = "127.0.0.1" ]; then
                read -r cpu ram <<< "$(local_stats)"
                w "   ${BLUE}CPU:${RESET} ${cpu}%  ${BLUE}RAM:${RESET} ${ram}%"
            else
                stats=$(timeout 3 sshpass -p "$(get_pass "${ip}")" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=1 "user@${ip}" \
                    "idle=\$(top -b -n1 2>/dev/null | grep '^%Cpu' | grep -oP '[0-9,]+(?=\s*id)' | tr ',' '.'); idle=\${idle:-100}; idle=\${idle%%.*}; cpu=\$((100-idle)); [ \$cpu -lt 0 ] && cpu=0; ram=\$(free | awk '/^Mem:/{printf \"%.0f\",\$3/\$2*100}'); echo \"\$cpu \$ram\"")
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

    # Koordinator + Modus
    w "${BLUE}📊 Koordinator (Round-Robin)${RESET}"
    if ps aux 2>/dev/null | grep -q "[u]vicorn koordinator"; then
        w "   Status: ${GREEN}✅ AKTIV (http://192.168.178.109:5000)${RESET}"
        # Modus anzeigen
        if [ -f /tmp/llama_mode.json ]; then
            mode=$(python3 -c "import json; d=json.load(open('/tmp/llama_mode.json')); print(d['mode'])" 2>/dev/null)
            reason=$(python3 -c "import json; d=json.load(open('/tmp/llama_mode.json')); print(d['reason'])" 2>/dev/null)
            if [ "$mode" = "petals" ]; then
                w "   Modus: ${GREEN}🌸 Petals${RESET} (${reason})"
            else
                w "   Modus: ${YELLOW}⚙ llama.cpp${RESET} (${reason})"
            fi
        fi
    else
        w "   Status: ${RED}❌ INAKTIV${RESET}"
        w "   Start: cd ~/Dokumente/KI_Lastverteilung_Petals && ~/petals-env/bin/python scripts/koordinator.py &'"
    fi
    w ""

    # Anfrage-Statistik
    if [ -f /tmp/llama_stats.json ] || [ -f /tmp/llama_requests.json ]; then
        w "${BOLD}────────── Anfrage-Statistik ──────────${RESET}"
        session_total=0
        per_worker=""

        # Koordinator-Stats
        if [ -f /tmp/llama_stats.json ]; then
            session_total=$(python3 -c "import json; d=json.load(open('/tmp/llama_stats.json')); print(d.get('total_requests',0))" 2>/dev/null)
            per_worker=$(python3 -c "
import json
d=json.load(open('/tmp/llama_stats.json'))
for w,info in d.get('workers',{}).items():
    ip=w.split('//')[1].split(':')[0] if '//' in w else w
    req=info.get('requests_session',0)
    lat=info.get('avg_latency_ms','?')
    cpu=info.get('cpu_percent','?')
    ram=info.get('ram_percent','?')
    print(f'{ip}|{req}|{lat}|{cpu}|{ram}')
" 2>/dev/null)
        fi

        # Client-Stats (Fallback)
        if [ -f /tmp/llama_requests.json ]; then
            client_total=$(python3 -c "import json; d=json.load(open('/tmp/llama_requests.json')); print(d.get('session_total',0))" 2>/dev/null)
            client_workers=$(python3 -c "
import json
d=json.load(open('/tmp/llama_requests.json'))
for w,c in d.get('per_worker',{}).items():
    print(f'{w}|{c}|-|-|-')
" 2>/dev/null)
            if [ -z "$per_worker" ]; then
                session_total=$client_total
                per_worker=$client_workers
            else
                session_total=$((session_total + client_total))
                per_worker="${per_worker}
${client_workers}"
            fi
        fi

        w "   Gesamt: ${BOLD}${session_total} Anfragen${RESET}"
        while IFS='|' read -r ip req lat cpu ram; do
            [ -z "$ip" ] && continue
            [ "$ip" = "$LOCAL_IP" ] && ip="${ip} (lokal)"
            w "   ${BLUE}${ip}${RESET}: ${req} Anfragen (${lat}ms, CPU:${cpu}%, RAM:${ram}%)"
        done <<< "$per_worker"
        w ""
    fi
    w "${YELLOW}Drücke Ctrl+C zum Beenden${RESET}"

    printf "\033[J"
    sleep 2
done
