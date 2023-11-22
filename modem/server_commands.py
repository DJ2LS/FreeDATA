from queues import DATA_QUEUE_TRANSMIT
import base64
import structlog
import threading
from random import randrange
log = structlog.get_logger("COMMANDS")

def cqcqcq():
    try:
        DATA_QUEUE_TRANSMIT.put(["CQ"])
        return
    except Exception as err:
        log.warning("[CMD] error while transmiting CQ", e=err)

def ping_ping(dxcall):
    try:
        DATA_QUEUE_TRANSMIT.put(["PING", None, dxcall])
        
    except Exception as err:
        log.warning(
            "[CMD] PING command execution error", e=err
        )

def modem_send_test_frame():

    log.info(
        "[CMD] Send test frame"
    )
    DATA_QUEUE_TRANSMIT.put(["SEND_TEST_FRAME"])
    
def modem_arq_send_raw(mycallsign, dxcallsign, payload, arq_uuid = "no-uuid"):

    # wait some random time
    threading.Event().wait(randrange(5, 25, 5) / 10.0)

    base64data = payload

    if len(base64data) % 4:
        raise TypeError

    binarydata = base64.b64decode(base64data)

    DATA_QUEUE_TRANSMIT.put(
        ["ARQ_RAW", binarydata, arq_uuid, mycallsign, dxcallsign]
    )


def modem_fec_transmit(mode, wakeup, base64data, mycallsign = None):
    log.info(
        "[CMD] Send fec frame"
    )
    if len(base64data) % 4:
        raise TypeError
    payload = base64.b64decode(base64data)

    DATA_QUEUE_TRANSMIT.put(["FEC", mode, wakeup, payload, mycallsign])

def modem_fec_is_writing(mycallsign):
    try:
        DATA_QUEUE_TRANSMIT.put(["FEC_IS_WRITING", mycallsign])
    except Exception as err:
        log.warning(
            "[SCK] Send fec frame command execution error",
            e=err,
        )

