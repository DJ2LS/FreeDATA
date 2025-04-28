import socket
import structlog
import helpers
import threading

class radio:
    """Controls a radio using rigctld.

    This class provides methods to interact with a radio using the
    rigctld server. It supports connecting, disconnecting, setting
    parameters (PTT, mode, frequency, bandwidth, RF level, tuner),
    retrieving radio parameters, starting and stopping the rigctld
    service, and handling VFO settings.
    """

    log = structlog.get_logger("radio (rigctld)")

    def __init__(self, config, states, hostname="localhost", port=4532, timeout=3):
        """Initializes the radio controller.

        Args:
            config (dict): Configuration dictionary.
            states (StateManager): State manager instance.
            hostname (str, optional): Hostname or IP address of the
                rigctld server. Defaults to "localhost".
            port (int, optional): Port number of the rigctld server.
                Defaults to 4532.
            timeout (int, optional): Timeout for socket operations in
                seconds. Defaults to 3.
        """
        self.hostname = hostname
        self.port = port
        self.timeout = timeout
        self.states = states
        self.config = config

        self.rigctld_process = None

        self.connection = None
        self.connected = False
        self.shutdown = False
        self.await_response = threading.Event()
        self.await_response.set()

        self.parameters = {
            'frequency': '---',
            'mode': '---',
            'alc': '---',
            'strength': '---',
            'bandwidth': '---',
            'rf': '---',
            'ptt': False,  # Initial PTT state is set to False,
            'tuner': False,
            'swr': '---',
            'chk_vfo': False,
            'vfo': '---',
        }

        # start rigctld...
        if self.config["RADIO"]["control"] in ["rigctld_bundle"]:
            self.start_service()

        # connect to radio
        self.connect()

    def connect(self):
        """Connects to the rigctld server.

        This method attempts to establish a connection to the rigctld
        server. If successful, it sets the connected flag, updates the
        radio status, logs the connection, checks VFO support, and gets
        the current VFO. If the connection fails, it logs a warning and
        updates the radio status accordingly.
        """
        if self.shutdown:
            return
        try:
            self.connection = socket.create_connection((self.hostname, self.port), timeout=self.timeout)
            self.connection.settimeout(self.timeout)
            # wait some time for hopefully solving the hamlib warmup problems
            threading.Event().wait(2)
            self.connected = True
            self.states.set_radio("radio_status", True)
            self.log.info(f"[RIGCTLD] Connected to rigctld at {self.hostname}:{self.port}")
            #self.dump_caps()
            self.check_vfo()
            self.get_vfo()
        except Exception as err:
            self.log.warning(f"[RIGCTLD] Failed to connect to rigctld: {err}")
            self.connected = False
            self.states.set_radio("radio_status", False)

    def disconnect(self):
        """Disconnects from the rigctld server.

        This method disconnects from the rigctld server, updates the
        radio status, resets radio parameters, and closes the socket
        connection.
        """
        self.shutdown = True
        self.connected = False
        if self.connection:
            self.connection.close()
        del self.connection
        self.connection = None
        self.states.set_radio("radio_status", False)
        self.parameters = {
            'frequency': '---',
            'mode': '---',
            'alc': '---',
            'strength': '---',
            'bandwidth': '---',
            'rf': '---',
            'ptt': False,  # Initial PTT state is set to False,
            'tuner': False,
            'swr': '---',
            'vfo': '---'
        }

    def send_command(self, command):
        """Sends a command to the rigctld server.

        This method sends a command to the rigctld server and waits for a
        response. It handles potential timeouts and other errors during
        communication. It uses a threading.Event to synchronize command
        sending and avoid concurrent access to the socket.

        Args:
            command (str): The command to send to rigctld.

        Returns:
            str or None: The response from rigctld, or None if an error
            occurred, the response contains 'RPRT', or the response
            contains 'None'.

        Raises:
            TimeoutError: If a timeout occurs while waiting for a response.
        """
        if self.connected:
            # wait if we have another command awaiting its response...
            # we need to set a timeout for avoiding a blocking state
            if not self.await_response.wait(timeout=1):  # Check if timeout occurred
                raise TimeoutError(f"[RIGCTLD] Timeout waiting for response from rigctld before sending command: [{command}]")

            try:
                self.await_response.clear()  # Signal that a command is awaiting response

                self.connection.sendall(command.encode('utf-8') + b"\n")
                response = self.connection.recv(1024)
                self.await_response.set()  # Signal that the response has been received
                stripped_result = response.decode('utf-8').strip()
                if 'RPRT' in stripped_result:
                    return None

                if 'None' in stripped_result:
                    return None

                return stripped_result

            except socket.timeout:
                self.log.warning(f"[RIGCTLD] Timeout waiting for response from rigctld: [{command}]")
                self.connected = False  # Set connected to False if timeout occurs
                return None  # Return None to indicate timeout
            except Exception as err:
                self.log.warning(f"[RIGCTLD] Error sending command [{command}] to rigctld: {err}")
                self.connected = False
                return None  # Return None to indicate error
            finally:
                self.await_response.set()  # Ensure await_response is always set in case of exceptions
        return ""

    def insert_vfo(self, command):
        """Inserts the VFO into rigctld commands if supported.

        This method modifies rigctld commands to include the VFO
        information if VFO support is enabled and the VFO is set. It
        takes a command string as input and returns the modified command
        string with the VFO inserted.

        Args:
            command (str): The rigctld command string.

        Returns:
            str: The modified command string with VFO inserted, or the
            original command string if VFO is not supported or not set.
        """
        #self.get_vfo()
        if self.parameters['chk_vfo'] and self.parameters['vfo'] and self.parameters['vfo'] not in [None, False, 'err', 0]:
            return f"{command[:1].strip()} {self.parameters['vfo']} {command[1:].strip()}"

        return command


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
                    command = 'T 1'
                else:
                    command = 'T 0'

                command = self.insert_vfo(command)
                self.send_command(command)


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
                command = self.insert_vfo(command)

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
                command = self.insert_vfo(command)
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
                command = self.insert_vfo(command)
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
                command = self.insert_vfo(command)
                self.send_command(command)
                self.parameters['rf'] = rf
                return True
            except Exception as err:
                self.log.warning(f"[RIGCTLD] Error setting RF: {err}")
                self.connected = False
        return False

    def set_tuner(self, state):
        """Set the TUNER state.

        Args:
            state (bool): True to enable PTT, False to disable.

        Returns:
            bool: True if the PTT state was set successfully, False otherwise.
        """
        if self.connected:
            try:

                if state:
                    command = 'U TUNER 1'
                else:
                    command = 'U TUNER 0'

                command = self.insert_vfo(command)
                self.send_command(command)

                self.parameters['tuner'] = state  # Update PTT state in parameters
                return True
            except Exception as err:
                self.log.warning(f"[RIGCTLD] Error setting TUNER state: {err}")
                self.connected = False
        return False

    def get_tuner(self):
        """Set the TUNER state.

        Args:
            state (bool): True to enable PTT, False to disable.

        Returns:
            bool: True if the PTT state was set successfully, False otherwise.
        """
        if self.connected:
            try:

                command = self.insert_vfo('u TUNER')
                result = self.send_command(command)

                state = result not in [None, ''] and int(result) == 1
                self.parameters['tuner'] = state
                return True
            except Exception as err:
                self.log.warning(f"[RIGCTLD] Error getting TUNER state: {err}")
                self.get_vfo()

        return False

    def get_parameters(self):
        if not self.connected:
            self.connect()

        if self.connected:
            #self.check_vfo()
            self.get_vfo()
            self.get_frequency()
            self.get_mode_bandwidth()
            self.get_alc()
            self.get_strength()
            self.get_rf()
            self.get_tuner()
            self.get_swr()

        return self.parameters

    def dump_caps(self):
        """Dumps rigctld capabilities.

        This method sends the '\dump_caps' command to rigctld and prints
        the response. It is used for debugging and informational
        purposes. It handles potential errors during command execution.
        """
        try:
            vfo_response = self.send_command(r'\dump_caps')
            print(vfo_response)

        except Exception as e:
            self.log.warning(f"Error getting dump_caps: {e}")

    def check_vfo(self):
        """Checks for VFO support.

        This method checks if the connected radio supports VFO by sending
        the '\chk_vfo' command to rigctld. It updates the 'chk_vfo'
        parameter accordingly and handles potential errors during the
        check.
        """
        try:
            vfo_response = self.send_command(r'\chk_vfo')
            if vfo_response in [1, "1"]:
                self.parameters['chk_vfo'] = True
            else:
                self.parameters['chk_vfo'] = False

        except Exception as e:
            self.log.warning(f"Error getting chk_vfo: {e}")
            self.parameters['chk_vfo'] = False

    def get_vfo(self):
        """Gets the current VFO.

        This method retrieves the current VFO from the radio using the 'v'
        command if VFO support is enabled. It updates the 'vfo' parameter
        with the retrieved VFO or sets it to 'currVFO' if no specific VFO
        is returned. If VFO support is disabled, it sets 'vfo' to False.
        It handles potential errors during VFO retrieval.
        """
        try:
            if self.parameters['chk_vfo']:

                vfo_response = self.send_command('v')

                if vfo_response not in [None, 'None', '']:
                    self.parameters['vfo'] = vfo_response.strip('')
                else:
                    self.parameters['vfo'] = 'currVFO'


            else:
                self.parameters['vfo'] = False

        except Exception as e:
            self.log.warning(f"Error getting vfo: {e}")
            self.parameters['vfo'] = 'err'

    def get_frequency(self):
        """Gets the current frequency from the radio.

        This method retrieves the current frequency from the radio using
        the 'f' command, with VFO support if enabled. It updates the
        'frequency' parameter with the retrieved frequency or sets it to
        'err' if an error occurs or no frequency is returned. It handles
        potential errors during frequency retrieval.
        """
        try:
            command = self.insert_vfo('f')
            frequency_response = self.send_command(command)
            if frequency_response not in [None, '']:
                self.parameters['frequency'] = int(frequency_response)
            else:
                self.parameters['frequency'] = 'err'

        except Exception as e:
            self.log.warning(f"Error getting frequency: {e}")
            self.parameters['frequency'] = 'err'

    def get_mode_bandwidth(self):
        """Gets the current mode and bandwidth from the radio.

        This method retrieves the current mode and bandwidth from the
        radio using the 'm' command, with VFO support if enabled. It
        updates the 'mode' and 'bandwidth' parameters accordingly. It
        handles potential errors during retrieval, including ValueError
        if the response cannot be parsed correctly.
        """
        try:
            command = self.insert_vfo('m')
            response = self.send_command(command)

            if response not in [None, '']:
                response = response.strip()
                mode, bandwidth = response.split('\n', 1)
                bandwidth = int(bandwidth)
                self.parameters['mode'] = mode
                self.parameters['bandwidth'] = bandwidth
            else:
                self.parameters['mode'] = 'err'
                self.parameters['bandwidth'] = 'err'
        except ValueError:
            self.parameters['mode'] = 'err'
            self.parameters['bandwidth'] = 'err'
        except Exception as e:
            self.log.warning(f"Error getting mode and bandwidth: {e}")
            self.parameters['mode'] = 'err'
            self.parameters['bandwidth'] = 'err'

    def get_alc(self):
        """Gets the ALC (Automatic Level Control) value.

        This method retrieves the ALC value from the radio using the 'l
        ALC' command, with VFO support if enabled. It updates the 'alc'
        parameter with the retrieved value or sets it to 'err' if an
        error occurs or no value is returned. It handles potential
        errors during ALC retrieval.
        """
        try:
            command = self.insert_vfo('l ALC')
            alc_response = self.send_command(command)
            if alc_response not in [False, None, '', 'None', 0]:
                self.parameters['alc'] = float(alc_response)
            else:
                self.parameters['alc'] = 'err'

        except Exception as e:
            self.log.warning(f"Error getting ALC: {e}")
            self.parameters['alc'] = 'err'
            self.get_vfo()

    def get_strength(self):
        """Gets the signal strength.

        This method retrieves the signal strength from the radio using
        the 'l STRENGTH' command, with VFO support if enabled. It updates
        the 'strength' parameter with the retrieved value or sets it to
        'err' if an error occurs or no value is returned. It handles
        potential errors during strength retrieval.
        """
        try:
            command = self.insert_vfo('l STRENGTH')
            strength_response = self.send_command(command)
            if strength_response not in [None, '']:
                self.parameters['strength'] = int(strength_response)
            else:
                self.parameters['strength'] = 'err'
        except Exception as e:
            self.log.warning(f"Error getting strength: {e}")
            self.parameters['strength'] = 'err'
            self.get_vfo()

    def get_rf(self):
        """Gets the RF power level.

        This method retrieves the RF power level from the radio using the
        'l RFPOWER' command, with VFO support if enabled. It updates the
        'rf' parameter with the retrieved value (converted to integer
        percentage) or sets it to 'err' if an error occurs or no value is
        returned. It handles potential ValueErrors during conversion and
        other exceptions during retrieval.
        """
        try:
            command = self.insert_vfo('l RFPOWER')
            rf_response = self.send_command(command)
            if rf_response not in [None, '']:
                self.parameters['rf'] = int(float(rf_response) * 100)
            else:
                self.parameters['rf'] = 'err'
        except ValueError:
            self.parameters['rf'] = 'err'
        except Exception as e:
            self.log.warning(f"Error getting RF power: {e}")
            self.parameters['rf'] = 'err'
            self.get_vfo()

    def get_swr(self):
        """Gets the SWR (Standing Wave Ratio) value.

        This method retrieves the SWR value from the radio using the 'l
        SWR' command, with VFO support if enabled. It updates the 'swr'
        parameter with the retrieved value or sets it to 'err' if an
        error occurs or no value is returned. It handles potential
        ValueErrors and other exceptions during retrieval.
        """
        try:
            command = self.insert_vfo('l SWR')
            rf_response = self.send_command(command)
            if rf_response not in [None, '']:
                self.parameters['swr'] = rf_response
            else:
                self.parameters['swr'] = 'err'
        except ValueError:
            self.parameters['swr'] = 'err'
        except Exception as e:
            self.log.warning(f"Error getting SWR: {e}")
            self.parameters['swr'] = 'err'
            self.get_vfo()

    def start_service(self):
        """Starts the rigctld service.

        This method attempts to start the rigctld service using the
        configured parameters and any additional arguments. It searches
        for the rigctld binary in common locations, and if found,
        attempts to execute it. It handles potential errors during
        startup and logs informational and warning messages.
        """
        binary_name = "rigctld"
        binary_paths = helpers.find_binary_paths(binary_name, search_system_wide=True)
        additional_args = self.format_rigctld_args()

        if binary_paths:
            for binary_path in binary_paths:
                try:
                    self.log.info(f"Attempting to start rigctld using binary found at: {binary_path}")
                    self.rigctld_process = helpers.kill_and_execute(binary_path, additional_args)
                    self.log.info(f"Successfully executed rigctld", args=additional_args)
                    return  # Exit the function after successful execution
                except Exception as e:
                    self.log.warning(f"Failed to start rigctld with binary at {binary_path}: {e}")  # Log the error
            self.log.warning("Failed to start rigctld with all found binaries.", binaries=binary_paths)
        else:
            self.log.warning("Rigctld binary not found.")

    def stop_service(self):
        """Stops the rigctld service.

        This method stops the rigctld service if it was previously
        started by this class. It uses the helper function
        `helpers.kill_process` to terminate the rigctld process.
        """
        if self.rigctld_process:
            self.log.info("Stopping rigctld service")  # Log the action
            helpers.kill_process(self.rigctld_process)


    def format_rigctld_args(self):
        """Formats the arguments for starting rigctld.

        This method reads the configuration and constructs the command-line
        arguments for starting the rigctld process. It handles various
        settings like model ID, serial port parameters, PTT configuration,
        and custom arguments. Values defined as 'ignore', 0, or '0' in the
        configuration are skipped. The method returns a list of formatted
        arguments.

        Returns:
            list: A list of strings representing the formatted rigctld arguments.
        """
        config = self.config['RADIO']
        config_rigctld = self.config['RIGCTLD']
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

        if self.config['RIGCTLD']['enable_vfo']:
            args += ['--vfo']

        # Fixme        #rts_state
        # if not should_ignore(config.get('rts_state')):
        #    args += ['--set-conf', f'stop_bits={config["rts_state"]}']

        # Handle custom arguments for rigctld
        # Custom args are split via ' ' so python doesn't add extranaeous quotes on windows
        args += config_rigctld["arguments"].split(" ")
        print("Hamlib args ==>" + str(args))
        
        return args

