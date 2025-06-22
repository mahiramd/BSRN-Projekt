"""
@file network_comm.py
@brief Modul für den Austausch von Nachrichten und Bildern im Peer-to-Peer-Chat "Plauderkiste".

Dieses Modul kümmert sich um das Senden und Empfangen von Textnachrichten und Bilddateien zwischen den Teilnehmern.
Die Kommunikation läuft über TCP – jedes Plauderkiste-Programm ist zugleich Client und Server.
Nachrichten und Bilder werden von diesem Modul empfangen, verarbeitet und an das User-Interface weitergegeben.

Es werden keine Klassen verwendet. Die Anbindung an das CLI und die Discovery-Komponente erfolgt über Queues.

@author Mahir Ahmad, Sena Akpolad, Onur Ücelehan, Meriam Lakhrissi, Najiba Sulaimankhel
@date 2025
"""

import socket
import os
import subprocess
import sys


def open_image(filepath):
    # Öffnet ein Bild im Standardprogramm des OS
    try:
        if sys.platform.startswith('darwin'): # MacOS
            subprocess.Popen(['open', filepath])
        elif os.name == 'nt': # Windows
            os.startfile(filepath)
        elif os.name == 'posix': # Linux uvm.
            subprocess.Popen(['xdg-open', filepath])
    except Exception as e:
        pass # Fehler muss nicht beim Nutzer angezeigt werden

## TCP-Server & Client für Nachrichten- und Bildübertragung.
def network_service(ui_queue, net_queue, config, peers):
    """
    Startet den TCP-Server und verarbeitet sowohl eingehende als auch ausgehende Nachrichten und Bilder.

    @param ui_queue: Queue für Status- und Chatnachrichten an die Benutzeroberfläche (multiprocessing.Queue)
    @param net_queue: Queue für ausgehende Befehle/Sendewünsche aus dem CLI (multiprocessing.Queue)
    @param config: Konfigurationsdaten (dict) mit Nutzername, Port, Bildordner etc.
    @param peers: Kontaktbuch (Manager.dict), aktuelle Peer-Liste mit IP und Port
    @return: None
    """
    username = config["handle"]
    tcp_port = config["port"]
    image_folder = config.get("imagepath", "./images")

    # Sicherstellen, dass der Ordner für Bilder existiert
    if not os.path.exists(image_folder):
        os.makedirs(image_folder, exist_ok=True)

    # Startet den TCP-Server für eingehende Nachrichten/Bilder
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("", tcp_port))
    server.listen()
    server.settimeout(0.5)
    ui_queue.put(f"[System] Lausche auf TCP-Port {tcp_port}")

    while True:
        # Prüfung auf eingehende Verbindungen (Textnachricht oder Bild)
        try:
            conn, addr = server.accept()
            header = conn.recv(512).decode().strip()
            if header.startswith("IMG"):
                # Empfang einer Bilddatei (Header: IMG filename size)
                try:
                    _, filename, size_str = header.split()
                    size = int(size_str)
                    conn.sendall(b"OK")
                    data = b""
                    while len(data) < size:
                        chunk = conn.recv(min(4096, size - len(data)))
                        if not chunk:
                            break
                        data += chunk
                    filepath = os.path.join(image_folder, filename)
                    with open(filepath, "wb") as f:
                        f.write(data)
                    ui_queue.put(f"[Bild] Empfangen: {filename} ({size} Bytes)")
                    open_image(filepath)
                except Exception as e:
                    ui_queue.put(f"[Fehler] Bildempfang fehlgeschlagen: {e}")
            else:
                # Normale Textnachricht (Absender:Nachricht)
                ui_queue.put(f"[Nachricht] {header}")
            conn.close()
        except socket.timeout:
            # Kein neuer Client, das ist der Normalfall bei kurzen Timeouts
            pass

        # Behandlung von ausgehenden Nachrichten/Bildern
        while not net_queue.empty():
            cmd = net_queue.get()
            if cmd.startswith("MSG"):
                # Sende eine Textnachricht an einen Peer
                _, recipient, text = cmd.split(" ", 2)
                if recipient in peers:
                    try:
                        ip, port = peers[recipient]
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect((ip, port))
                        s.sendall(f"{username}: {text}".encode())
                        s.close()
                        ui_queue.put(f"[System] Nachricht an {recipient} gesendet.")
                    except Exception as e:
                        ui_queue.put(f"[Fehler] Nachricht nicht gesendet: {e}")
                else:
                    ui_queue.put(f"[Warnung] Empfänger {recipient} nicht gefunden. (Tipp: who ausführen)")
            elif cmd.startswith("IMG_SEND"):
                # Sende ein Bild an einen Peer
                parts = cmd.split(" ", 1)[1].split("::")
                header, path = parts
                recipient, filename, size = header.split()[:3]
                size = int(size)
                if recipient in peers:
                    try:
                        ip, port = peers[recipient]
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect((ip, port))
                        s.sendall(f"IMG {filename} {size}\n".encode())
                        ack = s.recv(16)
                        if ack == b"OK":
                            with open(path, "rb") as f:
                                s.sendall(f.read())
                            ui_queue.put(f"[System] Bild an {recipient} gesendet: {filename}")
                        s.close()
                    except Exception as e:
                        ui_queue.put(f"[Fehler] Bildversand fehlgeschlagen: {e}")
                else:
                    ui_queue.put(f"[Warnung] Empfänger {recipient} nicht gefunden. (Tipp: who ausführen)")
