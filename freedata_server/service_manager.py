import threading
import frame_dispatcher
import modem
import structlog
import audio
import radio_manager
from socket_interface import SocketInterfaceHandler
import queue

class SM:
    """Manages the FreeDATA server services.

    This class controls the starting, stopping, and restarting of the modem,
    radio manager, and socket interface. It handles commands from the modem
    service queue and performs actions based on the received commands.
    """
    def __init__(self, ctx):
        """Initializes the service manager.

        This method sets up the service manager with references to the main
        application object and its components, including the config manager,
        modem, radio manager, state manager, event manager, and schedule
        manager. It also initializes the socket interface manager if enabled
        in the configuration and starts the runner thread.

        Args:
            app: The main application object.
        """
        
        
        self.log = structlog.get_logger("service manager")
        self.ctx = ctx
        self.ctx.rf_modem = False

        self.shutdown_flag = threading.Event()


        self.runner_thread = threading.Thread(
            target=self.runner, name="runner thread", daemon=False
        )

        self.runner_thread.start()


    def runner(self):
        """Main loop for handling service commands.

        This method continuously monitors the modem service queue for
        commands and executes the corresponding actions. It handles starting,
        stopping, and restarting the modem, radio manager, and socket
        interface.
        """
        while not self.shutdown_flag.is_set():
            try:
                cmd = self.ctx.modem_service.get()
                if self.shutdown_flag.is_set():
                    return

                if cmd in ['start']:
                    self.ctx.config_manager.read()

                    self.start_radio_manager()
                    self.start_modem()

                    if self.ctx.config_manager.config['SOCKET_INTERFACE']['enable']:
                        self.ctx.socket_interface_manager = SocketInterfaceHandler(self.ctx).start_servers()
                    else:
                        self.ctx.socket_interface_manager = None

                elif cmd in ['stop'] and self.ctx.rf_modem:
                    self.stop_modem()
                    self.stop_radio_manager()
                    if self.ctx.config_manager.config['SOCKET_INTERFACE']['enable'] and self.ctx.socket_interface_manager:
                        self.ctx.socket_interface_manager.stop_servers()
                    # we need to wait a bit for avoiding a portaudio crash
                    threading.Event().wait(0.5)

                elif cmd in ['restart']:
                    self.stop_modem()
                    self.stop_radio_manager()
                    if self.ctx.config_manager.config['SOCKET_INTERFACE']['enable'] and self.ctx.socket_interface_manager:
                        self.ctx.socket_interface_manager.stop_servers()
                        del self.ctx.socket_interface_manager

                    # we need to wait a bit for avoiding a portaudio crash
                    threading.Event().wait(0.5)
                    self.log.info("reading config...")
                    self.ctx.config_manager.read()

                    self.log.info("starting modem")
                    if self.start_modem():
                        self.ctx.event_manager.modem_restarted()

                    self.log.info("starting radio manager")
                    self.start_radio_manager()

                    if self.ctx.config_manager.config['SOCKET_INTERFACE']['enable']:
                        self.ctx.socket_interface_manager = SocketInterfaceHandler(self.ctx).start_servers()
                    else:
                        self.ctx.socket_interface_manager = None

                else:
                    if not self.shutdown_flag.is_set():
                        self.log.warning("[SVC] freedata_server command processing failed", cmd=cmd, state=self.ctx.state_manager.is_modem_running)

            # Queue is empty
            except queue.Empty:
                pass

            # finally clear processing commands
            self.ctx.modem_service.queue.clear()

    def start_modem(self):
        """Starts the FreeDATA modem.

        This method initializes and starts the RF modem, frame dispatcher,
        and schedule manager. It performs checks for valid callsign and
        audio device functionality before starting the modem.

        Returns:
            bool: True if the modem started successfully, False otherwise.
        """

        if self.ctx.config_manager.config['STATION']['mycall'] in ['XX1XXX']:
            self.log.warning("wrong callsign in config! interrupting startup")
            return False

        if self.ctx.state_manager.is_modem_running:
            self.log.warning("freedata_server already running")
            return False

        if not self.ctx.TESTMODE:
            # test audio devices
            audio_test = self.test_audio()
            if False in audio_test or None in audio_test or self.ctx.state_manager.is_modem_running:
                self.log.warning("starting freedata_server failed", input_test=audio_test[0], output_test=audio_test[1])
                self.ctx.state_manager.set("is_modem_running", False)
                self.ctx.event_manager.modem_failed()
                return False

        self.log.info("starting freedata_server....")
        self.ctx.rf_modem = modem.RF(self.ctx)
        self.frame_dispatcher = frame_dispatcher.DISPATCHER(self.ctx)
        self.frame_dispatcher.start()

        self.ctx.event_manager.modem_started()
        self.ctx.state_manager.set("is_modem_running", True)
        self.ctx.rf_modem.start_modem()
        self.ctx.schedule_manager.start(self.ctx.rf_modem)

        return True
        
    def stop_modem(self):
        """Stops the FreeDATA modem and related services.

        This method stops the RF modem, frame dispatcher, and schedule
        manager. It also updates the modem running state and emits a
        'modem_stopped' event. It handles potential AttributeErrors that
        may occur during the stopping process if components are not
        initialized.
        """
        self.log.warning("stopping modem....")
        try:
            if self.ctx.rf_modem and hasattr(self.ctx, 'modem_service'):
                self.ctx.rf_modem.stop_modem()
                del self.ctx.rf_modem
                self.ctx.rf_modem = False
        except AttributeError:
            pass
        self.ctx.state_manager.set("is_modem_running", False)
        try:
            if self.ctx.schedule_manager and hasattr(self.ctx, 'schedule_manager'):
                self.ctx.schedule_manager.stop()
        except AttributeError:
            pass
        try:
            if self.frame_dispatcher and hasattr(self.ctx, 'frame_dispatcher'):
                self.frame_dispatcher.stop()
        except AttributeError:
            pass

        self.ctx.event_manager.modem_stopped()

    def test_audio(self):
        """Tests the configured audio devices.

        This method tests the input and output audio devices specified in
        the configuration. It logs the test results and returns a list
        indicating whether each device passed the test.

        Returns:
            list: A list of booleans, where the first element represents the
            input device test result and the second element represents the
            output device test result. Returns [False, False] if an error
            occurs during testing.
        """
        try:
            audio_test = audio.test_audio_devices(self.ctx.config_manager.config['AUDIO']['input_device'],
                                                  self.ctx.config_manager.config['AUDIO']['output_device'])
            self.log.info("tested audio devices", result=audio_test)

            return audio_test
        except Exception as e:
            self.log.error("Error testing audio devices", e=e)
            return [False, False]

    def start_radio_manager(self):

        """Starts the radio manager.

        This method initializes and starts the RadioManager, which handles
        communication with the radio.
        """
        self.ctx.radio_manager = radio_manager.RadioManager(self.ctx)

    def stop_radio_manager(self):
        """Stops the radio manager.

        This method stops the RadioManager and releases the associated
        resources. It handles potential AttributeErrors if the radio manager
        has not been initialized.
        """
        if hasattr(self.ctx, 'radio_manager'):
            self.ctx.radio_manager.stop()
            del self.ctx.radio_manager

    def shutdown(self):
        """Shuts down the service manager.

        This method stops the modem, sets the shutdown flag, and waits for
        the runner thread to finish. This ensures a clean shutdown of all
        managed services.
        """
        self.log.warning("[SHUTDOWN] stopping service manager....")
        self.ctx.modem_service.put("stop")
        threading.Event().wait(2) # we need some time before processing with the shutdown_event_flag
        self.shutdown_flag.set()
        self.runner_thread.join(0.5)
