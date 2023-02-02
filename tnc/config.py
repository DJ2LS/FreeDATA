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
                                  'TNCPORT': data[50]
                                  }

        self.config['STATION'] = {'#Station settings': None,
                                  'mycall': data[1],
                                  'mygrid': data[2],
                                  'ssid_list': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] # list(data[26])
                                  }

        self.config['AUDIO'] = {'#Audio settings': None,
                                'rx': data[3],
                                'tx': data[4],
                                'txaudiolevel': data[22],
                                'auto_tune': data[27]

                                }
        self.config['RADIO'] = {'#Radio settings': None,
                                'radiocontrol': data[13],
                                # TODO: disabled because we dont need these settings anymore
                                #'devicename': data[5],
                                #'deviceport': data[6],
                                #'serialspeed': data[7],
                                #'pttprotocol': data[8],
                                #'pttport': data[9],
                                #'data_bits': data[10],
                                #'stop_bits': data[11],
                                #'handshake': data[12],
                                'rigctld_ip': data[14],
                                'rigctld_port': data[15]
                                }
        self.config['TNC'] = {'#TNC settings': None,
                              'scatter': data[16],
                              'fft': data[17],
                              'narrowband': data[18],
                              'fmin': data[19],
                              'fmax': data[20],
                              'qrv': data[23],
                              'rxbuffersize': data[24],
                              'explorer': data[25],
                              'stats': data[28]
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
            #print(self.config.read(self.config_name))
            #print(self.config.sections())

            return self.config

