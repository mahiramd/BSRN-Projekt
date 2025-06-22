"""
@file ui_cli.py
@brief Farbige, interaktive Kommandozeilen-Benutzeroberfläche für den Peer-to-Peer-Chat "Plauderkiste".

Dieses Modul bietet eine textbasierte, farbige Chat-Oberfläche. Nutzer können Nachrichten senden,
Bilder übertragen, Kontakte verwalten und ihren Status setzen. Die Oberfläche zeigt alle wichtigen
Informationen wie Status, DND (Nicht-stören), Kontakte und Chatverlauf an und gibt nützliche Hilfetexte aus.

Das Interface kommuniziert über Queues mit den Discovery- und Netzwerkmodulen.
Für die Farbdarstellung wird das Paket colorama verwendet.

Das CLI ist so gestaltet, dass es ohne Klassen auskommt und auch für technisch weniger erfahrene
Nutzer leicht zu bedienen ist.

@author Mahir Ahmad, Sena Akpolad, Onur Ücelehan, Meriam Lakhrissi, Najiba Sulaimankhel
@date 2025
"""

import threading
import os
import time
from colorama import init, Fore, Style

init(autoreset=True)

## Gibt einen Hilfetext für alle verfügbaren Kommandos aus.
def print_help():
    """
    Gibt eine Übersicht über alle unterstützten Chat-Befehle und deren Anwendung aus.
    """
    print(Fore.CYAN + """
Befehle:
  msg <Benutzer> <Text>         - Sende eine Textnachricht an einen Kontakt
  img <Benutzer> <Pfad>         - Übertrage ein Bild an einen Kontakt
  who                           - Aktualisiere die Nutzerliste im lokalen Netzwerk
  contacts                      - Zeige alle bekannten Kontakte an
  history                       - Zeige den bisherigen Chatverlauf
  status <Text>                 - Setze deinen eigenen Status (z.B. 'Abwesend')
  dnd                           - Aktiviere/deaktiviere Nicht-Stören-Modus
  save                          - Speichere den bisherigen Chatverlauf in einer Datei
  reload                        - Lade die Konfiguration neu (z.B. nach Änderungen)
  help                          - Zeige diese Hilfe an
  leave                         - Verlasse den Chat und beende die Sitzung
""")

## Gibt alle neuen Nachrichten aus der UI-Queue farbig auf dem Terminal aus.
def watcher(ui_queue):
    """
    Gibt alle eingegangenen System- oder Chatnachrichten, die sich in der Queue befinden, farbig aus.

    @param ui_queue: Queue mit neuen Nachrichten
    """
    while True:
        while not ui_queue.empty():
            msg = ui_queue.get()
            if "fehler" in msg.lower():
                print(Fore.RED + msg)
            elif "bild" in msg.lower():
                print(Fore.MAGENTA + msg)
            elif "chat verlassen" in msg.lower():
                print(Fore.CYAN + msg)
            elif "gesendet" in msg.lower():
                print(Fore.GREEN + msg)
            else:
                print(Fore.WHITE + msg)
        time.sleep(0.1)

## Zeigt aktuelle Nutzerinformationen (Nickname, Status, DND) im Terminal an.
def print_status(handle, status, dnd):
    """
    Zeigt in einer farbigen Zeile an, unter welchem Nickname der Nutzer aktiv ist,
    welchen Status er gesetzt hat und ob der Nicht-stören-Modus aktiv ist.

    @param handle: Aktueller Nutzername 
    @param status: Aktueller Statuswert 
    @param dnd: DND-Modus (Nicht stören)
    """
    dnd_str = (Fore.RED + "🛑 Nicht stören") if dnd.value else (Fore.GREEN + "🟢 Erreichbar")
    print(
        f"{Fore.YELLOW}[{handle}{Style.RESET_ALL} | "
        f"{Fore.BLUE}Status: {status.value}{Style.RESET_ALL} | {dnd_str}{Fore.YELLOW}]"
    )

