"""
This module provides a utility function to send ADIF-formatted QSO data over UDP.
It reads configuration settings from a provided dictionary to determine if ADIF UDP logging is enabled,
and if so, retrieves the destination host and port. Using a UDP socket, it encodes the ADIF data as UTF-8 and
sends it to the specified server.
"""


import socket
import structlog

def send_adif_qso_data(config, adif_data):
    """
    Sends ADIF QSO data to the specified server via UDP.

    Parameters:
    server_ip (str): IP address of the server.
    server_port (int): Port of the server.
    adif_data (str): ADIF-formatted QSO data.
    """

    log = structlog.get_logger()

    # If False then exit the function
    adif = config['QSO_LOGGING'].get('enable_adif_udp', 'False')

    if not adif:
        return  # exit as we don't want to log ADIF UDP

    adif_log_host = config['QSO_LOGGING'].get('adif_udp_host', '127.0.0.1')
    adif_log_port = int(config['QSO_LOGGING'].get('adif_udp_port', '2237'))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:

        # Send the ADIF data to the server
        sock.sendto(adif_data.encode('utf-8'), (adif_log_host, adif_log_port))
        log.info(f"[CHAT] ADIF QSO data sent to: {adif_log_host}:{adif_log_port} {adif_data.encode('utf-8')}")
    except Exception as e:
        log.info(f"[CHAT] Error sending ADIF data: {e}")
    finally:
        sock.close()
