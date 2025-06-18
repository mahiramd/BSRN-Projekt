import os
import socket

## Funktion, die Nachrichten aus dem Netzwerk empfängt und verarbeitet
def network_listener_starten(config, users):
    # Port und eigener Benutzername (Handle) aus der Konfiguration holen
    port = config["port"]
    handle = config["handle"]

    # UDP-Socket erstellen (für Netzwerk-Kommunikation)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Socket an alle Netzwerkadapter auf dem angegebenen Port binden
    sock.bind(("", port))

    # Endlosschleife, um ständig auf eingehende Nachrichten zu warten
    while True:
        expecting_image = False
        expected_size = 0
        current_sender = ''
        expecting_image = False
        expected_size = 0
        current_sender = ''
        # Empfang von Daten (max. 1024 Bytes) und Absenderadresse
        data, addr = sock.recvfrom(65535)
        if expecting_image:
            timestamp = int(time.time())
            filename = f"{current_sender}_{timestamp}.jpg"
            save_path = os.path.join(config["imagepath"], filename)
            os.makedirs(config["imagepath"], exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(data)
            print(f"\n[IMG von {current_sender}]: Bild gespeichert unter {save_path}")
            try:
                import subprocess
                subprocess.run(["xdg-open", save_path])
            except:
                pass
            expecting_image = False
            continue
        try:
            message = data.decode("utf-8").strip()
        except UnicodeDecodeError:
            print("[FEHLER] Empfangene Daten konnten nicht als UTF-8 decodiert werden – vermutlich fehlendes IMG vorher.")
            continue
        data, addr = sock.recvfrom(65535)
        if expecting_image:
            timestamp = int(time.time())
            filename = f"{current_sender}_{timestamp}.jpg"
            save_path = os.path.join(config["imagepath"], filename)
            os.makedirs(config["imagepath"], exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(data)
            print(f"\n[IMG von {current_sender}]: Bild gespeichert unter {save_path}")
            try:
                import subprocess
                subprocess.run(["xdg-open", save_path])
            except:
                pass
            expecting_image = False
            continue
        try:
            message = data.decode("utf-8").strip()
        except UnicodeDecodeError:
            print("[FEHLER] Empfangene Daten konnten nicht als UTF-8 decodiert werden – vermutlich fehlendes IMG vorher.")
            continue
        if expecting_image:
            timestamp = int(time.time())
            filename = f"{current_sender}_{timestamp}.jpg"
            save_path = os.path.join(config["imagepath"], filename)
            os.makedirs(config["imagepath"], exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(data)
            print(f"\n[IMG von {current_sender}]: Bild gespeichert unter {save_path}")
            try:
                import subprocess
                subprocess.run(["xdg-open", save_path])
            except:
                pass
            expecting_image = False
            continue
        try:
            message = data.decode("utf-8").strip()
        except UnicodeDecodeError:
            print("[FEHLER] Empfangene Daten konnten nicht als UTF-8 decodiert werden.")
            continue
        # Daten in lesbaren Text umwandeln und Leerzeichen am Anfang/Ende entfernen
        message = data.decode("utf-8").strip()

        # Wenn die Nachricht mit "MSG" beginnt, ist es eine Chat-Nachricht
        if message.startswith("MSG"):
            # Nachricht in drei Teile aufteilen: "MSG", Sendername, Text
            parts = message.split(" ", 2)
            # Prüfen, ob alle drei Teile vorhanden sind
            if len(parts) == 3:
                sender = parts[1]  # Absendername
                text = parts[2]    # Textnachricht
                # Nachricht auf der Konsole ausgeben
                print(f"\n[MSG von {sender}]: {text}")

        # Wenn die Nachricht mit "KNOWUSERS" beginnt, enthält sie bekannte Nutzer
        elif message.startswith("KNOWUSERS"):
            # Nutzerliste extrahieren und nach Komma trennen
            entries = message.replace("KNOWUSERS ", "").split(",")
            # Alle Einträge durchgehen
            for entry in entries:
                try:
                    # Eintrag aufteilen in Nutzername, IP und Port
                    h, ip, p = entry.strip().split()
                    # Eigenen Nutzernamen ignorieren, nur andere hinzufügen
                    # Eigener Nutzer wird NICHT mehr ignoriert
                    users[h] = (ip, int(p))
                    print(f"[INFO] Neuer oder bekannter User: {h} @ {ip}:{p}")
                    # Nutzer in das Wörterbuch speichern (Name: (IP, Port))
                    users[h] = (ip, int(p))
                    print(f"[INFO] Neuer oder bekannter User: {h} @ {ip}:{p}")
                    print(f"[INFO] Neuer User auf: {h} @ {ip}:{p}")
                except Exception as e:
                    # Falls beim Aufteilen ein Fehler auftritt, Warnung ausgeben
                    print(f"[WARNUNG] Falsche Verwendung von KNOWUSERS: {e}")
