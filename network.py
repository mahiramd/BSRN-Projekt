import socket
import select  # Brauchen wir, um zwei Sockets gleichzeitig abzufragen

# Funktion, die auf Nachrichten wartet und reagiert (egal ob Chat oder WHO etc.)
def network_listener_starten(config, users):
    port = config["port"]           # Der Port, auf dem ich Chat-Nachrichten empfange
    whoisport = config["whoisport"] # Der Port für WHO/KNOWUSERS (Discovery-Zeug)
    handle = config["handle"]       # Mein eigener Name (z.B. Alice oder Bob)

    # Chat-Socket (normale Nachrichten wie MSG)
    sock_msg = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_msg.bind(("", port))  # Binde an meinen Chat-Port

    # Zweiter Socket nur für WHO / Discovery (wer ist da?)
    sock_discovery = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_discovery.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_discovery.bind(("", whoisport))  # Discovery-Port (alle hören hier drauf)

    # Beide Sockets gleichzeitig im Blick behalten (Multitasking!)
    sockets = [sock_msg, sock_discovery]

    # Endlosschleife: hört für immer zu, bis man das Programm killt
    while True:
        # select sagt uns: hey, bei diesen Sockets kam was rein!
        readable, _, _ = select.select(sockets, [], [])
        for sock in readable:
            # Nachricht abholen
            data, addr = sock.recvfrom(1024)
            message = data.decode("utf-8").strip()

            # Wenn ne MSG kommt → is einfach ne Chat-Nachricht
            if message.startswith("MSG"):
                parts = message.split(" ", 2)
                if len(parts) == 3:
                    sender = parts[1]  # Von wem kam das?
                    text = parts[2]    # Was hat er geschrieben?
                    print(f"\n[MSG von {sender}]: {text}")  # Direkt ausgeben

            # Wenn ne KNOWUSERS kommt → Liste mit allen Leuten
            elif message.startswith("KNOWUSERS"):
                entries = message.replace("KNOWUSERS ", "").split(",")
                for entry in entries:
                    try:
                        h, ip, p = entry.strip().split()
                        if h != handle:  # Nicht mich selbst eintragen!
                            users[h] = (ip, int(p))  # Speichern (damit ich dem schreiben kann)
                            print(f"[INFO] Neuer User aufgetaucht: {h} @ {ip}:{p}")
                    except Exception as e:
                        print(f"[WARNUNG] Da stimmt was nicht in KNOWUSERS: {e}")