from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from message_system_db_model import Station
from message_system_db_manager import DatabaseManager
import os


class DatabaseManagerStations(DatabaseManager):
    def __init__(self, db_file=None):
        if not db_file:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, 'freedata-messages.db')
            db_file = 'sqlite:///' + db_path

        super().__init__(db_file)

    def get_station(self, callsign):
        """
        Retrieves a station by its callsign.
        """

        session = self.get_thread_scoped_session()
        try:
            station = session.query(Station).filter_by(callsign=callsign).first()
            return station.to_dict() if station else None

        except Exception as e:
            self.log(f"error fetching database station with error: {e}", isWarning=True)
            self.log(f"---> please delete or update existing database", isWarning=True)

            return []

        finally:
            session.remove()
