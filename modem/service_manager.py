import threading
import data_handler
import modem
import structlog

class SM:
    def __init__(self, app):
        self.log = structlog.get_logger("service")

        self.modem = False
        self.data_handler = False

        self.config = app.config_manager.config
        self.modem_events = app.modem_events
        self.modem_fft = app.modem_fft
        self.modem_service = app.modem_service

        runner_thread = threading.Thread(
            target=self.runner, name="runner thread", daemon=True
        )
        runner_thread.start()

    def runner(self):
        while True:
            cmd = self.modem_service.get()
            if cmd in ['start'] and not self.modem:
                self.log.info("starting modem....")
                self.modem = modem.RF(self.config, self.modem_events, self.modem_fft, self.modem_service)
                self.data_handler = data_handler.DATA(self.config, self.modem_events)
            else:
                print("--------------------------------------")
                self.log.info("stopping modem....")
                del self.modem
                del self.data_handler
                self.modem = False
                self.data_handler = False
