from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified
from freedata_server.message_system_db_model import Station
from freedata_server.message_system_db_manager import DatabaseManager


class DatabaseManagerStations(DatabaseManager):
    """Manages database operations for stations.

    This class extends the DatabaseManager and provides methods for
    retrieving, creating, and updating station information in the database.
    It handles database sessions and logging.
    """

    def __init__(self, ctx):
        """Initializes DatabaseManagerStations.

        Args:
            event_manager (EventManager): The event manager instance.
        """
        super().__init__(ctx)

    def get_station(self, callsign):
        """
        Retrieves a station by its callsign.

        Returns:
            dict or None: The station as a dictionary, or None if not found or on error.
        """
        session = self.get_thread_scoped_session()
        try:
            station = session.query(Station).filter_by(callsign=callsign).first()
            if station:
                return station.to_dict()
            else:
                self.log(f"No data found: {callsign}")
                return None
        except Exception as e:
            self.log(f"error fetching database station with error: {e}", isWarning=True)
            self.log("---> please delete or update existing database", isWarning=True)

            return None

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
            station = self.get_or_create_station(callsign, session)

            if station:
                station.info = new_info
                session.commit()
                return True
            else:
                self.log(f"No station found with callsign {callsign}", isWarning=True)
                return False
        except SQLAlchemyError as e:
            session.rollback()
            self.log(f"Failed to update station {callsign} with error: {e}", isWarning=True)
            return False
        finally:
            session.remove()

    def is_encryption_enabled(self, callsign):
        """Returns True if messages to this station are to be encrypted."""
        session = self.get_thread_scoped_session()
        try:
            station = session.query(Station).filter_by(callsign=callsign).first()
            return bool(station and station.encryption_enabled)
        except SQLAlchemyError as e:
            self.log(f"Failed to read encryption setting of {callsign}: {e}", isWarning=True)
            return False
        finally:
            session.remove()

    def set_encryption_enabled(self, callsign, enabled):
        """Turns encryption for a station on or off, creating the station if needed.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        session = self.get_thread_scoped_session()
        try:
            station = self.get_or_create_station(callsign, session)
            if not station:
                return False
            station.encryption_enabled = bool(enabled)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            self.log(f"Failed to set encryption for {callsign}: {e}", isWarning=True)
            return False
        finally:
            session.remove()

    def update_station_location(self, callsign, gridsquare):
        """
        Updates the location information of a station identified by its callsign.

        Args:
            callsign (str): The callsign of the station to update.
            gridsquare (str): The new gridsquare to store in the 'location' column.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        session = self.get_thread_scoped_session()
        try:
            # Ensure the station exists or create it, and get the station object
            station = self.get_or_create_station(callsign, session)

            if station:
                # Initialize location as an empty dict if None
                if not station.location:
                    station.location = {}

                # Update the station's location with gridsquare if it has changed
                if station.location.get("gridsquare") != gridsquare:
                    self.log(f"Updating location for {callsign}")
                    station.location["gridsquare"] = gridsquare
                    # plain JSON column: in-place changes are not tracked, so flag it explicitly
                    flag_modified(station, "location")
                    session.flush()
                else:
                    self.log(f"No changes needed for {callsign}'s location")

                session.commit()
                return True
            else:
                self.log(f"No station found with callsign {callsign}", isWarning=True)
                return False
        except SQLAlchemyError as e:
            session.rollback()
            self.log(f"Failed to update location for station {callsign} with error: {e}", isWarning=True)
            return False
        finally:
            session.remove()
