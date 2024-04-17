import re


def validate_remote_config(config):
    if not config:
        return

    mygrid = config["STATION"]["mygrid"]
    if len(mygrid) != 6:
        raise ValueError(f"Gridsquare must be 6 characters!")

    return True

def validate_freedata_callsign(callsign):
    #regexp = "^[a-zA-Z]+\d+\w+-\d{1,2}$"
    regexp = "^[A-Za-z0-9]{1,7}-[0-9]{1,3}$" # still broken - we need to allow all ssids form 0 - 255
    return re.compile(regexp).match(callsign) is not None

def validate_message_attachment(attachment):
    for field in ['name', 'type', 'data']:
        if field not in attachment:
            raise ValueError(f"Attachment missing '{field}'")

        # check for content length, except type
        # there are some files out there, don't having a mime type
        if len(attachment[field]) < 1 and field not in ["type"]:
            raise ValueError(f"Attachment has empty '{field}'")
