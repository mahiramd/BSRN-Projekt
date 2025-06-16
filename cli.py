
import socket
import os
import toml

# Schickt ne Nachricht an alle im Netzwerk (Broadcast)
def send_broadcast(message, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(message.encode("utf-8"), ("255.255.255.255", port))

# Kommandozeilen-Interface starten, um mit dem Chat zu interagieren
def start_cli(config, users):
    handle = config["handle"]
    port = config["port"]
    whoisport = config["whoisport"]
    away = config.get("away", False)

    my_ip = socket.gethostbyname(socket.gethostname())
    users[handle] = (my_ip, port)

    print("[INFO] Bitte zuerst mit: join <name> <port> dem Chat beitreten.")

    joined = False  # Erst nach 'join' aktiv

    try:
        while True:
            command = input("Eingabe >> ").strip()

            if not joined and not command.startswith("join"):
                if command == "help":
                    print("""
[HILFE – verfügbare Befehle]""")
                    print(" join <name> <port>      – Dem Chat beitreten")
                    print(" help                   – Diese Hilfe anzeigen")
                    print(" exit                   – Programm beenden")
                else:
                    print("[WARNUNG] Bitte zuerst mit 'join <name> <port>' dem Chat beitreten.")
                continue

            if command == "who":
                send_broadcast("WHO", whoisport)

            elif command == "users":
                print("[KNOWUSERS / User, die verfügbar sind]:")
                for name, (ipadresse, userport) in users.items():
                    print(f"  {name} @ {ipadresse}:{userport}")

            elif command.startswith("msg"):
                parts = command.split(" ", 2)
                if len(parts) == 3:
                    target = parts[1]
                    text = parts[2]
                    if target in users:
                        ip, userport = users[target]
                        msg = f"MSG {handle} {text}"
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.sendto(msg.encode("utf-8"), (ip, userport))
                    else:
                        print("[WARNUNG] Nutzer unbekannt.")
                else:
                    print("[FEHLER] Format: msg <name> <text>")

            elif command.startswith("img"):
                parts = command.split(" ", 2)
                if len(parts) == 3:
                    target = parts[1]
                    filepath = parts[2]
                    if target in users:
                        if os.path.exists(filepath):
                            filesize = os.path.getsize(filepath)
                            ip, userport = users[target]
                            msg = f"IMG {handle} {filesize}"
                            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            sock.sendto(msg.encode("utf-8"), (ip, userport))
                            with open(filepath, "rb") as f:
                                data = f.read()
                                sock.sendto(data, (ip, userport))
                            print(f"[INFO] Bild an {target} gesendet.")
                        else:
                            print("[FEHLER] Bildpfad existiert nicht.")
                    else:
                        print("[FEHLER] Zielnutzer unbekannt.")

            elif command == "away on":
                away = True
                config["away"] = True
                with open("config.toml", "w") as f:
                    toml.dump(config, f)
                print("[INFO] Abwesenheitsmodus aktiviert.")

            elif command == "away off":
                away = False
                config["away"] = False
                with open("config.toml", "w") as f:
                    toml.dump(config, f)
                print("[INFO] Abwesenheitsmodus deaktiviert.")

            elif command.startswith("set "):
                parts = command.split(" ", 2)
                if len(parts) == 3:
                    key, value = parts[1], parts[2]
                    if key in config:
                        config[key] = value
                        with open("config.toml", "w") as f:
                            toml.dump(config, f)
                        print(f"[INFO] Konfiguration geändert: {key} = {value}")
                    else:
                        print("[FEHLER] Unbekannter Parameter.")
                else:
                    print("[FEHLER] Format: set <parameter> <wert>")

            elif command.startswith("join "):
                parts = command.split()
                if len(parts) == 3:
                    new_handle = parts[1]
                    new_port = int(parts[2])
                    send_broadcast(f"LEAVE {handle}", whoisport)
                    handle = new_handle
                    port = new_port
                    config["handle"] = handle
                    config["port"] = port
                    with open("config.toml", "w") as f:
                        toml.dump(config, f)
                    my_ip = socket.gethostbyname(socket.gethostname())
                    users[handle] = (my_ip, port)
                    send_broadcast(f"JOIN {handle} {port}", whoisport)
                    send_broadcast("WHO", whoisport)
                    joined = True
                    print(f"[INFO] Du hast dich neu verbunden als {handle}:{port}")
                else:
                    print("[FEHLER] Format: join <name> <port>")

            elif command == "leave":
                send_broadcast(f"LEAVE {handle}", whoisport)
                joined = False
                print(f"[INFO] Du hast den Chat verlassen. Du bist jetzt offline.")

            elif command == "help":
                print("""
[HILFE – verfügbare Befehle]""")
                print(" join <name> <port>      – Dem Chat beitreten")
                print(" leave                  – Den Chat verlassen")
                print(" who                    – Wer ist online?")
                print(" users                  – Liste der bekannten Nutzer")
                print(" msg <name> <text>      – Textnachricht senden")
                print(" img <name> <pfad>      – Bild senden")
                print(" set <key> <wert>       – Konfiguration ändern")
                print(" away on/off            – Abwesenheitsmodus")
                print(" help                   – Diese Hilfe anzeigen")
                print(" exit                   – Programm beenden")

            elif command == "exit":
                if joined:
                    send_broadcast(f"LEAVE {handle}", whoisport)
                    print("[INFO] Du hast den Chat verlassen.")
                else:
                    print("[INFO] Chat wird beendet.")
                break

            else:
                print("[FEHLER] Unbekannter Befehl. Gib 'help' ein für eine Liste.")
    except KeyboardInterrupt:
        send_broadcast(f"LEAVE {handle}", whoisport)
        print("\n[INFO] Chat verlassen (Strg und C einfach drücken)")
