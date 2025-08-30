""" This module provides a set of validation functions used within the FreeData system. It includes:

validate_remote_config: Ensures that a remote configuration is present.
validate_freedata_callsign: Checks if a callsign conforms to a defined pattern. Note: The current regular expression allows 1 to 7 alphanumeric characters followed by a hyphen and 1 to 3 digits, but it may require adjustment to fully support all SSID values from 0 to 255.
validate_message_attachment: Validates that a message attachment (represented as a dictionary) includes the required fields ('name', 'type', 'data') and that the 'name' and 'data' fields are not empty.

"""


import re

GRID_RE = re.compile(r'^[A-Ra-r]{2}[0-9]{2}([A-Xa-x]{2})?$')
CALL_RE = re.compile(r'^[A-Z0-9]{1,7}(-[0-9]{1,3})?$', re.IGNORECASE)


def validate_gridsquare(value: str):
    """Validate and normalize a Maidenhead grid locator (4 or 6 characters)."""
    if not value or not isinstance(value, str):
        return None
    raw = value.strip()
    if not GRID_RE.match(raw):
        return None
    return raw[0:2].upper() + raw[2:4] + (raw[4:6].lower() if len(raw) == 6 else "")


def validate_freedata_callsign(value: str):
    """
    Validate a ham radio callsign.

    Rules:
      - Up to 7 alphanumeric characters for the base.
      - Optional -SSID with a number 0–255.
    """
    if not value or not isinstance(value, str):
        return None
    raw = value.strip().upper()
    match = CALL_RE.fullmatch(raw)
    if not match:
        return None

    if "-" in raw:
        base, ssid = raw.split("-", 1)
        try:
            ssid_num = int(ssid)
            if 0 <= ssid_num <= 255:
                return f"{base}-{ssid_num}"
            return None
        except ValueError:
            return None
    return raw


def validate_remote_config(config: dict) -> bool:
    """
    Validate 'mycall' and 'mygrid' in STATION.
    Returns False if either one is invalid.
    """
    if not config or "STATION" not in config:
        return False

    station = config["STATION"]

    call = validate_freedata_callsign(station.get("mycall"))
    grid = validate_gridsquare(station.get("mygrid"))

    if not call or not grid:
        return False

    # Write back normalized values
    station["mycall"] = call
    station["mygrid"] = grid
    return True


def validate_message_attachment(attachment):
    """Validates a message attachment.

    This function checks if the attachment includes the required fields ('name', 'type', 'data')
    and that the 'name' and 'data' fields are not empty. It raises a ValueError if
    any of these conditions are not met. Note: The 'type' field is not checked for
    emptiness as some files may not have a MIME type.

    Args:
        attachment: The message attachment to validate (represented as a dictionary).

    Raises:
        ValueError: If the attachment is missing a required field or if the 'name' or 'data' field is empty.
    """
    for field in ['name', 'type', 'data']:
        if field not in attachment:
            raise ValueError(f"Attachment missing '{field}'")

        # check for content length, except type
        # there are some files out there, don't having a mime type
        if len(attachment[field]) < 1 and field not in ["type"]:
            raise ValueError(f"Attachment has empty '{field}'")
