import socket



def send_adif_qso_data(config, adif_data):
    """
    Sends ADIF QSO data to the specified server via UDP.

    Parameters:
    server_ip (str): IP address of the server.
    server_port (int): Port of the server.
    adif_data (str): ADIF-formatted QSO data.
    """
    adif_log_host = config['MESSAGES'].get('adif_log_host', '127.0.0.1')
    adif_log_port = int(config['MESSAGES'].get('adif_log_port', '2237'))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Send the ADIF data to the server
        sock.sendto(adif_data.encode('utf-8'), (adif_log_host, adif_log_port))
        print(f"ADIF QSO data sent to {adif_log_host}:{adif_log_port}", adif_data.encode('utf-8'))
    except Exception as e:
        print(f"Error sending ADIF data: {e}")
    finally:
        sock.close()

