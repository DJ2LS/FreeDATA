import threading
import data_handler
import modem
import structlog
import audio
import ujson as json
import explorer


class SM:
    def __init__(self, app):
        self.log = structlog.get_logger("service")

        self.modem = False
        self.data_handler = False

        self.config = app.config_manager.read()
        self.modem_events = app.modem_events
        self.modem_fft = app.modem_fft
        self.modem_service = app.modem_service
        self.states = app.states

        runner_thread = threading.Thread(
            target=self.runner, name="runner thread", daemon=True
        )
        runner_thread.start()

        # optionally start explorer module
        if self.config['STATION']['enable_explorer']:
            explorer.explorer(self.config, self.states)

    def runner(self):
        while True:
            cmd = self.modem_service.get()
            if cmd in ['start'] and not self.modem:
                self.log.info("------------------ FreeDATA ------------------")
                self.log.info("------------------  MODEM   ------------------")
                self.start_modem()
            elif cmd in ['stop'] and self.modem:
                self.stop_modem()
                # we need to wait a bit for avoiding a portaudio crash
                threading.Event().wait(0.5)

            elif cmd in ['restart']:
                self.stop_modem()
                # we need to wait a bit for avoiding a portaudio crash
                threading.Event().wait(0.5)
                if self.start_modem():
                    self.modem_events.put(json.dumps({"freedata": "modem-event", "event": "restart"}))

            else:
                self.log.warning("[SVC] modem command processing failed", cmd=cmd, state=self.states.is_modem_running)


    def start_modem(self):
        audio_test = self.test_audio()
        if False not in audio_test and None not in audio_test and not self.states.is_modem_running:
            self.log.info("starting modem....")
            self.modem = modem.RF(self.config, self.modem_events, self.modem_fft, self.modem_service, self.states)
            self.data_handler = data_handler.DATA(self.config, self.modem_events, self.states)
            self.states.set("is_modem_running", True)
            return True
        elif self.states.is_modem_running:
            self.log.warning("modem already running")
            return False

        else:
            self.log.warning("starting modem failed", input_test=audio_test[0], output_test=audio_test[1])
            self.states.set("is_modem_running", False)
            self.modem_events.put(json.dumps({"freedata": "modem-event", "event": "failed"}))
            return False

    def stop_modem(self):
        self.log.info("stopping modem....")
        del self.modem
        del self.data_handler
        self.modem = False
        self.data_handler = False
        self.states.set("is_modem_running", False)

    def test_audio(self):
        audio_test = audio.test_audio_devices(self.config['AUDIO']['input_device'],
                                              self.config['AUDIO']['output_device'])
        self.log.info("tested audio devices", result=audio_test)

        return audio_test