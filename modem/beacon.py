import threading
import data_frame_factory
import command_beacon

class Beacon:

    BEACON_LOOP_INTERVAL = 1

    def __init__(self, config, states, event_queue, logger, modem):

        self.modem_config = config
        self.states = states
        self.event_queue = event_queue
        self.log = logger
        self.modem = modem

        self.loop_running = True
        self.paused = False
        self.thread = None
        self.event = threading.Event()

        self.frame_factory = data_frame_factory.DataFrameFactory(config)

    def start(self):
        beacon_thread = threading.Thread(target=self.run_beacon, name="beacon", daemon=True)
        beacon_thread.start()

    def stop(self):
        self.loop_running = False

    def refresh(self):
        self.event.set()
        self.event.clear()

    def run_beacon(self) -> None:
        while self.loop_running:
            while (self.states.is_beacon_running and 
                not self.paused and 
                True):
                #not self.states.channel_busy):

                cmd = command_beacon.BeaconCommand(self.modem_config, self.states, self.event_queue)
                cmd.run(self.event_queue, self.modem)
                self.event.wait(self.modem_config['MODEM']['beacon_interval'])

            self.event.wait(self.BEACON_LOOP_INTERVAL)
        