import re

def validate_freedata_callsign(callsign):
    regexp = "^[a-zA-Z]+\d+\w+-\d{1,2}$"
    return re.compile(regexp).match(callsign) is not None
