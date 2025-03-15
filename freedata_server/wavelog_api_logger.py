import requests
import threading
import structlog


def send_wavelog_qso_data(config, event_manager, wavelog_data):
    """
    Sends wavelog QSO data to the specified server via API call.

    Parameters:
    server_host:port (str)
    server_api_key (str)
    wavelog_data (str): wavelog-formatted ADIF QSO data.
    """

    log = structlog.get_logger()

    # If False then exit the function
    wavelog = config['QSO_LOGGING'].get('enable_adif_wavelog', 'False')

    if not wavelog:
        return  # exit as we don't want to log Wavelog

    wavelog_host = config['QSO_LOGGING'].get('adif_wavelog_host', 'http://localhost/')
    wavelog_api_key = config['QSO_LOGGING'].get('adif_wavelog_api_key', '')

    # check if the last part in the HOST URL from the config is correct
    if wavelog_host.endswith("/"):
        url = wavelog_host + "index.php/api/qso"
    else:
        url = wavelog_host + "/" + "index.php/api/qso"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    data = {
        "key": wavelog_api_key,
        "station_profile_id": "1",
        "type": "adif",
        "string": wavelog_data
    }

    def send_api():
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raise an error for bad status codes
            log.info(f"[CHAT] Wavelog API: {wavelog_data}")
            event_manager.freedata_logging(type="wavelog", status=True, message=f"QSO added")
        except requests.exceptions.RequestException as e:
            log.warning(f"[WAVELOG ADIF API EXCEPTION]: {e}")
            #FIXME format the output to get the actual error
            error_text = f"{e}"

            if error_text.startswith("401 Client Error:") or error_text.startswith("Failed to parse:"):
                error_first_line, _, remaining_string = error_text.partition(": ")
                error_second_line, _, last_part = remaining_string.partition((": "))
                error_formated = f"{error_first_line}<br>{error_second_line}<br>{last_part}"

            elif error_text.startswith("HTTPConnectionPool"):
                error_first_line, _, remaining_string = error_text.partition(": ")
                error_second_line, _, second_part = remaining_string.partition((": "))
                error_third_line, _, last_part = second_part.partition(("(Caused by NewConnectionError('"))
                error_formated = f"{error_first_line}<br>{error_second_line}<br>{error_third_line}<br>{last_part.rstrip("'))")}"

            else:
                error_formated = f"{e}"

            event_manager.freedata_logging(type="wavelog", status=False, message=f"{error_formated}")

    # Run the API call in a background thread to avoid blocking the main thread
    thread = threading.Thread(target=send_api, daemon=True)
    thread.start()