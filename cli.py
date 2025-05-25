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

     # Beim Start mitteilen, dass man dem Chat beitritt (für alle sichtbar)
    send_broadcast(f"JOIN {handle} {port}", whoisport)
    print(f"[INFO] Du bist dem Chat beigetreten als '{handle}'.")

    try:
        while True:
            # Eingabe vom Nutzer abfragen
            command = input("Eingabe >> ").strip()

            # Nutzer fragt nach der Liste aller Online-Nutzer
            if command == "who":
                send_broadcast("WHO", whoisport)

            # Liste der bekannten Nutzer lokal anzeigen
            elif command == "users":
                print("[KNOWUSERS / User, die verfügbar sind]:")
                for name, (ipadresse, userport) in users.items():
                    print(f"  {name} @ {ipadresse}:{userport}")

            # Nachricht an einen bestimmten Nutzer schicken
            elif command.startswith("msg"):
                parts = command.split(" ", 2)
                # Prüfen, ob Nutzername und Text angegeben sind
                if len(parts) == 3:
                    target = parts[1]   # Empfänger
                    text = parts[2]     # Nachrichtentext
                    if target in users:
                        ip, userport = users[target]
                        msg = f"MSG {handle} {text}"  # Nachricht im Chat-Format
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.sendto(msg.encode("utf-8"), (ip, userport))
                    else:
                        print("[WARNUNG] Nutzer unbekannt.")
                else:
                    print("[FEHLER] Format: msg <name> <text>")

            # Chat verlassen und anderen mitteilen
            elif command == "exit":
                send_broadcast(f"LEAVE {handle}", whoisport)
                print("[INFO] Du hast den Chat verlassen.")
                break

            # Für alle anderen Eingaben die verfügbaren Befehle anzeigen
            else:
                print("Verfügbare Befehle: who, users, msg <name> <text>, exit")

    # Bei Tastenkombination Strg+C ebenfalls den Chat verlassen
    except KeyboardInterrupt:
        send_broadcast(f"LEAVE {handle}", whoisport)
        print("\n[INFO] Chat verlassen (Strg und C einfach drücken)")

   