"""
@file start.py
@brief Startet alle Prozesse und das CLI (oder optional GUI) für den Peer-to-Peer-Chat "Plauderkiste".

Dieses Modul ist der Einstiegspunkt der Anwendung. Es kümmert sich um das Laden der Konfiguration,
startet alle benötigten Prozesse (Discovery, Netzwerk, UI) und verwaltet die Kommunikation zwischen ihnen.
Es kann über Kommandozeilenargumente die zu verwendende Konfigurationsdatei wählen.

Die einzelnen Komponenten kommunizieren über multiprocessing.Queue und teilen Daten über Manager-Objekte.

@author Mahir Ahmad, Sena Akpolad, Onur Ücelehan, Meriam Lakhrissi, Najiba Sulaimankhels
@date 2025
"""

import multiprocessing
import sys
import toml
from discovery_comm import discovery_service
from network_comm import network_service
from ui_cli import start_cli

## Hauptfunktion: Initialisiert Konfiguration und startet alle Komponenten.
def main():
    """
    Initialisiert das Plauderkiste-System: Lädt die Konfiguration, erstellt Datenstrukturen,
    startet Discovery-, Netzwerk- und UI-Prozess.

    Kann die Konfigurationsdatei als Argument entgegennehmen, ansonsten wird 'config1.toml' verwendet.
    Am Ende werden die Hintergrundprozesse sauber beendet.

    @return: None
    """
    multiprocessing.set_start_method("spawn")

    # Konfigurationsdatei als Argument, Standard: 'config1.toml'
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config1.toml"
    config = toml.load(config_path)
    config["config_path"] = config_path

    # Gemeinsame Datenstrukturen und Queues für Prozesskommunikation
    manager = multiprocessing.Manager()
    contacts = manager.dict()
    chat_history = manager.list()
    dnd = manager.Value('b', False)    # Nicht-Stören-Modus (bool)
    status = manager.Value('u', "Online")  # Status als Unicode-String

    ui_queue = multiprocessing.Queue()
    disc_queue = multiprocessing.Queue()
    net_queue = multiprocessing.Queue()

    # Start der Discovery- und Netzwerkprozesse
    proc_discovery = multiprocessing.Process(
        target=discovery_service, args=(ui_queue, disc_queue, config, contacts)
    )
    proc_network = multiprocessing.Process(
        target=network_service, args=(ui_queue, net_queue, config, contacts)
    )

    proc_discovery.start()
    proc_network.start()

    try:
        # Start des User-Interfaces (CLI)
        start_cli(ui_queue, disc_queue, net_queue, config, contacts, chat_history, dnd, status)
    except KeyboardInterrupt:
        print("\n[System] Abbruch durch Nutzer (KeyboardInterrupt).")
    finally:
        # Prozesse werden beim Beenden sauber terminiert
        proc_discovery.terminate()
        proc_network.terminate()
        proc_discovery.join()
        proc_network.join()

## Standard-Einstiegspunkt für das Skript.
if __name__ == "__main__":
    main()
