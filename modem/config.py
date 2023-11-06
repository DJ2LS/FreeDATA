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

        self.log.info("[CFG] logfile init", file=self.config_name)

        # check if log file exists
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

    def write_config(self, section: str, key: str, value):
        """
        write values to config
        """

    # Validates config data
    def validate(self, data):
        for section in data:
            for setting in data[section]:
                if section == 'NETWORK':
                    if setting == 'modemport' and int(data[section][setting]) == 0:
                        raise Exception("'modemport' should be an integer")
                if section == 'STATION':
                    if setting == 'mycall' and len(data[section][setting]) <= 0:
                        raise Exception("'%s' can't be empty" % setting)
                    if setting == 'mygrid' and len(data[section][setting]) <= 0:
                        raise Exception("'%s' can't be empty" % setting)
                    if setting == 'ssid_list' and not isinstance(data[section][setting], list):
                        raise Exception("'%s' needs to be a list" % setting)
        # TODO finish this for all config settings!
    
    # Handle special setting data type conversion 
    # is_writing means data from a dict being writen to the config file
    # if False, it means the opposite direction
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
        if not self.config_exists():
            return False
        
        # at first just copy the config as read from file
        result = {s:dict(self.config.items(s)) for s in self.config.sections()}

        # handle the special settings (like 'ssid_list')
        for section in result:
            for setting in result[section]:
                result[section][setting] = self.handle_setting(
                    section, setting, result[section][setting], False)

        return result

    def get(self, area, key, default):
        """
        read from config and add if not exists

        """

        for _ in range(2):
            try:
                parameter = (
                    self.config[area][key] in ["True", "true", True]
                    if default in ["True", "true", True, "False", "false", False]
                    else self.config[area][key]
                )
            except KeyError:
                self.config[area][key] = str(default)

        self.log.info("[CFG] reading...", parameter=parameter, key=key)
        return parameter
