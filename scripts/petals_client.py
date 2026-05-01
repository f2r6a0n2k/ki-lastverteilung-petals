#!/usr/bin/env python3
"""
Petals Client - Konfigurierbarer Client für verteiltes KI-Netzwerk
Verwendung: python3 petals_client.py "Deine Frage hier" [--modell MODELL_ID]
"""

import argparse
import json
import sys
from pathlib import Path

def load_config():
    """Lädt die Modell-Konfiguration aus configs/models.json"""
    config_path = Path(__file__).parent.parent / "configs" / "models.json"
    if not config_path.exists():
        # Fallback zur Standardkonfiguration
        return {
            "default_model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "models": []
        }
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description='Petals Client für KI-Lastverteilung')
    parser.add_argument('prompt', nargs='?', default='Hello!', help='Der Prompt für die KI')
    parser.add_argument('--modell', type=str, help='Modell-ID (überschreibt Standardmodell)')
    parser.add_argument('--list-models', action='store_true', help='Verfügbare Modelle anzeigen')
    args = parser.parse_args()

    config = load_config()

    # Verfügbare Modelle anzeigen
    if args.list_models:
        print("=== Verfügbare Modelle ===")
        for model in config.get("models", []):
            print(f"• {model['name']} ({model['id']})")
            print(f"  {model['description']}")
            print(f"  Min. Geräte: {model['min_devices']}, Speicher/Gerät: {model['memory_per_device']}")
            print()
        return

    # Modell auswählen
    model_id = args.modell if args.modell else config.get("default_model", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    print(f"=== Petals Client ===")
    print(f"Modell: {model_id}")
    print(f"Prompt: {args.prompt}")
    print(f"Verbinde mit Petals-Schwarm...")

    try:
        # Petals importieren
        from petals import AutoDistributedConfig, DistributedLlamaForCausalLM, DistributedLlamaTokenizer
        
        # Konfiguration laden
        config = AutoDistributedConfig.from_pretrained(model_id)
        print(f"✅ Verbunden mit {len(config.initial_peers)} Peers")
        
        # Modell und Tokenizer laden
        model = DistributedLlamaForCausalLM.from_pretrained(model_id, config=config)
        tokenizer = DistributedLlamaTokenizer.from_pretrained(model_id)
        
        # Prompt verarbeiten
        print("⏳ Verarbeite Prompt (verteilt auf Worker)...")
        inputs = tokenizer(args.prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=100)
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        print(f"\n=== Antwort ===")
        print(result)
        
    except ImportError:
        print("❌ Petals nicht installiert. Installiere mit: pip install petals")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
