#!/bin/bash
# htop-style Monitor für KI-Lastverteilung
# Nutzt alternativen Screen-Buffer (kein Flackern)

# Farben definieren
GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
RESET="\033[0m"
BOLD="\033[1m"

# Aufräumen bei Beenden (Ctrl+C)
cleanup() {
    tput rmcup 2>/dev/null  # Bildschirm wiederherstellen
    tput cnorm 2>/dev/null # Cursor wieder anzeigen
    exit 0
}
trap cleanup INT TERM

# In den alternativen Bildschirm wechseln (wie htop)
tput smcup
tput civis  # Cursor verstecken

while true; do
    # Cursor an den Anfang der Seite bewegen (0,0)
    echo -en "\033[H"
    
    # Header (feste Position)
    echo -e "${BOLD}==========================================${RESET}"
    echo -e "${BOLD}   KI-Lastverteilung Monitor (htop-style)${RESET}"
    echo -e "${BOLD}   Zeit: $(date +%T)${RESET}"
    echo -e "${BOLD}==========================================${RESET}"
    echo ""

    # --- Elitebook (105:8080) ---
    echo -e "${BLUE}📍 Elitebook (192.168.178.105:8080)${RESET}"
    if curl -s --connect-timeout 2 http://192.168.178.105:8080/health >/dev/null 2>&1; then
        echo -e "   Status: ${GREEN}✅ AKTIV${RESET}"
        # CPU-Last (1x sshpass, Ausgabe zwischenspeichern)
        CPU_ELITE=$(sshpass -p "cornholio" ssh -o StrictHostKeyChecking=no user@192.168.178.105 "top -b -n1 | head -4 | tail -1" 2>/dev/null)
        echo -e "   $CPU_ELITE" | sed 's/^/   /'
    else
        echo -e "   Status: ${RED}❌ INAKTIV${RESET}"
    fi
    echo ""

    # --- Lokal (109:8081) ---
    echo -e "${BLUE}📍 Lokal (192.168.178.109:8081)${RESET}"
    if curl -s --connect-timeout 2 http://192.168.178.109:8081/health >/dev/null 2>&1; then
        echo -e "   Status: ${GREEN}✅ AKTIV${RESET}"
        CPU_LOCAL=$(top -b -n1 | head -4 | tail -1)
        echo -e "   $CPU_LOCAL" | sed 's/^/   /'
    else
        echo -e "   Status: ${RED}❌ INAKTIV${RESET}"
    fi
    echo ""

    # --- Koordinator ---
    echo -e "${BLUE}📊 Koordinator (Round-Robin)${RESET}"
    if ps aux | grep -q "[u]vicorn koordinator"; then
        echo -e "   Status: ${GREEN}✅ AKTIV (http://192.168.178.109:5000)${RESET}"
    else
        echo -e "   Status: ${RED}❌ INAKTIV${RESET}"
    fi
    echo ""

    # --- Footer ---
    echo -e "${YELLOW}Drücke Ctrl+C zum Beenden${RESET}"
    
    # Warten, Cursor dabei oben halten
    sleep 2
done
