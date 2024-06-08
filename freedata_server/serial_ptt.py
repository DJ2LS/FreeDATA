import serial
import structlog

class radio:

    log = structlog.get_logger("radio (rigctld)")

    def __init__(self, config, state_manager):
        self.parameters = {
            'frequency': '---',
            'mode': '---',
            'alc': '---',
            'strength': '---',
            'bandwidth': '---',
            'rf': '---',
            'ptt': False,  # Initial PTT state is set to False
            'tuner': False,
            'swr': '---'
        }
        self.config = config
        self.state_manager = state_manager
        self.serial_rts = self.config["RADIO"]["serial_rts"]
        self.serial_dtr = self.config["RADIO"]["serial_dtr"]
        self.serial_comport = self.config["RADIO"]["ptt_port"]

        try:
            if self.serial_comport in ["ignore"]:
                self.state_manager.set_radio("radio_status", False)
                raise serial.SerialException
            self.serial_connection = serial.Serial(self.serial_comport)
            # Set initial states for RTS and DTR based on config
            self.set_rts_state(self.serial_rts)
            self.set_dtr_state(self.serial_dtr)
            self.set_ptt(False)

            self.state_manager.set_radio("radio_status", True)
        except serial.SerialException as e:
            self.log.warning(f"Error: could not open PTT port {self.serial_comport}: {e}")
            self.state_manager.set_radio("radio_status", False)
            self.serial_connection = None

    def connect(self, **kwargs):
        """
        Args:
          **kwargs:

        Returns:

        """
        return True

    def disconnect(self, **kwargs):
        """
        Args:
          **kwargs:

        Returns:

        """
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("Serial connection closed.")
        return True

    def get_frequency(self):
        """ """
        return None

    def get_mode(self):
        """ """
        return None

    def get_level(self):
        """ """
        return None

    def get_alc(self):
        """ """
        return None

    def get_meter(self):
        """ """
        return None

    def get_bandwidth(self):
        """ """
        return None

    def get_strength(self):
        """ """
        return None

    def get_tuner(self):
        """ """
        return None

    def get_swr(self):
        """ """
        return None

    def set_bandwidth(self):
        """ """
        return None

    def set_mode(self, mode):
        """
        Args:
          mode:

        Returns:

        """
        return None

    def set_tuner(self, state):
        """
        Args:
          mode:

        Returns:

        """
        return None

    def set_frequency(self, frequency):
        """
        Args:
          mode:

        Returns:

        """
        return None

    def get_status(self):
        """
        Args:
          mode:

        Returns:

        """
        return True

    def get_ptt(self):
        """ """
        return self.parameters['ptt']

    def set_ptt(self, state):
        """
        Args:
          state: Boolean - True to activate PTT, False to deactivate

        Returns:
          state: Boolean - The new PTT state
        """
        if self.serial_connection is None:
            self.log.warning("Error: Serial connection not established.")
            return self.parameters['ptt']

        try:
            self.set_rts_state(state)
            self.set_dtr_state(state)
            self.parameters['ptt'] = state
        except serial.SerialException as e:
            self.log.warning(f"Error: {e}")
            self.parameters['ptt'] = False
        return self.parameters['ptt']

    def set_rts_state(self, state):
        """
        Args:
          state: Boolean - True to activate, False to deactivate

        Sets the RTS line based on the configuration.
        """
        if self.serial_rts == "ON":
            self.serial_connection.rts = state
        else:
            self.serial_connection.rts = not state

    def set_dtr_state(self, state):
        """
        Args:
          state: Boolean - True to activate, False to deactivate

        Sets the DTR line based on the configuration.
        """
        if self.serial_dtr == "ON":
            self.serial_connection.dtr = state
        else:
            self.serial_connection.dtr = not state

    def close_rig(self):
        """ """
        return


    def get_parameters(self):
        return self.parameters

    def stop_service(self):
        pass