import threading
import data_handler
import modem
import structlog
import audio

class SM:
    def __init__(self, app):
        self.log = structlog.get_logger("service")

        self.modem = False
        self.data_handler = False

        self.config = app.config_manager.config
        self.modem_events = app.modem_events
        self.modem_fft = app.modem_fft
        self.modem_service = app.modem_service
        self.states = app.states

        runner_thread = threading.Thread(
            target=self.runner, name="runner thread", daemon=True
        )
        runner_thread.start()

    def runner(self):
        while True:
            cmd = self.modem_service.get()
            if cmd in ['start'] and not self.modem:
                audio_test = audio.test_audio_devices(self.config['AUDIO']['input_device'], self.config['AUDIO']['output_device'])
                print(audio_test)
                if False not in audio_test and None not in audio_test and not self.states.is_modem_running:
                    self.log.info("starting modem....")
                    self.modem = modem.RF(self.config, self.modem_events, self.modem_fft, self.modem_service, self.states)
                    self.data_handler = data_handler.DATA(self.config, self.modem_events)
                    self.states.set("is_modem_running", True)

                else:
                    self.log.warning("starting modem failed", input_test=audio_test[0], output_test=audio_test[1])
                    self.states.set("is_modem_running", False)


            else:
                    print("--------------------------------------")
                    self.log.info("stopping modem....")
                    del self.modem
                    del self.data_handler
                    self.modem = False
                    self.data_handler = False
                    self.states.set("is_modem_running", False)

            threading.Event().wait(0.5)
