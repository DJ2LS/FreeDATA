""" This module provides a set of validation functions used within the FreeData system. It includes:

validate_remote_config: Ensures that a remote configuration is present.
validate_freedata_callsign: Checks if a callsign conforms to a defined pattern. Note: The current regular expression allows 1 to 7 alphanumeric characters followed by a hyphen and 1 to 3 digits, but it may require adjustment to fully support all SSID values from 0 to 255.
validate_message_attachment: Validates that a message attachment (represented as a dictionary) includes the required fields ('name', 'type', 'data') and that the 'name' and 'data' fields are not empty.

"""


import re

def validate_remote_config(config):
    """Validates the presence of a remote configuration.

    This function checks if a remote configuration is present.

    Args:
        config: The configuration to validate.

    Returns:
        True if the configuration is present, None otherwise.
    """
    if not config:
        return
    return True

def validate_freedata_callsign(callsign):
    """Validates a FreeData callsign.

    This function checks if a given callsign conforms to the defined pattern.
    Currently, the regular expression allows 1 to 7 alphanumeric characters
    followed by a hyphen and 1 to 3 digits.  Note: This may require adjustment
    to fully support all SSID values from 0 to 255.

    Args:
        callsign: The callsign to validate.

    Returns:
        True if the callsign is valid, False otherwise.
    """
    #regexp = "^[a-zA-Z]+\d+\w+-\d{1,2}$"
    regexp = "^[A-Za-z0-9]{1,7}-[0-9]{1,3}$" # still broken - we need to allow all ssids form 0 - 255
    return re.compile(regexp).match(callsign) is not None

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
