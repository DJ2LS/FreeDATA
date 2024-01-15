import command_beacon
import sched
import time
import threading

class Beacon:
    def __init__(self, config, states, event_manager, logger, modem):
        self.config = config
        self.states = states
        self.event_manager = event_manager
        self.log = logger
        self.modem = modem

        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.beacon_interval = self.config['MODEM']['beacon_interval']
        self.beacon_enabled = False
        self.event = threading.Event()

    def start(self):
        self.beacon_enabled = True
        self.schedule_beacon()

    def stop(self):
        self.beacon_enabled = False

    def schedule_beacon(self):
        if self.beacon_enabled:
            self.scheduler.enter(self.beacon_interval, 1, self.run_beacon)
            threading.Thread(target=self.scheduler.run, daemon=True).start()

    def run_beacon(self):
        if self.beacon_enabled:
            # Your beacon logic here
            cmd = command_beacon.BeaconCommand(self.config, self.states, self.event_manager)
            cmd.run(self.event_manager, self.modem)
            self.schedule_beacon()  # Reschedule the next beacon

    def refresh(self):
        # Interrupt and reschedule the beacon
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.schedule_beacon()