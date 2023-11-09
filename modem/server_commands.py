from queues import DATA_QUEUE_TRANSMIT
import structlog
log = structlog.get_logger("COMMANDS")

def cqcqcq(self):
    DATA_QUEUE_TRANSMIT.put(["CQ"])

def ping_ping(data):
    try:
        dxcallsign = data["dxcallsign"]
        if not str(dxcallsign).strip():
            return
        DATA_QUEUE_TRANSMIT.put(["PING", None, dxcallsign])
        
    except Exception as err:
        log.warning(
            "[CMD] PING command execution error", e=err, command=data
        )

def beacon(data):
    beacon_state = False
    if data['enabled'] in ['True']:
        beacon_state = True
    #Beacon.beacon_state = beacon_state
    log.info(
        "[CMD] Changing beacon state", state=beacon_state
    )
    DATA_QUEUE_TRANSMIT.put(["BEACON", 300, beacon_state])