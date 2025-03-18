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
    """Manages scheduled tasks for the FreeDATA modem.

    This class schedules and executes various tasks related to the FreeDATA
    modem, including checking for queued messages, publishing to the
    explorer, transmitting beacons, cleaning up old beacons, and updating
    transmission states. It uses the `sched` module for scheduling and
    runs tasks in a separate thread.
    """
    def __init__(self, modem_version, config_manager, state_manger, event_manager):
        """Initializes the ScheduleManager.

        Args:
            modem_version (str): The version of the FreeDATA modem.
            config_manager (ConfigManager): The configuration manager instance.
            state_manger (StateManager): The state manager instance.
            event_manager (EventManager): The event manager instance.
        """
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
        """Schedules and executes a recurring event.

        This method executes the given event function and then reschedules
        it to run again after the specified interval, as long as the
        ScheduleManager is still running.

        Args:
            event_function (function): The function to execute.
            interval (int): The time interval between executions in seconds.
        """
        event_function()  # Execute the event function
        if self.running:  # Only reschedule if still running
            self.scheduler.enter(interval, 1, self.schedule_event, (event_function, interval))

    def start(self, modem):
        """Starts the scheduled tasks.

        This method initializes and starts the scheduler in a separate
        thread. It waits for a short period to allow the freedata_server to
        initialize, retrieves the freedata_server instance, sets the running
        flag, schedules the initial events, and starts the scheduler
        thread.

        Args:
            modem: The FreeDATA modem instance.
        """

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
        """Stops the scheduler and its associated thread.

        This method stops the scheduler by setting the running flag to
        False, canceling any pending scheduled events, and waiting for the
        scheduler thread to finish. It logs messages indicating the
        shutdown process.
        """
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
        """Transmits a beacon signal.

        This method transmits a beacon signal if beacon transmission is
        enabled, the freedata_server is running, and no ARQ transmission is in
        progress. It handles potential exceptions during beacon
        transmission.
        """
        try:
            if not self.state_manager.getARQ() and self.state_manager.is_beacon_running and self.state_manager.is_modem_running:
                    cmd = command_beacon.BeaconCommand(self.config, self.state_manager, self.event_manager)
                    cmd.run(self.event_manager, self.modem)
        except Exception as e:
            print(e)

    def delete_beacons(self):
        """Deletes old beacon records from the database.

        This method periodically cleans up old beacon records from the
        database that are older than two days. It handles potential
        exceptions during the cleanup process.
        """
        try:
            DatabaseManagerBeacon(self.event_manager).beacon_cleanup_older_than_days(2)
        except Exception as e:
            print(e)

    def push_to_explorer(self):
        
        self.config = self.config_manager.read()

        # check before if self.config has a loaded config dict
        if not isinstance(self.config, dict):
            return

        if self.config['STATION']['enable_explorer'] and self.state_manager.is_modem_running:
            try:
                explorer.Explorer(self.modem_version, self.config_manager, self.state_manager).push()
            except Exception as e:
                print(e)

    def check_for_queued_messages(self):
        """Checks for and sends queued messages.

        This method checks for queued messages in the database and transmits
        the first queued message if the freedata_server is running, not currently
        transmitting other data (ARQ or Codec2), and a queued message is
        available. It handles potential exceptions during message retrieval
        and transmission.
        """
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
        """Updates and cleans up ARQ session states.

        This method periodically checks the state of active ARQ sessions.
        It sets inactive IRS (Information Receiving Station) sessions to
        RESUME, deletes successfully completed or failed/aborted sessions,
        and handles potential exceptions during state updates and session
        deletion.
        """

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