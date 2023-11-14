import configparser
import structlog
import json

class CONFIG:
    """
    CONFIG class for handling with config files

    """

    def __init__(self, configfile: str):
        # set up logger
        self.log = structlog.get_logger("CONFIG")

        # init configparser
        self.config = configparser.ConfigParser(inline_comment_prefixes="#", allow_no_value=True)
        
        try:
            self.config_name = configfile
        except Exception:
            self.config_name = "config.ini"

        self.log.info("[CFG] config init", file=self.config_name)

        # check if config file exists
        self.config_exists()

    def config_exists(self):
        """
        check if config file exists
        """
        try:
            return bool(self.config.read(self.config_name, None))
        except Exception as configerror:
            self.log.error("[CFG] logfile init error", e=configerror)
            return False

    # Validates config data
    def validate_network_settings(self, data):
        if 'modemport' in data:
            if not isinstance(data['modemport'], int):
                raise ValueError("'modemport' in 'NETWORK' must be an integer.")

    def validate_station_settings(self, data):
        for setting in ['mycall', 'mygrid']:
            if setting in data and not data[setting]:
                raise ValueError(f"'{setting}' in 'STATION' cannot be empty.")
        if 'ssid_list' in data and not isinstance(data['ssid_list'], list):
            raise ValueError("'ssid_list' in 'STATION' needs to be a list.")

    def validate_audio_settings(self, data):
        for setting in ['input_device', 'output_device']:
            if setting in data and not isinstance(data[setting], str):
                raise ValueError(f"'{setting}' in 'AUDIO' must be a string.")
        for setting in ['rx_audio_level', 'tx_audio_level']:
            if setting in data and not isinstance(data[setting], int):
                raise ValueError(f"'{setting}' in 'AUDIO' must be an integer.")

    def validate_radio_settings(self, data):
        if 'radioport' in data and not (data['radioport'] is None or isinstance(data['radioport'], int)):
            raise ValueError("'radioport' in 'RADIO' must be None or an integer.")

    def validate_tci_settings(self, data):
        if 'tci_ip' in data and not isinstance(data['tci_ip'], str):
            raise ValueError("'tci_ip' in 'TCI' must be a string.")
        if 'tci_port' in data and not isinstance(data['tci_port'], int):
            raise ValueError("'tci_port' in 'TCI' must be an integer.")

    def validate_modem_settings(self, data):
        for setting in ['enable_fft', 'enable_fsk', 'enable_low_bandwidth_mode', 'respond_to_cq', 'enable_scatter']:
            if setting in data and not isinstance(data[setting], bool):
                raise ValueError(f"'{setting}' in 'MODEM' must be a boolean.")
        for setting in ['tuning_range_fmax', 'tuning_range_fmin', 'rx_buffer_size', 'tx_delay']:
            if setting in data and not isinstance(data[setting], int):
                raise ValueError(f"'{setting}' in 'MODEM' must be an integer.")

    def validate_mesh_settings(self, data):
        if 'enable_protocol' in data and not isinstance(data['enable_protocol'], bool):
            raise ValueError("'enable_protocol' in 'MESH' must be a boolean.")

    def validate(self, data):
        for section, settings in data.items():
            if section == 'NETWORK':
                self.validate_network_settings(settings)
            elif section == 'STATION':
                self.validate_station_settings(settings)
            elif section == 'AUDIO':
                self.validate_audio_settings(settings)
            elif section == 'RADIO':
                self.validate_radio_settings(settings)
            elif section == 'TCI':
                self.validate_tci_settings(settings)
            elif section == 'MESH':
                self.validate_mesh_settings(settings)
            elif section == 'MODEM':
                self.validate_modem_settings(settings)
            else:
                self.log.warning("wrong config", section=section)

    # converts values of settings from String to Value.
    # For example 'False' (type String) will be converted to False (type Bool)
    def convert_types(self, config):
        for setting in config:
            value = config[setting]

            if isinstance(value, dict):
                # If the value is a dictionary, apply the function recursively
                config[setting] = self.convert_types(value)

            elif isinstance(value, list):
                # If the value is a list, iterate through the list
                new_list = []
                for item in value:
                    # Apply the function to each dictionary item in the list
                    if isinstance(item, dict):
                        new_list.append(self.convert_types(item))
                    else:
                        new_list.append(item)
                config[setting] = new_list

            elif isinstance(value, str):
                # Attempt to convert string values
                if value.lstrip('-').isdigit():
                    config[setting] = int(value)
                else:
                    try:
                        # Try converting to a float
                        float_value = float(value)
                        # If it's actually an integer (like -50.0), convert it to an integer
                        config[setting] = int(float_value) if float_value.is_integer() else float_value
                    except ValueError:
                        # Convert to boolean if applicable
                        if value.lower() in ['true', 'false']:
                            config[setting] = value.lower() == 'true'

        return config

    # Handle special setting data type conversion
    # is_writing means data from a dict being writen to the config file
    # if False, it means the opposite direction
    # TODO check if we can include this in function "convert_types"
    def handle_setting(self, section, setting, value, is_writing = False):
        if (section == 'STATION' and setting == 'ssid_list'):
            if (is_writing):
                return json.dumps(value)
            else:
                return json.loads(value)
        else: 
            return value

    # Sets and writes config data from a dict containing data settings
    def write(self, data):
        # convert datatypes
        data = self.convert_types(data)
        # Validate config data before writing
        self.validate(data)

        for section in data:
            # init section if it doesn't exist yet
            if not section.upper() in self.config.keys():
                self.config[section] = {}

            for setting in data[section]:
                new_value = self.handle_setting(
                    section, setting, data[section][setting], True)
                self.config[section][setting] = str(new_value)
        
        # Write config data to file
        try:
            with open(self.config_name, 'w') as configfile:
                self.config.write(configfile)
                return self.read()
        except Exception as conferror:
            self.log.error("[CFG] reading logfile", e=conferror)
            return False

    def read(self):
        """
        read config file
        """
        self.log.info("[CFG] reading...")
        if not self.config_exists():
            return False
        
        # at first just copy the config as read from file
        result = {s:dict(self.config.items(s)) for s in self.config.sections()}
        result = self.convert_types(result)

        # handle the special settings (like 'ssid_list')
        for section in result:
            for setting in result[section]:
                result[section][setting] = self.handle_setting(
                   section, setting, result[section][setting], False)

        return result
