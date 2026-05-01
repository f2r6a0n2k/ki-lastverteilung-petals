#!/bin/bash
# Schönes Chat-Interface für KI-Lastverteilung (wie OpenCode)
# Verwendung: bash /home/frank/Dokumente/KI_Lastverteilung_Petals/scripts/chat.sh

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
echo -e "${DIM}   (wie OpenCode - Round-Robin Worker)${RESET}"
echo -e "${BOLD}==========================================${RESET}"
echo ""
echo -e "${BLUE}Verfügbare Worker:${RESET}"
echo -e "   • Elitebook (192.168.178.105:8080)"
echo -e "   • Lokal (192.168.178.109:8081)"
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

    echo ""
    echo -e "${CYAN}Sende an Worker...${RESET}"

    # Sende an llama_client.py (Round-Robin)
    RESULT=$(python3 /home/frank/Dokumente/KI_Lastverteilung_Petals/scripts/llama_client.py "$USER_PROMPT" 2>&1)

    # Fehler?
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}Fehler beim Senden!${RESET}"
        echo "$RESULT"
        continue
    fi

    # Worker extrahieren (falls in Ausgabe)
    WORKER=$(echo "$RESULT" | grep -o 'http://[^ ]*' | head -1)
    if [[ -z "$WORKER" ]]; then
        WORKER="Unbekannt"
    fi

    # Antwort anzeigen
    echo ""
    echo -e "${GREEN}Antwort von: $WORKER${RESET}"
    echo -e "${DIM}----------------------------------------${RESET}"
    echo "$RESULT" | grep -v '=== llama.cpp Client ===' | grep -v 'Worker:' | grep -v 'Prompt:' | grep -v 'Sende Anfrage...'
    echo -e "${DIM}----------------------------------------${RESET}"
    echo ""
done

cleanup
