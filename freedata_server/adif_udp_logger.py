import socket
import structlog
import threading

def send_adif_qso_data(config, event_manager, adif_data):
    """
    Sends ADIF QSO data to the specified server via UDP in a non-blocking manner.

    Parameters:
    config (dict): Configuration settings.
    event_manager: An event manager to log success/failure.
    adif_data (str): ADIF-formatted QSO data.
    """
    log = structlog.get_logger()

    # Check if ADIF UDP logging is enabled
    adif = config['QSO_LOGGING'].get('enable_adif_udp', 'False')
    if not adif:
        return  # Exit if ADIF UDP logging is disabled

    adif_log_host = config['QSO_LOGGING'].get('adif_udp_host', '127.0.0.1')
    adif_log_port = int(config['QSO_LOGGING'].get('adif_udp_port', '2237'))

    def send_thread():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set a timeout of 3 seconds to avoid blocking indefinitely
        sock.settimeout(3)

        callsign_start = adif_data.find(f">") + 1
        callsign_end = adif_data.find(f"<QSO_DATE", callsign_start)
        call_value = adif_data[callsign_start:callsign_end]

        try:
            sock.sendto(adif_data.encode('utf-8'), (adif_log_host, adif_log_port))
            log.info(f"[CHAT] ADIF QSO data sent to: {adif_log_host}:{adif_log_port}")
            event_manager.freedata_logging(type="udp", status=True, message=f" {call_value} ")

        except socket.timeout:
            log.info(f"[CHAT] Timeout occurred sending ADIF data to {adif_log_host}:{adif_log_port}")
            event_manager.freedata_logging(type="udp", status=True, message=f" {call_value} ")
        except Exception as e:
            log.info(f"[CHAT] Error sending ADIF data: {e}")
            event_manager.freedata_logging(type="udp", status=True, message=f" {call_value} ")

        finally:
            sock.close()

    # Run the sending function in a separate thread
    thread = threading.Thread(target=send_thread, daemon=True)
    thread.start()
