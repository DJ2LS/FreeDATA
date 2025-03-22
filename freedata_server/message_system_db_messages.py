from message_system_db_manager import DatabaseManager
from message_system_db_attachments import DatabaseManagerAttachments
from message_system_db_model import Status, P2PMessage
from message_system_db_station import DatabaseManagerStations
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import json
import os
from exceptions import MessageStatusError

class DatabaseManagerMessages(DatabaseManager):
    """Manages database operations for P2P messages.

    This class extends the DatabaseManager and provides methods for
    managing P2P messages in the database, including adding, retrieving,
    updating, deleting messages, handling attachments, and managing
    message statuses.
    """
    def __init__(self, event_manager):
        """Initializes DatabaseManagerMessages.

        Args:
            event_manager (EventManager): The event manager instance.
        """
        super().__init__(event_manager)
        self.attachments_manager = DatabaseManagerAttachments(event_manager)
        self.stations_manager = DatabaseManagerStations(event_manager)

    def add_message(self, message_data, statistics, direction='receive', status=None, is_read=True, frequency=None):
        """Adds a new P2P message to the database.

        This method adds a new P2P message record to the database,
        including its associated attachments. It handles station creation,
        status management, timestamp parsing, and attachment processing.
        It also logs the addition and triggers a database change event.

        Args:
            message_data (dict): A dictionary containing the message data.
            statistics (dict): A dictionary containing message statistics.
            direction (str, optional): The direction of the message ('send' or 'receive'). Defaults to 'receive'.
            status (str, optional): The status of the message. Defaults to None.
            is_read (bool, optional): Whether the message has been read. Defaults to True.
            frequency (float, optional): The frequency of the message. Defaults to None.

        Returns:
            str or None: The message ID if successfully added, None otherwise.
        """
        session = self.get_thread_scoped_session()
        try:
            # Create and add the origin and destination Stations
            origin = self.stations_manager.get_or_create_station(message_data['origin'], session)
            destination = self.stations_manager.get_or_create_station(message_data['destination'], session)

            # Create and add Status if provided
            if status:
                status = self.get_or_create_status(session, status)

            # Parse the timestamp from the message ID
            timestamp = datetime.fromisoformat(message_data['id'].split('_')[2])

            if frequency and frequency not in ['---']:
                statistics["frequency"] = frequency

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
                statistics=statistics            )

            session.add(new_message)

            # Process and add attachments
            if 'attachments' in message_data:
                for attachment_data in message_data['attachments']:
                    self.attachments_manager.add_attachment(session, new_message, attachment_data)

            session.commit()
            self.log(f"Added data to database: {new_message.id}")
            self.event_manager.freedata_message_db_change(message_id=new_message.id)
            return new_message.id
        except IntegrityError as e:
            session.rollback()  # Roll back the session to a clean state
            self.log(f"Message with ID {message_data['id']} already exists in the database.", isWarning=True)
            return None

        except Exception as e:
            session.rollback()
            self.log(f"error adding new message to database with error: {e}", isWarning=True)
            return None  # Return None to indicate an error

        finally:
            session.remove()

    def get_all_messages(self, filters=None):
        """Retrieves all P2P messages from the database, optionally filtered.

        This method retrieves all P2P messages from the database. It
        supports optional filtering based on criteria such as message ID,
        callsign (origin, via, or destination), direction, etc. The
        results are returned as a list of dictionaries, each representing
        a message. It handles database errors and logs appropriate
        messages.

        Args:
            filters (dict, optional): A dictionary of filter criteria.
                Available filters include 'id', 'callsign',
                'origin_callsign', 'via_callsign',
                'destination_callsign', and 'direction'. Defaults to
                None.

        Returns:
            list: A list of dictionaries, each representing a message, or
            an empty list if an error occurs or no messages match the
            filters.
        """
        session = self.get_thread_scoped_session()
        try:
            query = session.query(P2PMessage)

            if filters:
                for key, value in filters.items():
                    if key == 'id':
                        query = query.filter(P2PMessage.id == value)
                    elif key == 'callsign':
                        query = query.filter(
                            (P2PMessage.origin_callsign.contains(value)) |
                            (P2PMessage.via_callsign.contains(value)) |
                            (P2PMessage.destination_callsign.contains(value))
                        )
                    elif key in ['origin_callsign', 'via_callsign', 'destination_callsign', 'direction']:
                        query = query.filter(getattr(P2PMessage, key).contains(value))

            messages = query.all()
            return [message.to_dict() for message in messages]

        except Exception as e:
            self.log(f"error fetching database messages with error: {e}", isWarning=True)
            self.log(f"---> please delete or update existing database", isWarning=True)

            return []

        finally:
            session.remove()

    def get_all_messages_json(self, filters=None):
        """Retrieves all P2P messages as a JSON string, with a header.

        This method retrieves all messages, optionally filtered, and
        returns them as a JSON string. It includes a header containing the
        total number of messages. It calls get_all_messages to fetch the
        messages and then formats them as a JSON string.

        Args:
            filters (dict, optional): Filter criteria for messages. See
                get_all_messages for details. Defaults to None.

        Returns:
            dict: A dictionary containing the total number of messages and
            the messages themselves, formatted for JSON serialization.
        """
        messages_dict = self.get_all_messages(filters)
        messages_with_header = {'total_messages': len(messages_dict), 'messages': messages_dict}
        return messages_with_header

    def get_message_by_id(self, message_id):
        """Retrieves a P2P message by its ID.

        This method retrieves a specific P2P message from the database
        based on its ID. It returns the message data as a dictionary if
        found, or None if not found or if an error occurs. It handles
        database errors and logs appropriate messages.

        Args:
            message_id (str): The ID of the message to retrieve.

        Returns:
            dict or None: The message data as a dictionary if found, None
            otherwise.
        """
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
        """Retrieves a P2P message by ID as a JSON string.

        This method retrieves a message by its ID and returns it as a JSON
        string. It calls get_message_by_id to fetch the message and then
        serializes it to JSON.

        Args:
            message_id (str): The ID of the message.

        Returns:
            str: The message data as a JSON string, or an empty JSON object if not found.
        """
        message_dict = self.get_message_by_id(message_id)
        return json.dumps(message_dict)  # Convert to JSON string

    def get_message_by_id_adif(self, message_id):
        """
        Fetches a message by ID and returns it in ADIF format.

        Parameters:
        message_id (str): The ID of the message to retrieve.

        Returns:
        str: The ADIF formatted message, or None if the message is not found.
        """
        message_dict = self.get_message_by_id(message_id)
        if message_dict:
            try:
                # Extract fields from the message dictionary
                origin = message_dict.get("origin", "")
                destination = message_dict.get("destination", "")
                timestamp = message_dict.get("timestamp", "")
                direction = message_dict.get("direction", "").lower()  # Ensure case insensitivity
                status = message_dict.get("status", "")
                statistics = message_dict.get("statistics", {})

                # Determine the CALL based on the direction
                if direction == "receive":
                    call = origin.split("-")[0]  # Take the part before the "-" if it exists
                else:
                    call = destination.split("-")[0]  # Take the part before the "-" if it exists

                # Fetch station info
                origin_info = self.stations_manager.get_station(origin)

                # Parse the timestamp for QSO date and time, strip fractional seconds
                timestamp_clean = timestamp.split(".")[0]  # Remove fractional seconds
                qso_date = timestamp_clean.split("T")[0].replace("-", "")  # Extract the date part and remove hyphens

                # Extract the time and format it as HHMMSS
                time_on = datetime.strptime(timestamp_clean.split("T")[1], "%H:%M:%S").strftime("%H%M%S")

                # Calculate TIME_OFF by adding duration to TIME_ON
                duration = statistics.get("duration", 0.0)  # Duration in seconds
                time_on_obj = datetime.strptime(timestamp_clean.split("T")[1],
                                                "%H:%M:%S")  # Parse time_on as a datetime object
                time_off_obj = time_on_obj + timedelta(seconds=duration)
                time_off = time_off_obj.strftime("%H%M%S")  # Format time_off back to HHMMSS format

                # Set ADIF Fields
                mode = "DYNAMIC"
                submode = "FREEDATA"
                comment = f"QSO via FreeDATA RF-Chat"

                # Gridsquare handling
                print(origin_info)
                if origin_info and "location" in origin_info and origin_info["location"] is not None:
                    print(origin_info["location"])
                    grid = origin_info["location"].get("gridsquare", "")
                else:
                    grid = ""

                # Extract and adjust the frequency (Hz to MHz)
                frequency_hz = statistics.get("frequency")  # Get the frequency, may be None
                if frequency_hz is not None:
                    try:
                        # Convert frequency_hz to float if it's a string
                        frequency_value = float(frequency_hz)
                    except ValueError:
                        frequency_value = 0.0
                    frequency_mhz = round(frequency_value / 1_000_000, 3)  # Convert Hz to MHz
                    frequency_str = str(frequency_mhz)
                else:
                    frequency_str = "14.000000"  # Default if frequency is missing

                # Construct the ADIF message
                adif_fields = [
                    f"<CALL:{len(call)}>{call}",
                    f"<QSO_DATE:{len(qso_date)}>{qso_date}",
                    f"<TIME_ON:{len(time_on)}>{time_on}",
                    f"<TIME_OFF:{len(time_off)}>{time_off}",  # Include TIME_OFF
                    f"<FREQ:{len(frequency_str)}>{frequency_str}",  # Frequency in MHz
                    f"<MODE:{len(mode)}>{mode}",
                    f"<SUBMODE:{len(submode)}>{submode}",
                    f"<COMMENT:{len(comment)}>{comment}",
                    f"<GRIDSQUARE:{len(grid)}>{grid}",
                    #f"<DIRECTION:{len(direction)}>{direction}",
                    #f"<STATUS:{len(status)}>{status}",
                    #f"<DURATION:{len(str(duration))}>{duration}",
                    "<EOR>"
                ]

                return "".join(adif_fields)

            except Exception as e:
                self.log(f"Error converting message {message_id} to ADIF: {e}", isWarning=True)
                return None
        else:
            self.log(f"Message with ID {message_id} not found.", isWarning=True)
            return None

    def delete_message(self, message_id):
        """Deletes a P2P message from the database.

        This method deletes a P2P message and its associated attachments
        from the database. It first deletes the attachment links (and the
        attachments themselves if they are not linked to other
        messages). Then, it deletes the message record and logs the
        deletion, triggering a database change event.

        Args:
            message_id (str): The ID of the message to delete.

        Returns:
            dict: A dictionary indicating the status of the deletion
            ('success' or 'failure') and a corresponding message.
        """

        # Delete attachment links associated with this message.
        # This call will check each attachment link:
        # - If the attachment is used by other messages, only the link is removed.
        # - If the attachment is solely linked to this message, the attachment record is deleted.
        self.attachments_manager.delete_attachments_by_message_id(message_id)


        session = self.get_thread_scoped_session()
        try:
            message = session.query(P2PMessage).filter_by(id=message_id).first()
            if message:

                if message.to_dict()["status"] in ["transmitting", "queued"]:
                    raise MessageStatusError("Message is queued or transmitting")

                session.delete(message)
                session.commit()

                self.log(f"Deleted: {message_id}")
                self.event_manager.freedata_message_db_change(message_id=message_id)
                return {'status': 'success', 'message': f'Message {message_id} deleted'}
            else:
                return {'status': 'failure', 'message': 'Message not found'}
        except Exception as e:
            session.rollback()
            self.log(f"Error deleting message with ID {message_id}: {e}", isWarning=True)
            return {'status': 'failure', 'message': 'error deleting message'}
        except MessageStatusError as e:
            session.rollback()
            self.log(f"Error deleting message with ID {message_id}: {e}", isWarning=True)
            return {'status': 'failure', 'message': e}

        finally:
            session.remove()

    def update_message(self, message_id, update_data, frequency=None):
        """Updates a P2P message in the database.

        This method updates an existing P2P message in the database with
        the provided data. It allows updating various fields of the
        message, including body, status, statistics, read status, attempt
        count, and priority. It handles database errors, performs
        rollbacks if necessary, and triggers a database change event upon
        successful update.

        Args:
            message_id (str): The ID of the message to update.
            update_data (dict): A dictionary containing the fields to
                update and their new values.
            frequency (float, optional): The frequency to update in
                statistics. Defaults to None.

        Returns:
            dict: A dictionary indicating the status of the update
            ('success' or 'failure') and a corresponding message.
        """
        session = self.get_thread_scoped_session()
        try:
            message = session.query(P2PMessage).filter_by(id=message_id).first()
            if message:
                # Update fields of the message as per update_data
                for key, value in update_data.items():
                    if key == 'status':
                        setattr(message, key, self.get_or_create_status(session, value))
                    elif key == 'statistics':
                        statistics = value
                        if frequency and frequency not in ['---']:
                            statistics["frequency"] = frequency
                        setattr(message, key, statistics)
                    elif key in ['body', 'is_read', 'attempt', 'priority']:
                        setattr(message, key, value)

                session.commit()
                self.log(f"Updated: {message_id}")
                self.event_manager.freedata_message_db_change(message_id=message_id)
                return {'status': 'success', 'message': f'Message {message_id} updated'}
            else:
                return {'status': 'failure', 'message': 'Message not found'}

        except Exception as e:
            session.rollback()
            self.log(f"Error updating message with ID {message_id}: {e}", isWarning=True)
            return {'status': 'failure', 'message': 'error updating message'}

        finally:
            session.remove()

    def get_first_queued_message(self):
        """Retrieves the first queued P2P message from the database.

        This method retrieves the oldest queued message from the database
        based on its timestamp. It returns the message data as a
        dictionary if found, or None if no queued messages are found or
        an error occurs. It handles cases where the "queued" status is
        not found and logs appropriate messages.

        Returns:
            dict or None: The data of the first queued message as a
            dictionary, or None if no queued messages are found or if an
            error occurs.
        """
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
        """Increments the attempt count for a message.

        This method increments the attempt count for a given message in
        the database. It handles database sessions and transactions,
        committing changes only if it created the session. It logs
        messages indicating success, failure (message not found), or
        errors during the process.

        Args:
            message_id (str): The ID of the message to update.
            session (scoped_session, optional): An existing database
                session. Defaults to None.
        """
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


    def set_message_to_queued_for_callsign(self, callsign):
        """Sets the first failed message for a callsign to 'queued'.

        This method finds the first message in the database with the given
        destination callsign that has a 'failed' status and fewer than 10
        attempts. If such a message is found, its status is changed to
        'queued', its attempt count is incremented, and the changes are
        committed to the database. It handles cases where the 'failed' or
        'queued' statuses are not found and logs appropriate messages.

        Args:
            callsign (str): The destination callsign of the message.

        Returns:
            dict: A dictionary indicating the status ('success' or
            'failure') and a message describing the outcome.
        """
        session = self.get_thread_scoped_session()
        try:
            # Find the 'failed' status object
            failed_status = session.query(Status).filter_by(name='failed').first()
            # Find the 'queued' status object
            queued_status = session.query(Status).filter_by(name='queued').first()

            # Ensure both statuses are found
            if not failed_status or not queued_status:
                self.log("Failed or queued status not found", isWarning=True)
                return {'status': 'failure', 'message': 'Failed or queued status not found'}

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
                return {'status': 'success', 'message': f'message(s) set to queued'}
            else:
                return {'status': 'failure', 'message': 'No eligible messages found'}
        except Exception as e:
            session.rollback()
            self.log(f"An error occurred while setting messages to queued: {e}", isWarning=True)
            return {'status': 'failure', 'message': 'error setting message to queued'}
        finally:
            session.remove()
