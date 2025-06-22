"""
@file data_manager.py
@brief Modul zur Verwaltung von Chatverlauf und Konfiguration im Peer-to-Peer-Chat "Plauderkiste".

Dieses Modul übernimmt das Speichern und Nachladen von Chatverläufen sowie das Nachladen der
Konfiguration zur Laufzeit. Alle Funktionen sind als Einzeloperationen ohne Klassen implementiert.

Das Datenmanagement sorgt dafür, dass Nutzer jederzeit ihren bisherigen Verlauf sichern und
wiederherstellen können. Außerdem kann die Konfiguration (z.B. Nutzername oder Port) zur Laufzeit neu geladen werden.

@author Mahir Ahmad, Sena Akpolad, Onur Ücelehan, Meriam Lakhrissi, Najiba Sulaimankhel
@date 2025
"""

import toml

## Speichert den aktuellen Chatverlauf in eine Textdatei.
def save_history(chat_history, filename="verlauf.txt"):
    """
    Speichert alle bisher gesendeten und empfangenen Nachrichten in eine Textdatei.

    @param chat_history: Liste aller bisherigen Chat-Nachrichten
    @param filename: Name der Zieldatei (Standard: "verlauf.txt")
    @return: None
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for line in chat_history:
                f.write(line + "\n")
    except Exception as e:
        print(f"[Fehler] Verlauf konnte nicht gespeichert werden: {e}")

## Fügt eine neue Nachricht dem Chatverlauf hinzu.
def add_message(chat_history, msg):
    """
    Hängt eine neue Nachricht an die Chat-Historie an.

    @param chat_history: Chatverlauf als Manager Liste
    @param msg: Text der neuen Nachricht
    @return: None
    """
    chat_history.append(msg)

## Lädt die Konfiguration aus einer TOML-Datei neu.
def reload_config(config_path):
    """
    Lädt alle Einstellungen (z.B. Nickname, Port, Bildordner) aus der angegebenen Konfigurationsdatei nach.

    @param config_path: Pfad zur TOML-Konfigurationsdatei
    @return: config: Dict mit neuen Konfigurationseinstellungen
    """
    try:
        config = toml.load(config_path)
        config["config_path"] = config_path
        return config
    except Exception as e:
        print(f"[Fehler] Konfiguration konnte nicht neu geladen werden: {e}")
        return {}
