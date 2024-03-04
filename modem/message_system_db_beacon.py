from message_system_db_manager import DatabaseManager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from threading import local
from message_system_db_model import Base, Beacon, Station, Status, Attachment, P2PMessage
from datetime import timezone, timedelta, datetime
import os

class DatabaseManagerBeacon(DatabaseManager):
    def __init__(self, db_file=None):
        if not db_file:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, 'freedata-messages.db')
            db_file = 'sqlite:///' + db_path

        super().__init__(db_file)

    def add_beacon(self, timestamp, callsign, snr, gridsquare):
        session = None
        try:
            session = self.get_thread_scoped_session()
            # Ensure the station exists or create it, and get the station object
            station = self.get_or_create_station(callsign, session)
            # Initialize location as an empty dict if None
            if not station.location:
                station.location = {}

            # Now, check and update the station's location with gridsquare if it has changed
            if station.location.get('gridsquare') != gridsquare:
                self.log(f"Updating location for {callsign}")
                station.location['gridsquare'] = gridsquare  # Update directly without re-serialization
                session.flush()

            # Now, add the beacon
            new_beacon = Beacon(timestamp=timestamp, snr=snr, callsign=callsign)
            session.add(new_beacon)
            session.commit()
            self.log(f"Added beacon for {callsign}")

        except Exception as e:
            self.log(f"An error occurred while adding beacon for {callsign}: {e}", isWarning=True)
            if session:
                session.rollback()
        finally:
            if session and not session.is_active:
                session.remove()

    def get_beacons_by_callsign(self, callsign):
        session = self.get_thread_scoped_session()
        try:
            # Query the station by callsign
            station = session.query(Station).filter_by(callsign=callsign).first()
            if station:
                # Access the beacons directly thanks to the back_populated relationship
                beacons = station.beacons
                # Convert beacon objects to a dictionary if needed, or directly return the list
                beacons_data = [{
                    'id': beacon.id,
                    'timestamp': beacon.timestamp.isoformat(),
                    'snr': beacon.snr,
                    'gridsquare': station.location.get('gridsquare') if station.location else None
                } for beacon in beacons]
                return beacons_data
            else:
                self.log(f"No station found with callsign {callsign}")
                return []
        except Exception as e:
            self.log(f"An error occurred while fetching beacons for callsign {callsign}: {e}", isWarning=True)
            return []
        finally:
            session.remove()

    def get_all_beacons(self):
        session = None
        try:
            session = self.get_thread_scoped_session()
            # Query all beacons
            beacons_query = session.query(Beacon).all()

            # Optionally format the result for easier consumption
            beacons_list = []
            for beacon in beacons_query:
                # Fetch the associated station for each beacon to get the 'gridsquare' information
                station = session.query(Station).filter_by(callsign=beacon.callsign).first()
                gridsquare = station.location.get('gridsquare') if station and station.location else None

                beacons_list.append({
                    'id': beacon.id,
                    'timestamp': beacon.timestamp.isoformat(),
                    'snr': beacon.snr,
                    'callsign': beacon.callsign,
                    'gridsquare': gridsquare
                })

            return beacons_list

        except Exception as e:
            self.log(f"An error occurred while fetching all beacons: {e}", isWarning=True)
            return []  # Return an empty list or handle the error as appropriate
        finally:
            if session and not session.is_active:
                session.remove()

    def beacon_cleanup_older_than_days(self, days):
        session = None
        try:
            session = self.get_thread_scoped_session()
            # Calculate the threshold timestamp
            older_than_timestamp = datetime.now(timezone.utc) - timedelta(days=days)

            # Query and delete beacons older than the calculated timestamp
            delete_query = session.query(Beacon).filter(Beacon.timestamp < older_than_timestamp)
            deleted_count = delete_query.delete(synchronize_session='fetch')
            session.commit()

            self.log(f"Deleted {deleted_count} beacons older than {days} days")
            return deleted_count

        except Exception as e:
            self.log(f"An error occurred during beacon cleanup: {e}", isWarning=True)
            if session:
                session.rollback()
            return 0  # Return 0 or handle the error as appropriate
        finally:
            if session and not session.is_active:
                session.remove()