import configparser
import structlog



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

    def write_entire_config(self, data):
        """
        write entire config
        """
        self.config['NETWORK'] = {'#Network settings': None,
                                  'ModemPORT': data[50]
                                  }

        self.config['STATION'] = {'#Station settings': None,
                                  'mycall': data[1],
                                  'mygrid': data[2],
                                  'ssid_list': list(data[18])  # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] # list(data[18])
                                  }

        self.config['AUDIO'] = {'#Audio settings': None,
                                'rx': data[3],
                                'tx': data[4],
                                'txaudiolevel': data[14],
                                'rxaudiolevel': data[25],
                                'auto_tune': data[19]

                                }
        self.config['RADIO'] = {'#Radio settings': None,
                                'radiocontrol': data[5],
                                'rigctld_ip': data[6],
                                'rigctld_port': data[7]
                                }
        self.config['Modem'] = {'#Modem settings': None,
                                'scatter': data[8],
                                'fft': data[9],
                                'narrowband': data[10],
                                'fmin': data[11],
                                'fmax': data[12],
                                'qrv': data[15],
                                'rx_buffer_size': data[16],
                                'explorer': data[17],
                                'stats': data[19],
                                'fsk': data[13],
                                'tx_delay': data[21],
                                'transmit_morse_identifier': data[26]
                                }
        self.config['TCI'] = {'#TCI settings': None,
                              'ip': data[22],
                              'port': data[23]
                              }

        self.config['MESH'] = {'#Mesh settings': None,
                               'enable_protocol': data[24]
                               }

        try:
            with open(self.config_name, 'w') as configfile:
                self.config.write(configfile)
        except Exception as conferror:
            self.log.error("[CFG] reading logfile", e=conferror)

    def read_config(self):
        """
        read config file
        """
        if self.config_exists():
            # print(self.config.read(self.config_name))
            # print(self.config.sections())

            return self.config

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

        # ... [rest of the CONFIG class] ...

    def get_as_dict(self, modules: list = None):
        """
        Get config as a dictionary
        We return it as dictionary, because we want to use Flasks built-in jsonify function
        If module list is empty, return entire config, else the specified modules
        """
        module_list = set()
        config_dict = {}
        try:
            # check if module entries available in config sections
            # otherwise use all sections
            if modules:
                for module in modules:
                    config_sections = self.config.sections()
                    if module in config_sections:
                        module_list.add(module)
            else:
                module_list = self.config.sections()

            # Iterate over all sections in config
            for section in module_list:
                section_dict = {}

                # Iterate over all options in section
                for key in self.config[section]:
                    # Add key value to section key
                    section_dict[key] = self.config[section][key]

                # Add section to config dictionary
                config_dict[section] = section_dict
            return config_dict

        except Exception as e:
            self.log.info("[CFG] Error while converting config to dict", modules=modules, e=e)
            return {}
