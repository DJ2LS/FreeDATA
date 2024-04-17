import threading
import frame_dispatcher
import modem
import structlog
import audio

import radio_manager
from socket_interface import SocketInterfaceHandler

class SM:
    def __init__(self, app):
        self.log = structlog.get_logger("service")
        self.app = app
        self.modem = False
        self.app.radio_manager = False
        self.config = self.app.config_manager.read()
        self.modem_fft = app.modem_fft
        self.modem_service = app.modem_service
        self.state_manager = app.state_manager
        self.event_manager = app.event_manager
        self.schedule_manager = app.schedule_manager
        self.socket_interface_manager = None

        runner_thread = threading.Thread(
            target=self.runner, name="runner thread", daemon=True
        )
        runner_thread.start()

    def runner(self):
        while True:
            cmd = self.modem_service.get()
            if cmd in ['start'] and not self.modem:
                self.config = self.app.config_manager.read()
                self.start_radio_manager()
                self.start_modem()

                if self.config['SOCKET_INTERFACE']['enable']:
                    self.socket_interface_manager = SocketInterfaceHandler(self.modem, self.app.config_manager, self.state_manager, self.event_manager).start_servers()

            elif cmd in ['stop'] and self.modem:
                self.stop_modem()
                self.stop_radio_manager()
                if self.config['SOCKET_INTERFACE']['enable'] and self.socket_interface_manager:
                    self.socket_interface_manager.stop_servers()
                # we need to wait a bit for avoiding a portaudio crash
                threading.Event().wait(0.5)

            elif cmd in ['restart']:
                self.stop_modem()
                self.stop_radio_manager()
                if self.config['SOCKET_INTERFACE']['enable'] and self.socket_interface_manager:

                    self.socket_interface_manager.stop_servers()

                # we need to wait a bit for avoiding a portaudio crash
                threading.Event().wait(0.5)

                self.config = self.app.config_manager.read()
                self.start_radio_manager()

                if self.start_modem():
                    self.event_manager.modem_restarted()

            else:
                self.log.warning("[SVC] modem command processing failed", cmd=cmd, state=self.state_manager.is_modem_running)


    def start_modem(self):

        if self.config['STATION']['mycall'] in ['XX1XXX']:
            self.log.warning("wrong callsign in config! interrupting startup")
            return False

        if self.state_manager.is_modem_running:
            self.log.warning("modem already running")
            return False


        # test audio devices
        audio_test = self.test_audio()

        if False in audio_test or None in audio_test or self.state_manager.is_modem_running:
            self.log.warning("starting modem failed", input_test=audio_test[0], output_test=audio_test[1])
            self.state_manager.set("is_modem_running", False)
            self.event_manager.modem_failed()
            return False

        self.log.info("starting modem....")
        self.modem = modem.RF(self.config, self.event_manager, self.modem_fft, self.modem_service, self.state_manager, self.app.radio_manager)

        self.frame_dispatcher = frame_dispatcher.DISPATCHER(self.config, 
                                                            self.event_manager,
                                                            self.state_manager,
                                                            self.modem)
        self.frame_dispatcher.start()

        self.event_manager.modem_started()
        self.state_manager.set("is_modem_running", True)
        self.modem.start_modem()
        self.schedule_manager.start(self.modem)

        return True
        
    def stop_modem(self):
        self.log.info("stopping modem....")
        del self.modem
        self.modem = False
        self.state_manager.set("is_modem_running", False)
        self.schedule_manager.stop()
        self.event_manager.modem_stopped()

    def test_audio(self):
        try:
            audio_test = audio.test_audio_devices(self.config['AUDIO']['input_device'],
                                                  self.config['AUDIO']['output_device'])
            self.log.info("tested audio devices", result=audio_test)

            return audio_test
        except Exception as e:
            self.log.error("Error testing audio devices", e=e)
            return [False, False]

    def start_radio_manager(self):
        self.app.radio_manager = radio_manager.RadioManager(self.config, self.state_manager, self.event_manager)

    def stop_radio_manager(self):
        self.app.radio_manager.stop()
        del self.app.radio_manager