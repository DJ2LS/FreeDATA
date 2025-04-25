
import xmlrpc.client
import threading
import time
import logging

class radio:
    def __init__(self, config, state_manager, host='127.0.0.1', port=12345, poll_interval=1.0):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.state_manager = state_manager
        self.host = self.config["FLRIG"]["ip"]
        self.port = self.config["FLRIG"]["port"]
        self.poll_interval = poll_interval

        self.server = None
        self.connected = False

        self.parameters = {
            'frequency': '---',
            'mode': '---',
            'alc': '---',
            'strength': '---',
            'bandwidth': '---',
            'rf': '---',
            'ptt': False,
            'tuner': False,
            'swr': '---'
        }

        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def connect(self, **kwargs):
        try:
            self.server = xmlrpc.client.ServerProxy(f"http://{self.host}:{self.port}")
            self.connected = True
            self.logger.info("Connected to FLRig")
            self.state_manager.set_radio("radio_status", True)
            return True
        except Exception as e:
            self.logger.error(f"FLRig connection failed: {e}")
            self.connected = False
            self.server = None
            self.state_manager.set_radio("radio_status", False)
            return False

    def disconnect(self, **kwargs):
        self.logger.info("Disconnected from FLRig")
        self.connected = False
        self.server = None
        self.state_manager.set_radio("radio_status", False)
        return True

    def _poll_loop(self):
        while not self._stop_event.is_set():
            if not self.connected:
                self.connect()
            if self.connected:
                try:
                    self.get_frequency()
                    self.get_mode()
                    self.get_rf()
                    self.get_ptt()
                    self.get_swr()
                    self.get_frequency()
                    self.get_mode()
                    self.get_level()


                except Exception as e:
                    self.logger.warning(f"Polling error: {e}")
                    self.connected = False
                    self.server = None
            time.sleep(self.poll_interval)

    def get_frequency(self):
        self.parameters['frequency'] = self.server.rig.get_vfo()
        return self.parameters['frequency']

    def get_rf(self):

        current_power_level = self.server.rig.get_power()
        max_power_level = self.server.rig.get_maxpwr()
        power_percentage = (int(current_power_level) / int(max_power_level)) * 100
        self.parameters['rf'] = round(power_percentage, 0)
        return self.parameters['rf']


    def set_frequency(self, frequency):
        self.parameters['frequency'] = frequency
        if self.connected:
            try:
                self.server.main.set_frequency(float(frequency))

            except Exception as e:
                self.logger.error(f"Set frequency failed: {e}")
                self.connected = False

    def get_mode(self):
        self.parameters['mode'] = self.server.rig.get_mode()
        return self.parameters['mode']

    def set_mode(self, mode):
        self.parameters['mode'] = mode
        if self.connected:
            try:
                self.server.rig.set_mode(mode)
            except Exception as e:
                self.logger.error(f"Set mode failed: {e}")
                self.connected = False

    def get_level(self):
        self.parameters['strength'] = self.server.rig.get_smeter()

    def get_alc(self):
        return None

    def get_meter(self):
        return None

    def get_bandwidth(self):
        return self.parameters['bandwidth']

    def set_bandwidth(self, bandwidth):
        if self.connected:
            try:
                self.server.rig.set_bandwidth(int(bandwidth))

            except Exception as e:
                self.logger.error(f"Set bandwidth failed: {e}")
                self.connected = False

    def set_rf_level(self, rf):
        if self.connected:
            try:
                # Get max power from rig
                max_power = self.server.rig.get_maxpwr()

                # Calculate absolute power in watts (rounded to int)
                power_watts = int((float(rf) / 100) * float(max_power))

                # Set power level in watts
                self.server.rig.set_power(power_watts)

            except Exception as e:
                self.logger.error(f"Set RF level failed: {e}")
                self.connected = False

    def get_strength(self):
        return self.parameters['strength']

    def get_tuner(self):
        return self.parameters['tuner']

    def set_tuner(self, state):
        self.parameters['tuner'] = state
        return None

    def get_swr(self):
        self.parameters['swr'] = self.server.rig.get_swrmeter()
        return self.parameters['swr']

    def get_ptt(self):
        self.parameters['ptt'] = self.server.rig.get_ptt()
        return self.parameters['ptt']

    def set_ptt(self, state):
        self.parameters['ptt'] = state
        if self.connected:
            try:
                if state:
                    result = self.server.rig.set_ptt(1)
                else:
                    result = self.server.rig.set_ptt(0)
            except Exception as e:
                self.logger.error(f"Set PTT failed: {e}")
        return state

    def set_tuner(self, state):
        self.parameters['ptt'] = state
        if self.connected:
            try:
                self.server.rig.tune(state)
            except Exception as e:
                self.logger.error(f"Set Tune failed: {e}")
        return state


    def get_status(self):
        return self.connected

    def get_parameters(self):
        return self.parameters

    def close_rig(self):
        self.logger.info("Closing FLRig interface")
        self._stop_event.set()
        self._thread.join()

    def stop_service(self):
        self.close_rig()