## Hauptfunktion für die farbige Kommandozeilensteuerung von Plauderkiste.
def start_cli(ui_queue, discovery_queue, network_queue, config, contacts, chat_history, dnd, status):
    """
    Startet die textbasierte, farbige Oberfläche des Plauderkiste-Chats.
    Nutzer können Kommandos eingeben, Nachrichten versenden und Systeminformationen einsehen.

    Die Funktion läuft in einer Schleife bis der Nutzer den Chat verlässt.

    @param ui_queue: Queue für neue System- und Chatnachrichten 
    @param discovery_queue: Queue für Kommandos an die Discovery-Komponente
    @param network_queue: Queue für Kommandos an das Netzwerkmodul 
    @param config: Konfiguration (dict), enthält Nutzername, Port, u.a.
    @param contacts: Gemeinsame Kontaktliste
    @param chat_history: Gemeinsame Chat-Historie 
    @param dnd: Status für Nicht-stören 
    @param status: Freitext-Statusanzeige
    @return: None
    """
    handle = config.get("handle", "Unbekannt")
    print(Fore.YELLOW + "╔═══════════════════════╗")
    print(Fore.YELLOW + "║   Plauderkiste Chat  ║")
    print(Fore.YELLOW + "╚═══════════════════════╝")
    print(Fore.GREEN + "Willkommen bei Plauderkiste – deinem privaten Chat!")
    print_help()

    threading.Thread(target=watcher, args=(ui_queue,), daemon=True).start()
    
    while True:
        # Ausgabe aller Systemnachrichten (Chat, Netzwerk, Fehler, etc.)
        ### watcher(ui_queue)
        # Statuszeile mit Nutzername, Status und DND
        print_status(handle, status, dnd)
        # Mini-Hinweis für Kommandos unter dem Prompt
        print(Fore.LIGHTBLACK_EX + "[help] für Kommandos.", end="")
        try:
            inp = input(Fore.GREEN + "\nPlauderkiste > " + Style.RESET_ALL).strip()
        except (KeyboardInterrupt, EOFError):
            print(Fore.CYAN + "\nBeenden...")
            break
        if not inp:
            continue
        parts = inp.strip().split(" ", 2)
        cmd = parts[0].lower()

        # Verarbeitung der wichtigsten Kommandos, weitere Details siehe Hilfetext
        if cmd == "help" or cmd == "?":
            print_help()
        elif cmd == "leave":
            # Nutzer verlässt den Chat sauber, benachrichtigt das Netzwerk
            discovery_queue.put(f"LEAVE {handle}")
            print(Fore.CYAN + "Du hast den Chat verlassen.")
            time.sleep(0.5)
            break
        elif cmd == "who":
            # Fordert eine aktuelle Liste aller erreichbaren Nutzer an
            discovery_queue.put("WHO")
        elif cmd == "contacts":
            discovery_queue.put("WHO")
            # Zeigt alle aktuell bekannten Kontakte und deren Adressen
            if contacts:
                print(Fore.CYAN + "Bekannte Kontakte:")
                for name, (ip, port) in contacts.items():
                    print(Fore.YELLOW + f"  {name} " + Fore.LIGHTBLACK_EX + f"@ {ip}:{port}")
            else:
                print(Fore.LIGHTBLACK_EX + "Keine Kontakte gespeichert. (Tipp: who ausführen)")
        elif cmd == "history":
            # Gibt den bisherigen Chatverlauf aus
            if chat_history:
                print(Fore.CYAN + "Chatverlauf:")
                for line in chat_history:
                    print(Fore.WHITE + line)
            else:
                print(Fore.LIGHTBLACK_EX + "Noch keine Nachrichten im Verlauf.")
        elif cmd == "status" and len(parts) > 1:
            # Ändert den Status des Nutzers (z.B. "Abwesend")
            status.value = parts[1]
            print(Fore.BLUE + f"Status gesetzt: {parts[1]}")
        elif cmd == "dnd":
            # Schaltet den Nicht-stören-Modus um (z.B. für Meetings)
            dnd.value = not dnd.value
            state = "aktiviert" if dnd.value else "deaktiviert"
            print(Fore.BLUE + f"Nicht-Stören-Modus {state}.")
        elif cmd == "save":
            # Speichert den Chatverlauf in eine lokale Textdatei
            from data_manager import save_history
            save_history(chat_history)
            print(Fore.GREEN + "Verlauf gespeichert (verlauf.txt).")
        elif cmd == "reload":
            # Lädt die Konfiguration neu, falls Einstellungen geändert wurden
            from data_manager import reload_config
            try:
                new_config = reload_config(config.get("config_path", "config.toml"))
                config.clear()
                config.update(new_config)
                print(Fore.GREEN + "Konfiguration neu geladen.")
            except Exception as e:
                print(Fore.RED + f"Fehler beim Reload: {e}")
        elif cmd == "msg" and len(parts) > 2:
            # Sendet eine Textnachricht an einen Kontakt
            recipient = parts[1]
            message = parts[2]
            if recipient not in contacts:
                print(Fore.RED + f"Empfänger {recipient} unbekannt. (Tipp: who ausführen)")
            else:
                network_queue.put(f"MSG {recipient} {message}")
                from data_manager import add_message
                add_message(chat_history, f"Du an {recipient}: {message}")
        elif cmd == "img" and len(parts) > 2:
            # Überträgt ein Bild an einen Kontakt
            recipient = parts[1]
            path = parts[2]
            if not os.path.exists(path):
                print(Fore.RED + "Dateipfad existiert nicht!")
                continue
            filename = os.path.basename(path)
            size = os.path.getsize(path)
            network_queue.put(f"IMG_SEND {recipient} {filename} {size}::{path}")
            from data_manager import add_message
            add_message(chat_history, f"[Bild an {recipient} gesendet: {filename}]")
            print(Fore.MAGENTA + f"Bild wird an {recipient} gesendet...")
        else:
            # Fehlermeldung für ungültige Kommandos
            print(Fore.RED + "Unbekannter oder unvollständiger Befehl (help für Übersicht).")
        time.sleep(0.1)
