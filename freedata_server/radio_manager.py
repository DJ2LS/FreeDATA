import rigctld
import tci
import rigdummy
import time
import threading
class RadioManager:
    def __init__(self, config, state_manager, event_manager):
        self.config = config
        self.state_manager = state_manager
        self.event_manager = event_manager

        self.radiocontrol = config['RADIO']['control']
        self.rigctld_ip = config['RIGCTLD']['ip']
        self.rigctld_port = config['RIGCTLD']['port']

        self.refresh_rate = 1
        self.stop_event = threading.Event()
        self.update_thread = threading.Thread(target=self.update_parameters, daemon=True)
        self._init_rig_control()

    def _init_rig_control(self):
        # Check how we want to control the radio
        if self.radiocontrol in ["rigctld", "rigctld_bundle"]:
            self.radio = rigctld.radio(self.config, self.state_manager, hostname=self.rigctld_ip,port=self.rigctld_port)
        elif self.radiocontrol == "tci":
            raise NotImplementedError
            # self.radio = self.tci_module
        else:
            self.radio = rigdummy.radio()

        self.update_thread.start()

    def set_ptt(self, state):
        self.radio.set_ptt(state)

    def set_frequency(self, frequency):
        self.radio.set_frequency(frequency)

    def set_mode(self, mode):
        self.radio.set_mode(mode)

    def set_rf_level(self, level):
        self.radio.set_rf_level(level)

    def update_parameters(self):
        while not self.stop_event.is_set():
            parameters = self.radio.get_parameters()
            self.state_manager.set("radio_frequency", parameters['frequency'])
            self.state_manager.set("radio_mode", parameters['mode'])
            self.state_manager.set("radio_bandwidth", parameters['bandwidth'])
            self.state_manager.set("radio_rf_level", parameters['rf'])

            if self.state_manager.isTransmitting():
                self.radio_alc = parameters['alc']
            self.state_manager.set("s_meter_strength", parameters['strength'])
            time.sleep(self.refresh_rate)
    def stop(self):
        self.radio.disconnect()
        self.stop_event.set()