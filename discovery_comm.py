"""
@file discovery_comm.py
@brief Verantwortlich für das Auffinden und die Verwaltung von Chat-Teilnehmern im lokalen Netzwerk.

Dieses Modul übernimmt die Discovery-Funktion im Peer-to-Peer-Netzwerk.
Nutzer werden über UDP-Broadcast gefunden und bekannt gemacht (JOIN, WHO, LEAVE).
Die Nutzerliste wird regelmäßig synchronisiert, damit immer die aktuellen Teilnehmer angezeigt werden.

Optimiert für Tests auf localhost (mehrere Instanzen auf einem PC).
@author Mahir Ahmad, Sena Akpolad, Onur Ücelehan, Meriam Lakhrissi, Najiba Sulaimankhel
@date 2025
"""
import socket
import time

## Discovery-Service: Findet andere Nutzer im lokalen Netzwerk und verwaltet die Kontaktliste.
def discovery_service(ui_queue, disc_queue, config, kontaktbuch):
    """
    Erkennt andere Nutzer im lokalen Netz per UDP-Broadcast und synchronisiert die Kontaktliste.
    Wartet nach WHO kurz auf alle SEEN-Antworten und merged sie.

    @param ui_queue: Queue für System-/Statusnachrichten
    @param disc_queue: Queue für eingehende Discovery-Kommandos aus dem CLI 
    @param config: Dictionary mit Konfiguration (Nickname, Ports, etc.)
    @param kontaktbuch: Manager Dictionary zur Verwaltung aller bekannten Kontakte
    @return: None
    """

    nickname = config["handle"]
    udp_port = config["whoisport"]
    tcp_port = config["port"]

    hostname = socket.gethostname()
    eigene_ip = socket.gethostbyname(hostname)
    ui_queue.put(f"[Netzwerk] Eigene IP: {eigene_ip}")

    peers = {nickname: (eigene_ip, tcp_port)}
    kontaktbuch[nickname] = (eigene_ip, tcp_port)
    joined = False

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", udp_port))
    sock.setblocking(False)

    # Beim Start: JOIN und mehrere WHO senden
    join_msg = f"JOIN {nickname} {tcp_port}".encode()
    sock.sendto(join_msg, ("255.255.255.255", udp_port))
    for _ in range(3):
        sock.sendto(b"WHO", ("255.255.255.255", udp_port))
        time.sleep(0.2)

    # Merger-Speicher für SEEN-Einträge und Timestamp Messung
    seen_cache = {}
    seen_timer = 0
    awaiting_seen = False

    while True:
        # --- 1. Eingehende Nachrichten verarbeiten ---
        try:
            data, addr = sock.recvfrom(512)
            msg = data.decode().strip()
            if msg.startswith("JOIN"):
                _, user, port = msg.split()
                if user == nickname:
                    continue
                peers[user] = (addr[0], int(port))
                kontaktbuch[user] = (addr[0], int(port))
                # Antwortet auf JOIN auch selbst (Bidirektional)
                join_reply = f"JOIN {nickname} {tcp_port}".encode()
                sock.sendto(join_reply, (addr[0], udp_port))
                ui_queue.put(f"[Peer] {user} ist dem Chat beigetreten.")

                # UPDATE: Nach jedem JOIN mehrfach WHO senden (robust gegen Race Conditions)
                for _ in range(3):
                    sock.sendto(b"WHO", ("255.255.255.255", udp_port))
                    time.sleep(0.2)

            elif msg == "WHO":
                antwort = ", ".join(f"{n} {ip} {p}" for n, (ip, p) in peers.items())
                response = f"SEEN {antwort}"
                sock.sendto(response.encode(), addr)

            elif msg.startswith("LEAVE"):
                _, user = msg.split()
                peers.pop(user, None)
                kontaktbuch.pop(user, None)
                ui_queue.put(f"[Peer] {user} hat den Chat verlassen.")

            elif msg.startswith("SEEN"):
                eintraege = msg.replace("SEEN", "").strip().split(",")
                for eintrag in eintraege:
                    if eintrag.strip():
                        try:
                            name, ip, p = eintrag.strip().split()
                            peers[name] = (ip, int(p))
                            kontaktbuch[name] = (ip, int(p))
                            seen_cache[name] = (ip, int(p))
                        except Exception:
                            continue
                if awaiting_seen:
                    seen_timer = time.time()  # Reset: neues SEEN eingetroffen

        except BlockingIOError:
            pass

        # --- 2. CLI-Kommandos abarbeiten ---
        while not disc_queue.empty():
            befehl = disc_queue.get()
            if befehl == "WHO":
                # Raceproof: WHO mehrfach, dann kurz auf SEEN warten
                for _ in range(3):
                    sock.sendto(b"WHO", ("255.255.255.255", udp_port))
                    time.sleep(0.2)
                awaiting_seen = True
                seen_cache = {}
                seen_timer = time.time()
                ui_queue.put("[System] WHO-Broadcast gesendet.")
            elif befehl.startswith("JOIN"):
                sock.sendto(befehl.encode(), ("255.255.255.255", udp_port))
                # UPDATE: Auch nach eigenem JOIN mehrfach WHO senden
                for _ in range(3):
                    sock.sendto(b"WHO", ("255.255.255.255", udp_port))
                    time.sleep(0.2)
                ui_queue.put("[System] JOIN gesendet.")
                joined = True
            elif befehl.startswith("LEAVE"):
                sock.sendto(befehl.encode(), ("255.255.255.255", udp_port))
                ui_queue.put("[System] LEAVE gesendet.")
            elif befehl == "PEERS":
                if kontaktbuch:
                    ui_queue.put("[Peers] Aktuelle Nutzer:")
                    for n, (ip, port) in kontaktbuch.items():
                        ui_queue.put(f" - {n} @ {ip}:{port}")
                else:
                    ui_queue.put("[Peers] Keine anderen Nutzer gefunden.")

        # --- 3. WHO-Nachbearbeitung (Warte auf alle SEEN, dann einmal Kontaktbuch-Update) ---
        if awaiting_seen and (time.time() - seen_timer) > 0.6:
            for n, (ip, p) in seen_cache.items():
                kontaktbuch[n] = (ip, int(p))
                peers[n] = (ip, int(p))
            ui_queue.put("[System] Nutzerliste aktualisiert.")
            awaiting_seen = False
            seen_cache = {}

        time.sleep(0.1)
