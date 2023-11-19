from queues import DATA_QUEUE_TRANSMIT
import base64
import structlog
log = structlog.get_logger("COMMANDS")

def cqcqcq(data):
    try:
        DATA_QUEUE_TRANSMIT.put(["CQ"])
        return
    except Exception as err:
        log.warning("[CMD] error while transmiting CQ", e=err, command=data)

def ping_ping(data):
    try:
        dxcallsign = data["dxcall"]
        if not str(dxcallsign).strip():
            return
        DATA_QUEUE_TRANSMIT.put(["PING", None, dxcallsign])
        
    except Exception as err:
        log.warning(
            "[CMD] PING command execution error", e=err, command=data
        )

def beacon(data, interval=300):
    beacon_state = data['enabled'] in [True]
    
    log.info(
        "[CMD] Changing beacon state", state=beacon_state
    )
    if (beacon_state):
        DATA_QUEUE_TRANSMIT.put(["BEACON", interval, beacon_state])
    else:
        DATA_QUEUE_TRANSMIT.put(["BEACON", beacon_state])
def modem_send_test_frame():

    log.info(
        "[CMD] Send test frame"
    )
    DATA_QUEUE_TRANSMIT.put(["SEND_TEST_FRAME"])

def modem_fec_transmit(data):
    log.info(
        "[CMD] Send fec frame"
    )
    mode = data["mode"]
    wakeup = data["wakeup"]
    base64data = data["payload"]
    if len(base64data) % 4:
        raise TypeError
    payload = base64.b64decode(base64data)

    try:
        mycallsign = data["mycallsign"]
    except:
        mycallsign = None

    DATA_QUEUE_TRANSMIT.put(["FEC", mode, wakeup, payload, mycallsign])

def modem_fec_is_writing(data):
    try:
        mycallsign = data["mycallsign"]
        DATA_QUEUE_TRANSMIT.put(["FEC_IS_WRITING", mycallsign])
    except Exception as err:
        log.warning(
            "[SCK] Send fec frame command execution error",
            e=err,
            command=data,
        )

