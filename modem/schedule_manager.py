import sched
import time
import threading
import command_message_send
from message_system_db_manager import DatabaseManager
from message_system_db_messages import DatabaseManagerMessages
from message_system_db_beacon import DatabaseManagerBeacon
import explorer
import command_beacon


class ScheduleManager:
    def __init__(self, modem_version, config_manager, state_manger, event_manager):
        self.modem_version = modem_version
        self.config_manager = config_manager
        self.state_manager = state_manger
        self.event_manager = event_manager
        self.config = self.config_manager.read()

        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.events = {
            'check_for_queued_messages': {'function': self.check_for_queued_messages, 'interval': 10},
            'explorer_publishing': {'function': self.push_to_explorer, 'interval': 60},
            'transmitting_beacon': {'function': self.transmit_beacon, 'interval': 600},
            'beacon_cleanup': {'function': self.delete_beacons, 'interval': 600},
        }
        self.running = False  # Flag to control the running state
        self.scheduler_thread = None  # Reference to the scheduler thread

        self.modem = None

    def schedule_event(self, event_function, interval):
        """Schedule an event and automatically reschedule it after execution."""
        event_function()  # Execute the event function
        if self.running:  # Only reschedule if still running
            self.scheduler.enter(interval, 1, self.schedule_event, (event_function, interval))

    def start(self, modem):
        """Start scheduling events and run the scheduler in a separate thread."""

        # wait some time
        threading.Event().wait(timeout=10)

        # get actual modem instance
        self.modem = modem

        self.running = True  # Set the running flag to True
        for event_info in self.events.values():
            # Schedule each event for the first time
            self.scheduler.enter(0, 1, self.schedule_event, (event_info['function'], event_info['interval']))

        # Run the scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self.scheduler.run, daemon=True)
        self.scheduler_thread.start()

    def stop(self):
        """Stop scheduling new events and terminate the scheduler thread."""
        self.running = False  # Clear the running flag to stop scheduling new events
        # Clear scheduled events to break the scheduler out of its waiting state
        for event in list(self.scheduler.queue):
            self.scheduler.cancel(event)
        # Wait for the scheduler thread to finish
        if self.scheduler_thread:
            self.scheduler_thread.join()

    def transmit_beacon(self):
        try:
            if not self.state_manager.getARQ() and self.state_manager.is_beacon_running:
                    cmd = command_beacon.BeaconCommand(self.config, self.state_manager, self.event_manager)
                    cmd.run(self.event_manager, self.modem)
        except Exception as e:
            print(e)

    def delete_beacons(self):
        try:
            DatabaseManagerBeacon(self.event_manager).beacon_cleanup_older_than_days(2)
        except Exception as e:
            print(e)

    def push_to_explorer(self):
        self.config = self.config_manager.read()
        if self.config['STATION']['enable_explorer']:
            try:
                explorer.explorer(self.modem_version, self.config_manager, self.state_manager).push()
            except Exception as e:
                print(e)

    def check_for_queued_messages(self):
        if not self.state_manager.getARQ():
            try:
                if first_queued_message := DatabaseManagerMessages(
                    self.event_manager
                ).get_first_queued_message():
                    command = command_message_send.SendMessageCommand(self.config_manager.read(), self.state_manager, self.event_manager, first_queued_message)
                    command.transmit(self.modem)
            except Exception as e:
                print(e)
        return

