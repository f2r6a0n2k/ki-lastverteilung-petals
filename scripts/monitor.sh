#!/bin/bash
# Monitor für KI-Lastverteilung
# GARANTIERT: Keine alten Daten bleiben sichtbar

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
    # === GARANTIERTES LÖSCHEN: ANSI-Escape-Sequenz ===
    printf "\033[2J\033[H"
    
    # Header
    echo -e "${BOLD}==========================================${RESET}"
    echo -e "${BOLD}   KI-Lastverteilung Monitor${RESET}"
    echo -e "${BOLD}   Zeit: $(date +%T)${RESET}"
    echo -e "${BOLD}==========================================${RESET}"
    echo ""

    # Elitebook Worker
    echo -e "${BLUE}📍 Elitebook (192.168.178.105:8080)${RESET}"
    if curl -s --connect-timeout 2 http://192.168.178.105:8080/health >/dev/null 2>&1; then
        echo -e "   Status: ${GREEN}✅ AKTIV${RESET}"
        CPU_ELITE=$(sshpass -p "cornholio" ssh -o StrictHostKeyChecking=no user@192.168.178.105 "top -b -n1 | head -4 | tail -1" 2>/dev/null)
        echo "   $CPU_ELITE" | sed 's/^/   /'
    else
        echo -e "   Status: ${RED}❌ INAKTIV${RESET}"
    fi
    echo ""

    # Lokal Worker
    echo -e "${BLUE}📍 Lokal (192.168.178.109:8081)${RESET}"
    if curl -s --connect-timeout 2 http://192.168.178.109:8081/health >/dev/null 2>&1; then
        echo -e "   Status: ${GREEN}✅ AKTIV${RESET}"
        CPU_LOCAL=$(top -b -n1 | head -4 | tail -1)
        echo "   $CPU_LOCAL" | sed 's/^/   /'
    else
        echo -e "   Status: ${RED}❌ INAKTIV${RESET}"
    fi
    echo ""

    # Koordinator
    echo -e "${BLUE}📊 Koordinator (Round-Robin)${RESET}"
    if ps aux | grep -q "[u]vicorn koordinator"; then
        echo -e "   Status: ${GREEN}✅ AKTIV (http://192.168.178.109:5000)${RESET}"
    else
        echo -e "   Status: ${RED}❌ INAKTIV${RESET}"
    fi
    echo ""

    echo -e "${YELLOW}Drücke Ctrl+C zum Beenden${RESET}"
    
    sleep 2
done
