import yaml


def validate_credentials(file_path: str) -> bool:
    """
    Validiert die Struktur und den Inhalt der YAML-Datei mit Zugangsdaten.

    :param file_path: Pfad zur YAML-Datei.
    :return: True, wenn die Datei gültig ist, wirft andernfalls ValueError.
    """
    # YAML-Datei laden
    with open(file_path, "r") as file:
        try:
            data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ValueError(f"Ungültige YAML-Syntax: {e}")
    if not data:
        raise ValueError("Die YAML-Datei ist leer.")

    # Überprüfen, ob Hauptschlüssel vorhanden sind
    if "pacs" not in data or "api" not in data:
        raise ValueError("Fehlende erforderliche Schlüssel 'pacs' oder 'api' in der YAML-Datei.")

    # Validierung von `pacs`
    if not isinstance(data["pacs"], dict):
        raise ValueError("'pacs' sollte ein Wörterbuch (dict) im Format pac_id:passwort sein.")

    for pac_key, pac_value in data["pacs"].items():
        if not (isinstance(pac_key, str) and isinstance(pac_value, str)):
            raise ValueError(
                f"Ungültiger Eintrag in 'pacs': '{pac_key}: {pac_value}' (Schlüssel und Werte müssen Strings sein).")
        if not pac_key.strip() or not pac_value.strip():
            raise ValueError(
                f"Ungültiger Eintrag in 'pacs': '{pac_key}: {pac_value}' (Schlüssel und Werte dürfen nicht leer sein).")

    # Validierung von `api`
    if not isinstance(data["api"], list):
        raise ValueError("'api' sollte eine Liste von Wörterbüchern sein.")

    for api_entry in data["api"]:
        if not isinstance(api_entry, dict):
            raise ValueError(f"Ungültiger Eintrag in 'api': {api_entry} (dieser Eintrag sollte ein Wörterbuch sein).")

        # Überprüfen, ob erforderliche Schlüssel in jedem `api`-Eintrag vorhanden sind
        if "key" not in api_entry or "pacs" not in api_entry:
            raise ValueError(f"Fehlender Schlüssel 'key' oder 'pacs' in API-Eintrag: {api_entry}.")

        # Validierung des `key`
        if not isinstance(api_entry["key"], str) or not api_entry["key"].strip():
            raise ValueError(
                f"Ungültiger 'key' im API-Eintrag: {api_entry['key']} (Schlüssel sollte ein nicht-leerer String sein).")

        # Validierung des `pacs`-Feldes im Eintrag
        pacs = api_entry["pacs"]
        if isinstance(pacs, list):
            if not all(isinstance(p, str) and p.strip() for p in pacs):
                raise ValueError(
                    f"Die Liste in 'pacs' im API-Eintrag enthält ungültige Werte: {pacs} (alle Werte sollten nicht-leere Strings sein).")
            for pac in pacs:
                if pac not in data["pacs"]:
                    raise ValueError(f"Unbekannter 'pacs'-Wert '{pac}' im API-Eintrag: {api_entry}.")
        elif isinstance(pacs, str):
            if not pacs.strip():
                raise ValueError("Ungültiger 'pacs'-Wert im API-Eintrag (sollte ein nicht-leerer String sein).")
            if pacs not in data["pacs"]:
                raise ValueError(f"Unbekannter 'pacs'-Wert '{pacs}' im API-Eintrag: {api_entry}.")
        else:
            raise ValueError(
                f"Ungültiger Typ für 'pacs' im API-Eintrag: {pacs} (sollte ein String oder eine Liste von Strings sein).")

        # Validierung von `server`
        if not isinstance(data["server"], dict):
            raise ValueError(
                "'server' sollte ein Wörterbuch mit den Schlüsseln 'host', 'port', 'log-level' und 'worker' sein.")

        # Erwartete Schlüssel in `server`
        required_server_keys = ["host", "port", "log-level", "worker"]
        for key in required_server_keys:
            if key not in data["server"]:
                raise ValueError(f"Fehlender erforderlicher Schlüssel '{key}' in 'server'.")


    # Validierung der Server-Felder
    server = data["server"]
    # Host muss ein String sein
    if not isinstance(server["host"], str) or not server["host"].strip():
        raise ValueError(f"'host' in 'server' sollte ein nicht-leerer String sein (z. B. '127.0.0.1').")

    # Port muss eine Ganzzahl im gültigen Bereich sein
    if not isinstance(server["port"], int) or not (1 <= server["port"] <= 65535):
        raise ValueError(
            f"'port' in 'server' sollte eine Ganzzahl zwischen 1 und 65535 sein (aktuell: {server['port']}).")

    # Log-Level muss ein gültiger String sein
    if not isinstance(server["log-level"], str) or server["log-level"] not in ["error", "info", "debug"]:
        raise ValueError(
            f"'log-level' in 'server' sollte einer der folgenden Werte sein: 'error', 'info', 'debug'.")

    # Worker muss eine positive Ganzzahl sein
    if not isinstance(server["worker"], int) or server["worker"] <= 0:
        raise ValueError(f"'worker' in 'server' sollte eine positive Ganzzahl sein (aktuell: {server['worker']}).")


    print("Die YAML-Datei ist gültig!")
    return True


if __name__ == "__main__":
    try:
        validate_credentials("env.yaml")
    except ValueError as e:
        print(f"Validierung fehlgeschlagen: {e}")
