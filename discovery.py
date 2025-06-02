import socket

## Funktion, die im Netzwerk nach anderen Nutzern sucht und deren Verbindungen verwaltet
def discovery_service_starten(config, users):
    whois_port = config["whoisport"]  # Port, auf dem die Discovery-Anfragen reinkommen
    my_handle = config["handle"]       # Eigener Nutzername
    my_port = config["port"]           # Eigener Port für Nachrichten

    # Eigene IP-Adresse herausfinden (für lokale Netzwerke reicht das meist aus)
    my_ip = socket.gethostbyname(socket.gethostname())
    # Eigenen Nutzer mit IP und Port in die Nutzerliste eintragen
    users[my_handle] = (my_ip, my_port)

    # UDP-Socket erstellen
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Erlaubt, den Port sofort wieder zu benutzen, auch wenn er kurz zuvor belegt war
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", whois_port))
    print(f"[DISCOVERY] Gestartet auf {whois_port}. IP ist {my_ip}")

    # Endlosschleife, um ständig Nachrichten zu empfangen und zu verarbeiten
    while True:
        try:
            # Daten und Adresse des Absenders empfangen
            data, addr = sock.recvfrom(1024)
            # Nachricht in Text umwandeln und Leerzeichen entfernen
            message = data.decode("utf-8").strip()

            # Wenn die Nachricht mit "JOIN" beginnt, will sich jemand anmelden
            if message.startswith("JOIN"):
                parts = message.split()
                # Nachricht muss genau aus drei Teilen bestehen: "JOIN", Nutzername, Port
                if len(parts) == 3:
                    handle = parts[1]     # Nutzername
                    port = int(parts[2]) # Portnummer als Zahl
                    # Nutzer mit IP (vom Absender) und Port speichern
                    users[handle] = (addr[0], port)

            # Wenn Nachricht mit "LEAVE" beginnt, will sich jemand abmelden
            elif message.startswith("LEAVE"):
                parts = message.split()
                # Nachricht muss genau aus zwei Teilen bestehen: "LEAVE", Nutzername
                if len(parts) == 2:
                    handle = parts[1]
                    # Nutzer aus der Liste entfernen (kein Fehler, wenn nicht da)
                    users.pop(handle, None)

            # Wenn Nachricht genau "WHO" ist, fragt jemand nach der Nutzerliste
            elif message == "WHO":
                response = "KNOWUSERS "
                # Für jeden Nutzer einen Eintrag "Name IP Port" erstellen
                entries = [f"{h} {ip} {p}" for h, (ip, p) in users.items()]
                # Alle Einträge mit Komma trennen und an die Antwort anhängen
                response += ", ".join(entries)
                # Antwort an den Absender schicken (wichtig: UTF-8 wegen Sonderzeichen)
                sock.sendto(response.encode("utf-8"), addr)

        # Wenn der Socket kurzzeitig getrennt wird, einfach weiter machen
        except ConnectionResetError:
            continue