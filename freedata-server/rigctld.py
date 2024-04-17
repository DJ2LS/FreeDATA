import socket
import structlog
import helpers
import threading

class radio:
    """rigctld (hamlib) communication class"""

    log = structlog.get_logger("radio (rigctld)")

    def __init__(self, config, states, hostname="localhost", port=4532, timeout=5):
        self.hostname = hostname
        self.port = port
        self.timeout = timeout
        self.states = states
        self.config = config

        self.connection = None
        self.connected = False
        self.await_response = threading.Event()
        self.await_response.set()

        self.parameters = {
            'frequency': '---',
            'mode': '---',
            'alc': '---',
            'strength': '---',
            'bandwidth': '---',
            'rf': '---',
            'ptt': False  # Initial PTT state is set to False
        }

        # start rigctld...
        if self.config["RADIO"]["control"] in ["rigctld_bundle"]:
            self.start_service()

        # connect to radio
        self.connect()

    def connect(self):
        try:
            self.connection = socket.create_connection((self.hostname, self.port), timeout=self.timeout)
            self.connected = True
            self.states.set("radio_status", True)
            self.log.info(f"[RIGCTLD] Connected to rigctld at {self.hostname}:{self.port}")
        except Exception as err:
            self.log.warning(f"[RIGCTLD] Failed to connect to rigctld: {err}")
            self.connected = False
            self.states.set("radio_status", False)

    def disconnect(self):
        self.connected = False
        if self.connection:
            self.connection.close()
        del self.connection
        self.connection = None
        self.states.set("radio_status", False)
        self.parameters = {
            'frequency': '---',
            'mode': '---',
            'alc': '---',
            'strength': '---',
            'bandwidth': '---',
            'rf': '---',
            'ptt': False  # Initial PTT state is set to False
        }

    def send_command(self, command) -> str:
        if self.connected:
            # wait if we have another command awaiting its response...
            # we need to set a timeout for avoiding a blocking state
            self.await_response.wait(timeout=1)

            try:
                self.await_response = threading.Event()
                self.connection.sendall(command.encode('utf-8') + b"\n")
                response = self.connection.recv(1024)
                self.await_response.set()
                stripped_result = response.decode('utf-8').strip()
                if 'RPRT' in stripped_result:
                    return None
                return stripped_result

            except Exception as err:
                self.log.warning(f"[RIGCTLD] Error sending command [{command}] to rigctld: {err}")
                self.connected = False
        return ""

    def set_ptt(self, state):
        """Set the PTT (Push-to-Talk) state.

        Args:
            state (bool): True to enable PTT, False to disable.

        Returns:
            bool: True if the PTT state was set successfully, False otherwise.
        """
        if self.connected:
            try:
                if state:
                    self.send_command('T 1')  # Enable PTT
                else:
                    self.send_command('T 0')  # Disable PTT
                self.parameters['ptt'] = state  # Update PTT state in parameters
                return True
            except Exception as err:
                self.log.warning(f"[RIGCTLD] Error setting PTT state: {err}")
                self.connected = False
        return False

    def set_mode(self, mode):
        """Set the mode.

        Args:
            mode (str): The mode to set.

        Returns:
            bool: True if the mode was set successfully, False otherwise.
        """
        if self.connected:
            try:
                command = f"M {mode} 0"
                self.send_command(command)
                self.parameters['mode'] = mode
                return True
            except Exception as err:
                self.log.warning(f"[RIGCTLD] Error setting mode: {err}")
                self.connected = False
        return False

    def set_frequency(self, frequency):
        """Set the frequency.

        Args:
            frequency (str): The frequency to set.

        Returns:
            bool: True if the frequency was set successfully, False otherwise.
        """
        if self.connected:
            try:
                command = f"F {frequency}"
                self.send_command(command)
                self.parameters['frequency'] = frequency
                return True
            except Exception as err:
                self.log.warning(f"[RIGCTLD] Error setting frequency: {err}")
                self.connected = False
        return False

    def set_bandwidth(self, bandwidth):
        """Set the bandwidth.

        Args:
            bandwidth (str): The bandwidth to set.

        Returns:
            bool: True if the bandwidth was set successfully, False otherwise.
        """
        if self.connected:
            try:
                command = f"M {self.parameters['mode']} {bandwidth}"
                self.send_command(command)
                self.parameters['bandwidth'] = bandwidth
                return True
            except Exception as err:
                self.log.warning(f"[RIGCTLD] Error setting bandwidth: {err}")
                self.connected = False
        return False

    def set_rf_level(self, rf):
        """Set the RF.

        Args:
            rf (str): The RF to set.

        Returns:
            bool: True if the RF was set successfully, False otherwise.
        """
        if self.connected:
            try:
                command = f"L RFPOWER {rf/100}" #RF RFPOWER --> RFPOWER == IC705
                self.send_command(command)
                self.parameters['rf'] = rf
                return True
            except Exception as err:
                self.log.warning(f"[RIGCTLD] Error setting RF: {err}")
                self.connected = False
        return False

    def get_parameters(self):
        if not self.connected:
            self.connect()

        if self.connected:
            self.get_frequency()
            self.get_mode_bandwidth()
            self.get_alc()
            self.get_strength()
            self.get_rf()

        return self.parameters

    def get_frequency(self):
        try:
            frequency_response = self.send_command('f')
            self.parameters['frequency'] = frequency_response if frequency_response is not None else 'err'
        except Exception as e:
            self.log.warning(f"Error getting frequency: {e}")
            self.parameters['frequency'] = 'err'

    def get_mode_bandwidth(self):
        try:
            response = self.send_command('m')
            if response is not None:
                response = response.strip()
                mode, bandwidth = response.split('\n', 1)
            else:
                mode = 'err'
                bandwidth = 'err'
        except ValueError:
            mode = 'err'
            bandwidth = 'err'
        except Exception as e:
            self.log.warning(f"Error getting mode and bandwidth: {e}")
            mode = 'err'
            bandwidth = 'err'
        finally:
            self.parameters['mode'] = mode
            self.parameters['bandwidth'] = bandwidth

    def get_alc(self):
        try:
            alc_response = self.send_command('l ALC')
            self.parameters['alc'] = alc_response if alc_response is not None else 'err'
        except Exception as e:
            self.log.warning(f"Error getting ALC: {e}")
            self.parameters['alc'] = 'err'

    def get_strength(self):
        try:
            strength_response = self.send_command('l STRENGTH')
            self.parameters['strength'] = strength_response if strength_response is not None else 'err'
        except Exception as e:
            self.log.warning(f"Error getting strength: {e}")
            self.parameters['strength'] = 'err'

    def get_rf(self):
        try:
            rf_response = self.send_command('l RFPOWER')
            if rf_response is not None:
                self.parameters['rf'] = int(float(rf_response) * 100)
            else:
                self.parameters['rf'] = 'err'
        except ValueError:
            self.parameters['rf'] = 'err'
        except Exception as e:
            self.log.warning(f"Error getting RF power: {e}")
            self.parameters['rf'] = 'err'

    def start_service(self):
        binary_name = "rigctld"
        binary_paths = helpers.find_binary_paths(binary_name, search_system_wide=True)
        additional_args = self.format_rigctld_args()

        if binary_paths:
            for binary_path in binary_paths:
                try:
                    self.log.info(f"Attempting to start rigctld using binary found at: {binary_path}")
                    helpers.kill_and_execute(binary_path, additional_args)
                    self.log.info("Successfully executed rigctld.")
                    break  # Exit the loop after successful execution
                except Exception as e:
                    pass
                    # let's keep this hidden for the user to avoid confusion
                    # self.log.warning(f"Failed to start rigctld with binary at {binary_path}: {e}")
            else:
                self.log.warning("Failed to start rigctld with all found binaries.", binaries=binary_paths)
        else:
            self.log.warning("Rigctld binary not found.")


    def format_rigctld_args(self):
        config = self.config['RADIO']  # Accessing the 'RADIO' section of the INI file
        config_rigctld = self.config['RIGCTLD'] # Accessing the 'RIGCTLD' section of the INI file for custom args
        args = []

        # Helper function to check if the value should be ignored
        def should_ignore(value):
            return value in ['ignore', 0]

        # Model ID, Serial Port, and Speed
        if not should_ignore(config.get('model_id')):
            args += ['-m', str(config['model_id'])]
        if not should_ignore(config.get('serial_port')):
            args += ['-r', config['serial_port']]
        if not should_ignore(config.get('serial_speed')):
            args += ['-s', str(config['serial_speed'])]

        # PTT Port and Type
        if not should_ignore(config.get('ptt_port')):
            args += ['-p', config['ptt_port']]
        if not should_ignore(config.get('ptt_type')):
            args += ['-P', config['ptt_type']]

        # Serial DCD and DTR
        if not should_ignore(config.get('serial_dcd')):
            args += ['-D', config['serial_dcd']]

        if not should_ignore(config.get('serial_dtr')):
            args += ['--set-conf', f'dtr_state={config["serial_dtr"]}']

        # Handling Data Bits and Stop Bits
        if not should_ignore(config.get('data_bits')):
            args += ['--set-conf', f'data_bits={config["data_bits"]}']
        if not should_ignore(config.get('stop_bits')):
            args += ['--set-conf', f'stop_bits={config["stop_bits"]}']

        # Fixme        #rts_state
        # if not should_ignore(config.get('rts_state')):
        #    args += ['--set-conf', f'stop_bits={config["rts_state"]}']

        # Handle custom arguments for rigctld
        # Custom args are split via ' ' so python doesn't add extranaeous quotes on windows
        args += config_rigctld["arguments"].split(" ")
        print("Hamlib args ==>" + str(args))
        
        return args

