# database_manager.py
import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from threading import local
from message_system_db_model import Base, Station, Status, Attachment, P2PMessage
from datetime import datetime
import json
import structlog

class DatabaseManager:
    def __init__(self, event_manger, uri='sqlite:///freedata-messages.db'):
        self.event_manager = event_manger

        self.engine = create_engine(uri, echo=False)
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
                "aborted"
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

    def get_or_create_station(self, session, callsign):
        station = session.query(Station).filter_by(callsign=callsign).first()
        if not station:
            station = Station(callsign=callsign)
            session.add(station)
            session.flush()  # To get the callsign immediately
        return station

    def get_or_create_status(self, session, status_name):
        status = session.query(Status).filter_by(name=status_name).first()
        if not status:
            status = Status(name=status_name)
            session.add(status)
            session.flush()  # To get the ID immediately
        return status

    def add_message(self, message_data):
        session = self.get_thread_scoped_session()
        try:
            # Create and add the origin and destination Stations
            origin = self.get_or_create_station(session, message_data['origin'])
            destination = self.get_or_create_station(session, message_data['destination'])

            # Create and add Status if provided
            status = None
            if 'status' in message_data:
                status = self.get_or_create_status(session, message_data['status'])

            # Parse the timestamp from the message ID
            timestamp = datetime.fromisoformat(message_data['id'].split('_')[2])
            # Create the P2PMessage instance
            new_message = P2PMessage(
                id=message_data['id'],
                origin_callsign=origin.callsign,
                destination_callsign=destination.callsign,
                body=message_data['body'],
                timestamp=timestamp,
                direction=message_data['direction'],
                status_id=status.id if status else None
            )

            # Process and add attachments
            for attachment_data in message_data.get('attachments', []):
                attachment = Attachment(
                    name=attachment_data['name'],
                    data_type=attachment_data['type'],
                    data=attachment_data['data']
                )
                new_message.attachments.append(attachment)

            session.add(new_message)
            session.commit()

            self.log(f"Added data to database: {new_message.id}")
            self.event_manager.freedata_message_db_change()
            return new_message.id
        except Exception as e:
            session.rollback()
            self.log(f"error adding new message to databse with error: {e}", isWarning=True)
            self.log(f"---> please delete or update existing database", isWarning=True)
        finally:
            session.remove()

    def get_all_messages(self):
        session = self.get_thread_scoped_session()
        try:
            messages = session.query(P2PMessage).all()
            return [message.to_dict() for message in messages]

        except Exception as e:
            self.log(f"error fetching database messages with error: {e}", isWarning=True)
            self.log(f"---> please delete or update existing database", isWarning=True)

            return []

        finally:
            session.remove()

    def get_all_messages_json(self):
        messages_dict = self.get_all_messages()
        messages_with_header = {'total_messages' : len(messages_dict), 'messages' : messages_dict}
        return json.dumps(messages_with_header)  # Convert to JSON string
