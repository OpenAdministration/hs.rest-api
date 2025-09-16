import yaml

def validate_credentials(file_path: str) -> bool:
    """
    Validates the structure and content of the credentials YAML file.

    :param file_path: Path to the YAML file.
    :return: True if the file is valid, raises ValueError otherwise.
    """
    # Load the YAML file
    with open(file_path, "r") as file:
        try:
            data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}")
    if not data:
        raise ValueError("The YAML file is empty")

    # Validate main keys exist
    if "pacs" not in data or "api" not in data:
        raise ValueError("Missing required keys 'pacs' or 'api' in YAML.")

    # Validate `pacs`
    if not isinstance(data["pacs"], dict):
        raise ValueError("'pacs' should be a dictionary key:value(s).")

    for pac_key, pac_value in data["pacs"].items():
        if not isinstance(pac_key, str) or not isinstance(pac_value, str):
            raise ValueError(f"Invalid 'pacs' entry: '{pac_key}: {pac_value}' (should be string:string).")

    # Validate `api`
    if not isinstance(data["api"], list):
        raise ValueError("'api' should be a list of dictionaries.")

    for api_entry in data["api"]:
        if not isinstance(api_entry, dict):
            raise ValueError(f"Invalid 'api' entry: {api_entry} (should be a dictionary).")

        # Check required keys in `api` entries
        if "key" not in api_entry or "pacs" not in api_entry:
            raise ValueError(f"Missing 'key' or 'pacs' in API entry: {api_entry}.")

        if not isinstance(api_entry["key"], str) or not api_entry["key"]:
            raise ValueError(f"Invalid 'key' in API entry: {api_entry['key']} (should be a non-empty string).")

        # Validate `pacs` in the API entry
        pacs = api_entry["pacs"]
        if isinstance(pacs, list):
            if not all(isinstance(p, str) for p in pacs):
                raise ValueError(f"Invalid 'pacs' list in API entry: {pacs} (should be a list of strings).")
            for pac in pacs:
                if pac not in data["pacs"]:
                    raise ValueError(f"Unknown 'pacs' reference '{pac}' in API entry: {api_entry}.")
        elif isinstance(pacs, str):
            if pacs not in data["pacs"]:
                raise ValueError(f"Unknown 'pacs' reference '{pacs}' in API entry: {api_entry}.")
        else:
            raise ValueError(f"Invalid type for 'pacs' in API entry: {pacs} (should be string or list of strings).")

    print("YAML file is valid!")
    return True


try:
    validate_credentials("credentials.yaml")
except ValueError as e:
    print(f"Validation failed: {e}")