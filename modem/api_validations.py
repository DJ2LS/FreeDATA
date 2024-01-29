import re

def validate_freedata_callsign(callsign):
    #regexp = "^[a-zA-Z]+\d+\w+-\d{1,2}$"
    regexp = "^[A-Za-z0-9]{1,7}-[0-9]$"
    return re.compile(regexp).match(callsign) is not None

def validate_message_attachment(attachment):
    for field in ['name', 'type', 'data']:
        if field not in attachment:
            raise ValueError(f"Attachment missing '{field}'")
        if len(attachment[field]) < 1:
            raise ValueError(f"Attachment has empty '{field}'")
