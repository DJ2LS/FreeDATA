import serial.tools.list_ports
import helpers
import sys


def get_ports():

    serial_devices = []
    if sys.platform == 'win32':
        import list_ports_winreg
        ports = list_ports_winreg.comports(include_links=False)
    else:

        ports = serial.tools.list_ports.comports(include_links=False)

    for port, desc, hwid in ports:
        # calculate hex of hwid if we have unique names
        crc_hwid = helpers.get_crc_16(bytes(hwid, encoding="utf-8"))
        crc_hwid = crc_hwid.hex()
        description = f"{desc} [{crc_hwid}]"
        serial_devices.append(
            {"port": str(port), "description": str(description)}
        )
    return serial_devices
