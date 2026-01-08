import serial
import pynmea2
import serial_ports
from maidenhead import latlon_to_maidenhead

def extract_lat_lon_alt(msg):
    lat = getattr(msg, 'latitude', None)
    lon = getattr(msg, 'longitude', None)
    alt = getattr(msg, 'altitude', None)
    maidenhead = latlon_to_maidenhead(lat,lon, precision=8)
    return lat, lon, alt, maidenhead

def read_gps(port='/dev/ttyUSB0', baudrate=9600, wanted_type='GGA'):
    with serial.Serial(port, baudrate, timeout=1) as ser:
        while True:
            line = ser.readline().decode('ascii', errors='ignore').strip()
            if not line.startswith('$'):
                continue
            try:
                msg = pynmea2.parse(line)

                if msg.sentence_type != wanted_type:
                    continue  # Nur gewählten Typ weiterverarbeiten

                lat, lon, alt, maidenhead = extract_lat_lon_alt(msg)

                print(f"Satz: {wanted_type} | Talker: {msg.talker}")
                if lat is not None and lon is not None:
                    print(f"Latitude: {lat}, Longitude: {lon}, Altitude: {alt} m, Locator: {maidenhead}")
                else:
                    print("No Lat/Lon/Alt")

                print("-" * 50)
            except pynmea2.ParseError:
                continue



if __name__ == '__main__':
    ports = serial_ports.get_ports()
    print(ports)
    read_gps('/dev/cu.usbmodem1444206')
