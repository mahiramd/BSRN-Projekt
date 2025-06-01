import multiprocessing
from discovery import discovery_service_starten
from network import network_listener_starten
from cli import start_cli
import toml

# Funktion zum Laden der Konfiguration aus einer Datei im TOML-Format
def lade_konfiguration():
    with open("config.toml", "r") as f:
        return toml.load(f)

if __name__ == "__main__":
    # Konfiguration einlesen
    config = lade_konfiguration()
    # Manager erzeugen, um einen gemeinsamen Speicher (dict) für Prozesse zu erstellen
    manager = multiprocessing.Manager()
    users = manager.dict()  # Gemeinsames Wörterbuch für bekannte Nutzer

    # Discovery-Service als separater Prozess starten
    if config.get("discovery", True):
        discovery = multiprocessing.Process(target=discovery_service_starten, args=(config, users))
        discovery.start()
    # Netzwerk-Listener als separater Prozess starten
    network = multiprocessing.Process(target=network_listener_starten, args=(config, users))

    discovery.start()  # Discovery-Prozess starten
    network.start()    # Netzwerk-Prozess starten

    # Die Kommandozeile (CLI) läuft im Hauptprozess, damit Eingaben funktionieren
    try:
        start_cli(config, users)
    finally:
        # Wenn CLI beendet wird, auch die anderen Prozesse stoppen
        discovery.terminate()
        network.terminate()
