from message_system_db_manager import DatabaseManager
from message_system_db_attachments import DatabaseManagerAttachments
from message_system_db_model import Status, P2PMessage
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json
import os


class DatabaseManagerMessages(DatabaseManager):
    def __init__(self, db_file=None):
        if not db_file:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, 'freedata-messages.db')
            db_file = 'sqlite:///' + db_path

        super().__init__(db_file)
        self.attachments_manager = DatabaseManagerAttachments(db_file)

    def add_message(self, message_data, statistics, direction='receive', status=None, is_read=True):
        session = self.get_thread_scoped_session()
        try:
            # Create and add the origin and destination Stations
            origin = self.get_or_create_station(message_data['origin'], session)
            destination = self.get_or_create_station(message_data['destination'], session)

            # Create and add Status if provided
            if status:
                status = self.get_or_create_status(session, status)

            # Parse the timestamp from the message ID
            timestamp = datetime.fromisoformat(message_data['id'].split('_')[2])
            # Create the P2PMessage instance
            new_message = P2PMessage(
                id=message_data['id'],
                origin_callsign=origin.callsign,
                destination_callsign=destination.callsign,
                body=message_data['body'],
                timestamp=timestamp,
                direction=direction,
                status_id=status.id if status else None,
                is_read=is_read,
                attempt=0,
                statistics=statistics
            )

            session.add(new_message)

            # Process and add attachments
            if 'attachments' in message_data:
                for attachment_data in message_data['attachments']:
                    self.attachments_manager.add_attachment(session, new_message, attachment_data)

            session.commit()
            self.log(f"Added data to database: {new_message.id}")
            self.event_manager.freedata_message_db_change()
            return new_message.id
        except IntegrityError as e:
            session.rollback()  # Roll back the session to a clean state
            self.log(f"Message with ID {message_data['id']} already exists in the database.", isWarning=True)
            return None  # or you might return the existing message's ID or details


        except Exception as e:
            session.rollback()
            self.log(f"error adding new message to database with error: {e}", isWarning=True)
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
        return messages_with_header

    def get_message_by_id(self, message_id):
        session = self.get_thread_scoped_session()
        try:
            message = session.query(P2PMessage).filter_by(id=message_id).first()
            if message:
                return message.to_dict()
            else:
                return None
        except Exception as e:
            self.log(f"Error fetching message with ID {message_id}: {e}", isWarning=True)
            return None
        finally:
            session.remove()

    def get_message_by_id_json(self, message_id):
        message_dict = self.get_message_by_id(message_id)
        return json.dumps(message_dict)  # Convert to JSON string

    def delete_message(self, message_id):
        session = self.get_thread_scoped_session()
        try:
            message = session.query(P2PMessage).filter_by(id=message_id).first()
            if message:
                session.delete(message)
                session.commit()
                self.log(f"Deleted: {message_id}")
                self.event_manager.freedata_message_db_change()
                return {'status': 'success', 'message': f'Message {message_id} deleted'}
            else:
                return {'status': 'failure', 'message': 'Message not found'}

        except Exception as e:
            session.rollback()
            self.log(f"Error deleting message with ID {message_id}: {e}", isWarning=True)
            return {'status': 'failure', 'message': str(e)}

        finally:
            session.remove()

    def update_message(self, message_id, update_data):
        session = self.get_thread_scoped_session()
        try:
            message = session.query(P2PMessage).filter_by(id=message_id).first()
            if message:
                # Update fields of the message as per update_data
                if 'body' in update_data:
                    message.body = update_data['body']
                if 'status' in update_data:
                    message.status = self.get_or_create_status(session, update_data['status'])
                if 'statistics' in update_data:
                    message.statistics = update_data['statistics']

                session.commit()
                self.log(f"Updated: {message_id}")
                self.event_manager.freedata_message_db_change()
                return {'status': 'success', 'message': f'Message {message_id} updated'}
            else:
                return {'status': 'failure', 'message': 'Message not found'}

        except Exception as e:
            session.rollback()
            self.log(f"Error updating message with ID {message_id}: {e}", isWarning=True)
            return {'status': 'failure', 'message': str(e)}

        finally:
            session.remove()

    def get_first_queued_message(self):
        session = self.get_thread_scoped_session()
        try:
            # Find the status object for "queued"
            queued_status = session.query(Status).filter_by(name='queued').first()
            if queued_status:
                # Query for the first (oldest) message with status "queued"
                message = session.query(P2PMessage)\
                    .filter_by(status=queued_status)\
                    .order_by(P2PMessage.timestamp)\
                    .first()
                if message:
                    self.log(f"Found queued message with ID {message.id}")
                    return message.to_dict()
                else:
                    return None
            else:
                self.log("Queued status not found", isWarning=True)
                return None
        except Exception as e:
            self.log(f"Error fetching the first queued message: {e}", isWarning=True)
            return None
        finally:
            session.remove()

    def increment_message_attempts(self, message_id, session=None):
        own_session = False
        if not session:
            session = self.get_thread_scoped_session()
            own_session = True
        try:
            message = session.query(P2PMessage).filter_by(id=message_id).first()
            if message:
                message.attempt += 1
                if own_session:
                    session.commit()
                self.log(f"Incremented attempt count for message {message_id}")
            else:
                self.log(f"Message with ID {message_id} not found")
        except Exception as e:
            if own_session:
                session.rollback()
            self.log(f"An error occurred while incrementing attempts for message {message_id}: {e}")
        finally:
            if own_session:
                session.remove()

    def mark_message_as_read(self, message_id):
        session = self.get_thread_scoped_session()
        try:
            message = session.query(P2PMessage).filter_by(id=message_id).first()
            if message:
                message.is_read = True
                session.commit()
                self.log(f"Marked message {message_id} as read")
            else:
                self.log(f"Message with ID {message_id} not found")
        except Exception as e:
            session.rollback()
            self.log(f"An error occurred while marking message {message_id} as read: {e}")
        finally:
            session.remove()

    def set_message_to_queued_for_callsign(self, callsign):
        session = self.get_thread_scoped_session()
        try:
            # Find the 'failed' status object
            failed_status = session.query(Status).filter_by(name='failed').first()
            # Find the 'queued' status object
            queued_status = session.query(Status).filter_by(name='queued').first()

            # Ensure both statuses are found
            if not failed_status or not queued_status:
                self.log("Failed or queued status not found", isWarning=True)
                return

            # Query for messages with the specified callsign, 'failed' status, and fewer than 10 attempts
            message = session.query(P2PMessage) \
                .filter(P2PMessage.destination_callsign == callsign) \
                .filter(P2PMessage.status_id == failed_status.id) \
                .filter(P2PMessage.attempt < 10) \
                .first()

            if message:
                # Increment attempt count using the existing function
                self.increment_message_attempts(message.id, session)

                message.status_id = queued_status.id
                self.log(f"Set message {message.id} to queued and incremented attempt")

                session.commit()
                return {'status': 'success', 'message': f'{len(message)} message(s) set to queued'}
            else:
                return {'status': 'failure', 'message': 'No eligible messages found'}
        except Exception as e:
            session.rollback()
            self.log(f"An error occurred while setting messages to queued: {e}", isWarning=True)
            return {'status': 'failure', 'message': str(e)}
        finally:
            session.remove()
