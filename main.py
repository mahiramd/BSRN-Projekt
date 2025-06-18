
import socket
import multiprocessing
import time
from discovery import discovery_service_starten
from network import network_listener_starten
from cli import start_cli
import toml

# Funktion zum Laden der Konfigurationsdatei
def lade_konfiguration():
    with open("config.toml", "r") as f:
        return toml.load(f)

# Prüfen, ob Discovery-Port bereits benutzt wird (z. B. von anderer Instanz)
def port_belegt(port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", port))
        sock.close()
        return False
    except OSError:
        return True

if __name__ == "__main__":
    config = lade_konfiguration()
    manager = multiprocessing.Manager()
    users = manager.dict()

    discovery = None
    if not port_belegt(config["whoisport"]):
        print(f"[MAIN] Discovery wird gestartet auf Port {config['whoisport']}")
        discovery = multiprocessing.Process(target=discovery_service_starten, args=(config, users))
        discovery.start()
    else:
        print(f"[MAIN] Discovery wird NICHT gestartet (Port {config['whoisport']} belegt)")

    network = multiprocessing.Process(target=network_listener_starten, args=(config, users))
    network.start()

    try:
        start_cli(config, users)
    finally:
        if discovery:
            discovery.terminate()
        network.terminate()
