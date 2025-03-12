import serial.tools.list_ports
import helpers
import sys


def get_ports():
    """Retrieves a list of available serial ports.

    This function retrieves a list of available serial ports on the system,
    including their names and descriptions. On Windows, it uses a specific
    registry lookup to get detailed port information. For other platforms,
    it uses the standard serial.tools.list_ports function. It calculates a
    CRC-16 checksum of the hardware ID (HWID) for each port and appends it
    to the description to ensure unique entries.

    Windows part taken from https://github.com/pyserial/pyserial/pull/70 as a temporary fix

    Returns:
        list: A list of dictionaries, where each dictionary represents a
        serial port and contains 'port' (str) and 'description' (str) keys.
    """

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
