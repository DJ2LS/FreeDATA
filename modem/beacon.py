import threading
import data_frame_factory
import time
import command_beacon
from state_manager import StateManager

class Beacon:

    BEACON_LOOP_INTERVAL = 1

    def __init__(self, config, modem_states: StateManager, event_queue, logger, modem_tx_queue):

        self.modem_config = config
        self.states = modem_states
        self.event_queue = event_queue
        self.log = logger
        self.tx_frame_queue = modem_tx_queue

        self.paused = False
        self.thread = None
        self.event = threading.Event()

        self.frame_factory = data_frame_factory.DataFrameFactory(config)

    def start(self):
        beacon_thread = threading.Thread(target=self.run_beacon, name="beacon", daemon=True)
        beacon_thread.start()

    def refresh(self):
        self.event.set()
        self.event.clear()

    def run_beacon(self) -> None:
        """
        Controlling function for running a beacon
        Args:

            self: arq class

        Returns:

        """
        while True:
            while (self.states.is_beacon_running and 
                not self.paused and 
                True):
                #not self.states.channel_busy):

                cmd = command_beacon.BeaconCommand(self.modem_config, self.log)
                cmd.run(self.event_queue, self.tx_frame_queue)
                self.event.wait(self.modem_config['MODEM']['beacon_interval'])

            self.event.wait(self.BEACON_LOOP_INTERVAL)
        