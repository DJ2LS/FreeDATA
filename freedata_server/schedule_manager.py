import sched
import time
import threading

import command_message_send
from message_system_db_manager import DatabaseManager
from message_system_db_messages import DatabaseManagerMessages
from message_system_db_beacon import DatabaseManagerBeacon
import explorer
import command_beacon
import atexit
import numpy as np
import structlog
from arq_session_irs import IRS_State
from arq_session_iss import ISS_State

class ScheduleManager:
    def __init__(self, modem_version, config_manager, state_manger, event_manager):
        self.log = structlog.get_logger("SCHEDULE_MANAGER")

        self.modem_version = modem_version
        self.config_manager = config_manager
        self.state_manager = state_manger
        self.event_manager = event_manager
        self.config = self.config_manager.read()

        self.scheduler = sched.scheduler(time.time, threading.Event().wait)
        self.events = {
            'check_for_queued_messages': {'function': self.check_for_queued_messages, 'interval': 5},
            'explorer_publishing': {'function': self.push_to_explorer, 'interval': 60},
            'transmitting_beacon': {'function': self.transmit_beacon, 'interval': 600},
            'beacon_cleanup': {'function': self.delete_beacons, 'interval': 600},
            'update_transmission_state': {'function': self.update_transmission_state, 'interval': 10},
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

        # wait some time for the modem to be ready
        threading.Event().wait(timeout=0.1)

        # get actual freedata_server instance
        self.modem = modem

        self.running = True  # Set the running flag to True
        for event_info in self.events.values():
            # Schedule each event for the first time
            self.scheduler.enter(0, 1, self.schedule_event, (event_info['function'], event_info['interval']))

        # Run the scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self.scheduler.run, daemon=False)
        self.scheduler_thread.start()

    def stop(self):
        """Stop scheduling new events and terminate the scheduler thread."""
        self.log.warning("[SHUTDOWN] stopping schedule manager....")
        self.running = False  # Clear the running flag to stop scheduling new events
        # Clear scheduled events to break the scheduler out of its waiting state
        for event in list(self.scheduler.queue):
            self.scheduler.cancel(event)

        # Wait for the scheduler thread to finish
        if self.scheduler_thread:
            self.scheduler_thread.join(1)
        self.log.warning("[SHUTDOWN] schedule manager stopped")
    def transmit_beacon(self):
        try:
            if not self.state_manager.getARQ() and self.state_manager.is_beacon_running and self.state_manager.is_modem_running:
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
        if self.config['STATION']['enable_explorer'] and self.state_manager.is_modem_running:
            try:
                explorer.Explorer(self.modem_version, self.config_manager, self.state_manager).push()
            except Exception as e:
                print(e)

    def check_for_queued_messages(self):
        if not self.state_manager.getARQ() and not self.state_manager.is_receiving_codec2_signal() and self.state_manager.is_modem_running:
            try:
                if first_queued_message := DatabaseManagerMessages(
                    self.event_manager
                ).get_first_queued_message():
                    command = command_message_send.SendMessageCommand(self.config_manager.read(), self.state_manager, self.event_manager, first_queued_message)
                    command.transmit(self.modem)
            except Exception as e:
                print(e)

        return

    def update_transmission_state(self):

        session_to_be_deleted = set()

        for session_id in self.state_manager.arq_irs_sessions:
            session = self.state_manager.arq_irs_sessions[session_id]

            # set an IRS session to RESUME for being ready getting the data again
            if session.is_IRS and session.last_state_change_timestamp + 90 < time.time():
                try:
                    # if session state is already RESUME, don't set it again for avoiding a flooded cli
                    if session.state not in [session.state_enum.RESUME]:
                        self.log.info(f"[SCHEDULE] [ARQ={session_id}] Setting state to", old_state=session.state,
                                      state=IRS_State.RESUME)
                        session.state = session.set_state(session.state_enum.RESUME)
                        session.state = session.state_enum.RESUME

                    # if session is received successfully, indiciated by ENDED state, delete it
                    if session.state in [session.state_enum.ENDED]:
                        session_to_be_deleted.add(session)

                except Exception as e:
                    self.log.warning("[SCHEDULE] error setting ARQ state", error=e)

        for session_id in self.state_manager.arq_iss_sessions:
            session = self.state_manager.arq_iss_sessions[session_id]
            if not session.is_IRS and session.last_state_change_timestamp + 90 < time.time() and session.state in [
                ISS_State.ABORTED, ISS_State.FAILED]:
                session_to_be_deleted.add(session)

        # finally delete sessions
        try:
            for session in session_to_be_deleted:
                if session.is_IRS:
                    self.state_manager.remove_arq_irs_session(session.id)
                else:
                    self.state_manager.remove_arq_iss_session(session.id)

        except Exception as e:
            self.log.warning("[SCHEDULE] error deleting ARQ session", error=e)