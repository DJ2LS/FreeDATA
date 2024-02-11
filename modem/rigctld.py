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
                return response.decode('utf-8').strip()
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
            self.parameters['frequency'] = self.send_command('f')
            response = self.send_command(
                'm').strip()  # Get the mode/bandwidth response and remove leading/trailing spaces
            try:
                mode, bandwidth = response.split('\n', 1)  # Split the response into mode and bandwidth
            except ValueError:
                mode = 'err'
                bandwidth = 'err'

            self.parameters['mode'] = mode
            self.parameters['bandwidth'] = bandwidth

            self.parameters['alc'] = self.send_command('l ALC')
            self.parameters['strength'] = self.send_command('l STRENGTH')
            self.parameters['rf'] = self.send_command('l RFPOWER') # RF, RFPOWER

        """Return the latest fetched parameters."""
        return self.parameters

    def start_service(self):
        binary_name = "rigctld"
        binary_path = helpers.find_binary_path(binary_name, search_system_wide=True)
        additional_args = self.format_rigctld_args()
        if binary_path:
            self.log.info(f"Rigctld binary found at: {binary_path}")
            helpers.kill_and_execute(binary_path, additional_args)
            self.log.info(f"Executed rigctld...")
        else:
            self.log.warning("Rigctld binary not found.")

    def format_rigctld_args(self):
        config = self.config['RADIO']  # Accessing the 'RADIO' section of the INI file
        args = []

        # Helper function to check if the value should be ignored
        def should_ignore(value):
            return value in ['ignore', 0]

        # Model ID, Serial Port, and Speed
        if not should_ignore(config.get('model_id', "0")):
            args += ['-m', str(config['model_id'])]
        if not should_ignore(config.get('serial_port', "0")):
            args += ['-r', config['serial_port']]
        if not should_ignore(config.get('serial_speed', "0")):
            args += ['-s', str(config['serial_speed'])]

        # PTT Port and Type
        if not should_ignore(config.get('ptt_port', "0")):
            args += ['--ptt-port', config['ptt_port']]
        if not should_ignore(config.get('ptt_type', "0")):
            args += ['--ptt-type', config['ptt_type']]

        # Serial DCD and DTR
        if not should_ignore(config.get('serial_dcd', "0")):
            args += ['--set-dcd', config['serial_dcd']]
        if not should_ignore(config.get('serial_dtr', "0")):
            args += ['--set-dtr', config['serial_dtr']]

        # Handling Stop Bits with the corrected --set-conf syntax
        if not should_ignore(config.get('stop_bits', "0")):
            args += ['--set-conf', f'stop_bits={config["stop_bits"]}']

        return args

