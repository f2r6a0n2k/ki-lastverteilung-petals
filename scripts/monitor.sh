#!/bin/bash
# Monitor für KI-Lastverteilung - FINAL (schnell, zuverlässig)
# Verwendung: bash /home/frank/Dokumente/KI_Lastverteilung_Petals/scripts/monitor.sh

# Farben
GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
RESET="\033[0m"
BOLD="\033[1m"

# Aufräumen 
cleanup() {
    tput cnorm 2>/dev/null
    exit 0
}
trap cleanup INT TERM

# Cursor verstecken
tput civis 2>/dev/null

while true; do
    # Bildschirm komplett löschen (zuverlässig)
    clear
    
    # Header
    echo -e "${BOLD}==========================================${RESET}"
    echo -e "${BOLD}   KI-Lastverteilung Monitor${RESET}"
    echo -e "${BOLD}   Zeit: $(date +%T)${RESET}"
    echo -e "${BOLD}==========================================${RESET}"
    echo ""

    # === Elitebook Worker (105:8080) ===
    echo -e "${BLUE}📍 Elitebook (192.168.178.105:8080)${RESET}"
    if curl -s --connect-timeout 0.5 http://192.168.178.105:8080/health >/dev/null 2>&1; then
        echo -e "   Status: ${GREEN}✅ AKTIV${RESET}"
        # CPU-Last via sshpass
        CPU_ELITE=$(sshpass -p "cornholio" ssh -o StrictHostKeyChecking=no user@192.168.178.105 "top -b -n1 2>/dev/null | grep '^%Cpu'" 2>/dev/null | head -1)
        if [ -n "$CPU_ELITE" ]; then
            echo -e "   ${BLUE}CPU-Last:${RESET} $CPU_ELITE"
        else
            echo -e "   ${YELLOW}CPU-Last: ${RED}✘ Nicht messbar${RESET}"
        fi
    else
        echo -e "   Status: ${RED}❌ INAKTIV${RESET}"
        echo -e "   Start: ssh user@192.168.178.105 'bash ~/start_elitebook_worker.sh'"
    fi
    echo ""

    # === Lokal Worker (109:8081) ===
    echo -e "${BLUE}📍 Lokal (192.168.178.109:8081)${RESET}"
    if curl -s --connect-timeout 0.5 http://192.168.178.109:8081/health >/dev/null 2>&1; then
        echo -e "   Status: ${GREEN}✅ AKTIV${RESET}"
        # CPU-Last lokal 
        CPU_LOCAL=$(top -b -n1 2>/dev/null | grep '^%Cpu' | head -1)
        if [ -n "$CPU_LOCAL" ]; then
            echo -e "   ${BLUE}CPU-Last:${RESET} $CPU_LOCAL"
        else
            echo -e "   ${YELLOW}CPU-Last: ${RED}✘ Nicht messbar${RESET}"
        fi
    else
        echo -e "   Status: ${RED}❌ INAKTIV${RESET}"
        echo -e "   Start: bash ~/start_local_worker.sh"
    fi
    echo ""

    # === Koordinator ===
    echo -e "${BLUE}📊 Koordinator (Round-Robin)${RESET}"
    if ps aux 2>/dev/null | grep -q "[u]vicorn koordinator"; then
        echo -e "   Status: ${GREEN}✅ AKTIV (http://192.168.178.109:5000)${RESET}"
    else
        echo -e "   Status: ${RED}❌ INAKTIV${RESET}"
    fi
    echo ""

    echo -e "${YELLOW}Drücke Ctrl+C zum Beenden${RESET}"
    
    # Kurze Pause (nur für CPU-Entlastung)
    sleep 0.3
done
