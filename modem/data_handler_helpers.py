from modem_frametypes import FRAME_TYPE as FR_TYPE
import threading
from codec2 import FREEDV_MODE
from queues import MODEM_TRANSMIT_QUEUE
import ujson as json


def enqueue_frame_for_tx(
        frame_to_tx,  # : list[bytearray], # this causes a crash on python 3.7
        c2_mode=FREEDV_MODE.sig0.value,
        copies=1,
        repeat_delay=0,
) -> None:
    """
    Send (transmit) supplied frame to Modem

    :param frame_to_tx: Frame data to send
    :type frame_to_tx: list of bytearrays
    :param c2_mode: Codec2 mode to use, defaults to datac13
    :type c2_mode: int, optional
    :param copies: Number of frame copies to send, defaults to 1
    :type copies: int, optional
    :param repeat_delay: Delay time before sending repeat frame, defaults to 0
    :type repeat_delay: int, optional
    """
    frame_type = FR_TYPE(int.from_bytes(frame_to_tx[0][:1], byteorder="big")).name
    #log.debug("[Modem] enqueue_frame_for_tx", c2_mode=FREEDV_MODE(c2_mode).name, data=frame_to_tx,
                   type=frame_type)

    MODEM_TRANSMIT_QUEUE.put([c2_mode, copies, repeat_delay, frame_to_tx])

    # Wait while transmitting
    while states.is_transmitting:
        threading.Event().wait(0.01)

def send_data_to_socket_queue(**jsondata):
    """
    Send information to the UI via JSON and the sock.SOCKET_QUEUE.

    Args:
      Dictionary containing the data to be sent, in the format:
      key=value, for each item. E.g.:
        send_data_to_socket_queue(
            freedata="modem-message",
            arq="received",
            status="success",
            uuid=transmission_uuid,
            timestamp=timestamp,
            mycallsign=str(mycallsign, "UTF-8"),
            dxcallsign=str(dxcallsign, "UTF-8"),
            dxgrid=str(dxgrid, "UTF-8"),
            data=base64_data,
        )
    """

    # add mycallsign and dxcallsign to network message if they not exist
    # and make sure we are not overwrite them if they exist

    """
    try:
        if "mycallsign" not in jsondata:
            jsondata["mycallsign"] = str(mycallsign, "UTF-8")
        if "dxcallsign" not in jsondata:
            jsondata["dxcallsign"] = str(dxcallsign, "UTF-8")
    except Exception as e:
        log.debug("[Modem] error adding callsigns to network message", e=e)
    """
    # run json dumps
    json_data_out = json.dumps(jsondata)

    log.debug("[Modem] send_data_to_socket_queue:", jsondata=json_data_out)
    # finally push data to our network queue
    # sock.SOCKET_QUEUE.put(json_data_out)
    event_queue.put(json_data_out)