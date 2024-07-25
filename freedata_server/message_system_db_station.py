from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from message_system_db_model import Station
from message_system_db_manager import DatabaseManager
import os


class DatabaseManagerStations(DatabaseManager):
    def __init__(self, event_manager):
        super().__init__(event_manager)

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

    def update_station_info(self, callsign, new_info):
        """
        Updates the information of a station identified by its callsign.

        Args:
            callsign (str): The callsign of the station to update.
            new_info (str): The new information to store in the 'info' column.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        session = self.get_thread_scoped_session()
        try:
            station = session.query(Station).filter_by(callsign=callsign).first()
            if station:
                station.info = new_info
                session.commit()
                return True
            else:
                self.log(f"No station found with callsign {callsign}", isWarning=True)
                return False
        except SQLAlchemyError as e:
            session.rollback()
            self.log(f"Failed to update station {callsign} with error: {e}", isError=True)
            return False
        finally:
            session.remove()
