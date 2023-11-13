import serial.tools.list_ports
import crcengine

def get_ports():
    crc_algorithm = crcengine.new("crc16-ccitt-false")  # load crc8 library

    serial_devices = []
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in ports:
        # calculate hex of hwid if we have unique names
        crc_hwid = crc_algorithm(bytes(hwid, encoding="utf-8"))
        crc_hwid = crc_hwid.to_bytes(2, byteorder="big")
        crc_hwid = crc_hwid.hex()
        description = f"{desc} [{crc_hwid}]"
        serial_devices.append(
            {"port": str(port), "description": str(description)}
        )
    return serial_devices
