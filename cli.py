import socket

## Funktion, um eine Nachricht an alle im Netzwerk per Broadcast zu senden
def send_broadcast(message, port):
    # UDP-Socket erstellen
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Broadcast erlauben (damit die Nachricht an alle gesendet wird)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Nachricht an die Broadcast-Adresse senden (alle im lokalen Netzwerk)
    sock.sendto(message.encode("utf-8"), ("255.255.255.255", port))

## Kommandozeilen-Interface starten, um mit dem Chat zu interagieren
def start_cli(config, users):
    handle = config["handle"]       # Eigener Nutzername
    port = config["port"]           # Eigener Port für eingehende Nachrichten
    whoisport = config["whoisport"] # Port für Discovery-Nachrichten

   