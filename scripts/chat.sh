#!/bin/bash
# Chat-Interface für KI-Lastverteilung (Round-Robin)
# Verwendung: bash scripts/chat.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../configs/workers.json"

# Farben
GREEN="\033[1;32m"
RED="\033[1;31m"
BLUE="\033[1;34m"
CYAN="\033[1;36m"
MAGENTA="\033[1;35m"
YELLOW="\033[1;33m"
RESET="\033[0m"
BOLD="\033[1m"
DIM="\033[2m"

# Worker aus Konfiguration laden
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Konfigurationsdatei nicht gefunden: ${CONFIG_FILE}${RESET}"
    exit 1
fi

mapfile -t WORKERS < <(python3 -c "import json; [print(w['url']) for w in json.load(open('${CONFIG_FILE}'))['workers']]")
mapfile -t NAMES < <(python3 -c "import json; [print(w.get('name', 'Worker')) for w in json.load(open('${CONFIG_FILE}'))['workers']]")

if [ ${#WORKERS[@]} -eq 0 ]; then
    echo -e "${RED}Keine Worker in der Konfiguration gefunden.${RESET}"
    exit 1
fi

WORKER_INDEX=0

# Aufräumen
cleanup() {
    tput cnorm 2>/dev/null
    echo -e "${RESET}"
    exit 0
}
trap cleanup INT TERM

# Cursor verstecken
tput civis 2>/dev/null

# Start-Screen
clear
echo -e "${BOLD}==========================================${RESET}"
echo -e "${BOLD}   KI-Lastverteilung Chat-Interface${RESET}"
echo -e "${DIM}   (Round-Robin Lastverteilung)${RESET}"
echo -e "${BOLD}==========================================${RESET}"
echo ""
echo -e "${BLUE}Verfugbare Worker:${RESET}"
for i in "${!WORKERS[@]}"; do
    echo -e "   • ${NAMES[$i]} (${WORKERS[$i]})"
done
echo ""
echo -e "${YELLOW}Tipp: 'quit' oder 'exit' zum Beenden${RESET}"
echo ""

# Chat-Schleife
while true; do
    # Prompt-Eingabe
    echo -en "${MAGENTA}Du › ${RESET}"
    read -r USER_PROMPT

    # Beenden?
    if [[ "$USER_PROMPT" == "quit" || "$USER_PROMPT" == "exit" ]]; then
        echo -e "${YELLOW}Beende...${RESET}"
        break
    fi

    # Leer?
    if [[ -z "$USER_PROMPT" ]]; then
        echo -e "${RED}Bitte Prompt eingeben!${RESET}"
        continue
    fi

    # Round-Robin Worker auswählen
    CURRENT_WORKER="${WORKERS[$WORKER_INDEX]}"
    CURRENT_NAME="${NAMES[$WORKER_INDEX]}"
    WORKER_INDEX=$(( (WORKER_INDEX + 1) % ${#WORKERS[@]} ))

    echo ""
    echo -e "${CYAN}Sende an ${CURRENT_NAME}...${RESET}"

    # Direkt an Worker senden
    RESPONSE=$(curl -s --max-time 60 -X POST "${CURRENT_WORKER}/completion" \
        -H "Content-Type: application/json" \
        -d "{\"prompt\": \"${USER_PROMPT}\", \"max_tokens\": 100}" 2>&1)

    # Fehler?
    if [[ $? -ne 0 || -z "$RESPONSE" ]]; then
        echo -e "${RED}Fehler beim Senden!${RESET}"
        echo -e "${DIM}Worker: ${CURRENT_WORKER}${RESET}"
        continue
    fi

    # Antwort extrahieren
    CONTENT=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('content','') or d.get('response','No response'))" 2>/dev/null)

    if [[ -z "$CONTENT" ]]; then
        echo -e "${RED}Keine gultige Antwort erhalten.${RESET}"
        echo -e "${DIM}Raw: ${RESPONSE:0:100}...${RESET}"
        continue
    fi

    # Antwort anzeigen
    echo ""
    echo -e "${GREEN}Antwort von: ${CURRENT_NAME} (${CURRENT_WORKER})${RESET}"
    echo -e "${DIM}----------------------------------------${RESET}"
    echo "$CONTENT"
    echo -e "${DIM}----------------------------------------${RESET}"
    echo ""
done

cleanup
