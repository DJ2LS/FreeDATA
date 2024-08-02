# database_manager.py
import sqlite3

from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from threading import local
from message_system_db_model import Base, Station, Status, P2PMessage
import structlog
import helpers
import os
import sys

class DatabaseManager:
    DATABASE_ENV_VAR = 'FREEDATA_DATABASE'
    DEFAULT_DATABASE_FILE = 'freedata-messages.db'

    def __init__(self, event_manager):
        self.event_manager = event_manager

        db_file = self.get_database()
        self.engine = create_engine(db_file, echo=False)
        self.thread_local = local()
        self.session_factory = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

        self.logger = structlog.get_logger(type(self).__name__)

    def get_database(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(script_directory)

        if self.DATABASE_ENV_VAR in os.environ:
            #db_path = os.getenv(self.DATABASE_ENV_VAR, os.path.join(script_directory, self.DEFAULT_DATABASE_FILE))
            db_path = os.getenv(self.DATABASE_ENV_VAR)
        else:
            db_path = os.path.join(script_directory, self.DEFAULT_DATABASE_FILE)
        return 'sqlite:///' + db_path

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

    def database_repair_and_cleanup(self):
        session = self.get_thread_scoped_session()
        try:

            # Fetch the 'failed' status ID
            failed_status = session.query(Status).filter_by(name="failed").first()
            if not failed_status:
                raise ValueError("Failed status not found in the database")

            # Fetch the 'transmitting' status ID
            transmitting_status = session.query(Status).filter_by(name="transmitting").first()
            if transmitting_status:
                # Check if any messages have the status "transmitting" and update them to "failed"
                messages_to_update = session.query(P2PMessage).filter_by(status_id=transmitting_status.id).all()
                for message in messages_to_update:
                    message.status_id = failed_status.id

                session.commit()
                len_repaired_message = len(messages_to_update)
                if len_repaired_message > 0:
                    self.log(f"Repaired {len_repaired_message} messages ('transmitting' to 'failed')")

            # Vacuum the database to reclaim space
            session.execute(text("VACUUM"))
            self.log("Database vacuumed successfully")

            # Reindex all tables to improve query performance
            session.execute(text("REINDEX"))
            self.log("Database reindexed successfully")

            # Perform an integrity check on the database
            result = session.execute(text("PRAGMA integrity_check")).fetchone()
            if result[0] == 'ok':
                self.log("Database integrity check passed")
            else:
                self.log("Database integrity check failed", isWarning=True)

        except Exception as e:
            session.rollback()
            self.log(f"An error occurred while checking databse: {e}", isWarning=True)
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

