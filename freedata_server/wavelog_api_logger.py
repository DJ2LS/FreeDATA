import requests
import re


def send_wavelog_qso_data(config, wavelog_data):
    """
    Sends wavelog QSO data to the specified server via API call.

    Parameters:
    server_host:port (str)
    server_api_key (str)
    wavelog_data (str): wavelog-formatted ADIF QSO data.
    """

    # If False then exit the function
    wavelog = config['MESSAGES'].get('wavelog_enable', 'False')

    if not wavelog:
        return # exit as we don't want to log Wavelog

    wavelog_host = config['MESSAGES'].get('wavelog_host', 'http://localhost:8086')
    wavelog_api_key = config['MESSAGES'].get('wavelog_api_key', '')

    url = wavelog_host + "/index.php/api/qso"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # If there is no gridsquare fix this so that it follows the ADIF standard.
    wrong_grids = [
        r"<GRIDSQUARE:4>----",
        r"<GRIDSQUARE:1> ",
        r"<GRIDSQUARE:3>N/A"
    ]

    for grids in wrong_grids:
        if re.search(grids, wavelog_data):
            wavelog_data = re.sub(grids, "<GRIDSQUARE:0>", wavelog_data)
            break

#    wavelog_data = re.sub(r"<GRIDSQUARE:4>----", "<GRIDSQUARE:0>", wavelog_data)

    data = {
        "key": wavelog_api_key,
        "station_profile_id": "1",
        "type": "adif",
        "string": wavelog_data
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an error for bad status codes
        print("Response:", response.json())  # Print the JSON response from the server
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
