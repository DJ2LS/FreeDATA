import threading
import data_handler
import frame_dispatcher
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
        self.app = app
        self.config = self.app.config_manager.read()
        self.modem_events = app.modem_events
        self.modem_fft = app.modem_fft
        self.enable_fft_stream = False
        self.modem_service = app.modem_service
        self.states = app.state_manager

        runner_thread = threading.Thread(
            target=self.runner, name="runner thread", daemon=True
        )
        runner_thread.start()

        # optionally start explorer module
        if self.config['STATION']['enable_explorer']:
            explorer.explorer(self.app, self.config, self.states)

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
            elif cmd in ['fft:true']:
                # Tell modem it should put FFT data in the queue
                self.modem.set_FFT_stream(True)
                self.enable_fft_stream=True
            elif cmd in ['fft:false']:
                # Tell modem it should not put FFT data in the queue
                self.modem.set_FFT_stream(False)
                self.enable_fft_stream=False
            else:
                self.log.warning("[SVC] modem command processing failed", cmd=cmd, state=self.states.is_modem_running)


    def start_modem(self):
        # read config
        self.config = self.app.config_manager.read()

        if self.states.is_modem_running:
            self.log.warning("modem already running")
            return False

        # test audio devices
        audio_test = self.test_audio()

        if False in audio_test or None in audio_test or self.states.is_modem_running:
            self.log.warning("starting modem failed", input_test=audio_test[0], output_test=audio_test[1])
            self.states.set("is_modem_running", False)
            self.modem_events.put({"freedata": "modem-event", "event": "failed"})
            return False

        self.log.info("starting modem....")
        self.modem = modem.RF(self.config, self.modem_events, self.modem_fft, self.modem_service, self.states)

        self.frame_dispatcher = frame_dispatcher.DISPATCHER(self.config, self.modem_events, self.states)
        self.frame_dispatcher.start()

        self.states.set("is_modem_running", True)
        self.modem.set_FFT_stream(self.enable_fft_stream)

        return True
        
    def stop_modem(self):
        self.log.info("stopping modem....")
        del self.modem
        #del self.data_handler
        self.modem = False
        #self.data_handler = False
        self.states.set("is_modem_running", False)

    def test_audio(self):
        audio_test = audio.test_audio_devices(self.config['AUDIO']['input_device'],
                                              self.config['AUDIO']['output_device'])
        self.log.info("tested audio devices", result=audio_test)

        return audio_test