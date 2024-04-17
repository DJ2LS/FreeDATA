# database_manager.py
import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from threading import local
from message_system_db_model import Base, Station, Status
import structlog
import helpers
import os

class DatabaseManager:
    def __init__(self, event_manger, db_file=None):
        self.event_manager = event_manger
        if not db_file:
            print(os.environ)

            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, 'freedata-messages.db')
            db_file = 'sqlite:///' + db_path

        self.engine = create_engine(db_file, echo=False)
        self.thread_local = local()
        self.session_factory = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

        self.logger = structlog.get_logger(type(self).__name__)

    def initialize_default_values(self):
        session = self.get_thread_scoped_session()
        try:
            statuses = [
                "transmitting",
                "transmitted",
                "received",
                "failed",
                "failed_checksum",
                "aborted",
                "queued"
            ]

            # Add default statuses if they don't exist
            for status_name in statuses:
                existing_status = session.query(Status).filter_by(name=status_name).first()
                if not existing_status:
                    new_status = Status(name=status_name)
                    session.add(new_status)

            session.commit()
            self.log("Initialized database")
        except Exception as e:
            session.rollback()
            self.log(f"An error occurred while initializing default values: {e}", isWarning=True)
        finally:
            session.remove()

    def log(self, message, isWarning=False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def get_thread_scoped_session(self):
        if not hasattr(self.thread_local, "session"):
            self.thread_local.session = scoped_session(self.session_factory)
        return self.thread_local.session

    def get_or_create_station(self, callsign, session=None):
        own_session = False
        if not session:
            session = self.get_thread_scoped_session()
            own_session = True

        try:
            station = session.query(Station).filter_by(callsign=callsign).first()
            if not station:
                self.log(f"Updating station list with {callsign}")
                station = Station(callsign=callsign, checksum=helpers.get_crc_24(callsign).hex())
                session.add(station)
                session.flush()

            if own_session:
                session.commit()  # Only commit if we created the session

            return station

        except Exception as e:

            if own_session:
                session.rollback()

        finally:
            if own_session:
                session.remove()

    def get_callsign_by_checksum(self, checksum):
        session = self.get_thread_scoped_session()
        try:
            station = session.query(Station).filter_by(checksum=checksum).first()
            if station:
                self.log(f"Found callsign [{station.callsign}] for checksum [{station.checksum}]")
                return station.callsign
            else:
                self.log(f"No callsign found for [{checksum}]")
                return None
        except Exception as e:
            self.log(f"Error fetching callsign for checksum {checksum}: {e}", isWarning=True)
            return {'status': 'failure', 'message': str(e)}
        finally:
            session.remove()

    def get_or_create_status(self, session, status_name):
        status = session.query(Status).filter_by(name=status_name).first()
        if not status:
            status = Status(name=status_name)
            session.add(status)
            session.flush()  # To get the ID immediately
        return status

