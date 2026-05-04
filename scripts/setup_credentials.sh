#!/bin/bash
# Hilfskript zum Erstellen der credentials.json
# Wird nicht von Git getrackt (siehe .gitignore)

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PROJECT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
CREDS="$PROJECT_DIR/credentials.json"

if [ -f "$CREDS" ]; then
    echo "credentials.json existiert bereits. Überschreiben? (j/N)"
    read -r answer
    if [ "$answer" != "j" ] && [ "$answer" != "J" ]; then
        echo "Abbruch."
        exit 0
    fi
fi

echo "=== SSH-Zugangsdaten einrichten ==="
echo ""
read -p "Standard Benutzername: " def_user
read -sp "Standard Passwort: " def_pass
echo ""
echo ""

# Datei erstellen (nicht im Git!)
cat > "$CREDS" << EOF
{
    "default_user": "$def_user",
    "default_pass": "$def_pass",
    "nodes": {}
}
EOF

chmod 600 "$CREDS"
echo "✅ $CREDS erstellt (nur lesbar für Besitzer)."
echo ""
echo "Für individuelle Node-Credentials editiere die Datei manuell:"
echo '{'
echo '    "nodes": {'
 echo '        "10.0.0.42": {"user": "admin", "pass": "geheim"}'
echo '    }'
echo '}'