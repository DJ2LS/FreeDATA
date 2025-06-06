import rigctld
import flrig
import rigdummy
import serial_ptt
import threading

class RadioManager:
    def __init__(self, ctx):

        self.ctx = ctx

        self.radiocontrol = self.ctx.config_manager.config['RADIO']['control']


        self.refresh_rate = 1
        self.stop_event = threading.Event()
        self.update_thread = threading.Thread(target=self.update_parameters, daemon=True)
        self._init_rig_control()

    def _init_rig_control(self):
        # Check how we want to control the radio
        if self.radiocontrol in ["rigctld", "rigctld_bundle"]:
            self.radio = rigctld.radio(self.ctx)
        elif self.radiocontrol == "serial_ptt":
            self.radio = serial_ptt.radio(self.ctx)
        elif self.radiocontrol == "flrig":
            self.radio = flrig.radio(self.ctx)
        else:
            self.radio = rigdummy.radio()

        self.update_thread.start()

    def set_ptt(self, state):
        self.radio.set_ptt(state)
        # set disabled ptt twice for reducing chance of stuck PTT
        if not state:
            self.radio.set_ptt(state)

        # send ptt state via socket interface
        try:
            if self.ctx.config_manager.config['SOCKET_INTERFACE']['enable'] and self.ctx.socket_interface_manager.command_server.command_handler:
                self.socket_interface_manager.command_server.command_handler.socket_respond_ptt(state)
        except Exception as e:
            print(e)

    def set_tuner(self, state):
        self.radio.set_tuner(state)
        self.ctx.state_manager.set_radio("radio_tuner", state)

    def set_frequency(self, frequency):
        self.radio.set_frequency(frequency)
        self.ctx.state_manager.set_radio("radio_frequency", frequency)

    def set_mode(self, mode):
        self.radio.set_mode(mode)
        self.ctx.state_manager.set_radio("radio_mode", mode)

    def set_rf_level(self, level):
        self.radio.set_rf_level(level)
        self.ctx.state_manager.set_radio("radio_rf_level", level)

    def update_parameters(self):
        while not self.stop_event.is_set():
            parameters = self.radio.get_parameters()

            self.ctx.state_manager.set_radio("radio_frequency", parameters['frequency'])
            self.ctx.state_manager.set_radio("radio_mode", parameters['mode'])
            self.ctx.state_manager.set_radio("radio_bandwidth", parameters['bandwidth'])
            self.ctx.state_manager.set_radio("radio_rf_level", parameters['rf'])
            self.ctx.state_manager.set_radio("radio_tuner", parameters['tuner'])

            if self.ctx.state_manager.isTransmitting():
                self.radio_alc = parameters['alc']
                self.ctx.state_manager.set_radio("radio_swr", parameters['swr'])

            self.ctx.state_manager.set_radio("s_meter_strength", parameters['strength'])
            threading.Event().wait(self.refresh_rate)

    def stop(self):
        self.stop_event.set()
        self.radio.disconnect()
        self.radio.stop_service()