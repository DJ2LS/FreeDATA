from message_system_db_manager import DatabaseManager
from message_system_db_model import MessageAttachment, Attachment, P2PMessage
import json
import hashlib
import os


class DatabaseManagerAttachments(DatabaseManager):
    """Manages database operations for message attachments.

    This class extends the DatabaseManager and provides methods for adding,
    retrieving, and deleting message attachments in the database. It also
    handles orphaned attachments and database sessions.
    """
    def __init__(self, event_manager):
        """Initializes DatabaseManagerAttachments.

        Args:
            event_manager (EventManager): The event manager instance.
        """
        super().__init__(event_manager)


    def add_attachment(self, session, message, attachment_data):
        """Adds an attachment to the database and links it to a message.

        This method adds a new attachment to the database if it doesn't
        already exist, based on its SHA-512 hash. It then creates a link
        between the message and the attachment using the MessageAttachment
        association table. It handles cases where the attachment already
        exists and logs appropriate messages.

        Args:
            session: The database session object.
            message: The message object to link the attachment to.
            attachment_data (dict): A dictionary containing the attachment
                data, including 'name', 'type', 'data', and optionally
                'checksum_crc32'.

        Returns:
            Attachment: The Attachment object that was added or found.
        """
        hash_sha512 = hashlib.sha512(attachment_data['data'].encode()).hexdigest()
        existing_attachment = session.query(Attachment).filter_by(hash_sha512=hash_sha512).first()

        if not existing_attachment:
            attachment = Attachment(
                name=attachment_data['name'],
                data_type=attachment_data['type'],
                data=attachment_data['data'],
                checksum_crc32=attachment_data.get('checksum_crc32', ''),
                hash_sha512=hash_sha512
            )
            session.add(attachment)
            session.flush()  # Ensure the attachment is persisted and has an ID
            self.log(f"Added attachment to database: {attachment.name}")
        else:
            attachment = existing_attachment
            self.log(f"Attachment {attachment.name} already exists in database")

        # Link the message and the attachment through MessageAttachment
        link = MessageAttachment(message=message, attachment=attachment)
        session.add(link)
        self.log(f"Linked message with attachment: {attachment.name}")

        return attachment

    def get_attachments_by_message_id(self, message_id):
        """Retrieves attachments associated with a message ID.

        This method retrieves all attachments linked to a given message ID
        from the database. It returns a list of dictionaries, where each
        dictionary represents an attachment. It handles cases where no
        message or attachments are found and logs any database errors.

        Args:
            message_id: The ID of the message whose attachments are to be retrieved.

        Returns:
            list: A list of dictionaries, each representing an attachment,
            or an empty list if no attachments or message are found.
        """
        session = self.get_thread_scoped_session()
        try:
            # Fetch the message by its ID
            message = session.query(P2PMessage).filter_by(id=message_id).first()
            if message:
                # Navigate through the association to get attachments
                attachments = [ma.attachment.to_dict() for ma in message.message_attachments]
                return attachments
            else:
                return []
        except Exception as e:
            self.log(f"Error fetching attachments for message ID {message_id}: {e}", isWarning=True)
            return []
        finally:
            session.remove()

    def get_attachments_by_message_id_json(self, message_id):
        """Retrieves attachments for a message as a JSON string.

        This method retrieves attachments associated with a given message ID
        and returns them as a JSON-formatted string. It calls
        get_attachments_by_message_id to fetch the attachments and then
        serializes them to JSON.

        Args:
            message_id: The ID of the message.

        Returns:
            str: A JSON string representing the attachments.
        """
        attachments = self.get_attachments_by_message_id(message_id)
        return json.dumps(attachments)

    def get_attachment_by_sha512(self, hash_sha512):
        """Retrieves an attachment by its SHA-512 hash.

        This method queries the database for an attachment matching the
        provided SHA-512 hash. If found, it returns the attachment data as
        a dictionary; otherwise, it returns None. It handles potential
        database errors and logs appropriate messages.

        Args:
            hash_sha512 (str): The SHA-512 hash of the attachment to retrieve.

        Returns:
            dict or None: The attachment data as a dictionary if found,
            None otherwise.
        """
        session = self.get_thread_scoped_session()
        try:
            attachment = session.query(Attachment).filter_by(hash_sha512=hash_sha512).first()
            if attachment:
                return attachment.to_dict()
            else:
                self.log(f"No attachment found with SHA-512 hash: {hash_sha512}")
                return None
        except Exception as e:
            self.log(f"Error fetching attachment with SHA-512 hash {hash_sha512}: {e}", isWarning=True)
            return None
        finally:
            session.remove()

    def delete_attachments_by_message_id(self, message_id):
        """
        Deletes attachment associations for a given message ID.

        For each attachment linked to the message:
          - If the attachment is linked to more than one message, only the association for this message is deleted.
          - If the attachment is linked only to this message, both the association and the attachment record are deleted.

        Parameters:
            message_id (str): The ID of the message whose attachment associations should be deleted.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        session = self.get_thread_scoped_session()
        try:
            # Find all attachment associations for the given message ID.
            links = session.query(MessageAttachment).filter_by(message_id=message_id).all()
            if not links:
                self.log(f"No attachments linked with message ID {message_id} found.")
                return True

            for link in links:
                # Count how many associations exist for this attachment.
                link_count = session.query(MessageAttachment).filter_by(attachment_id=link.attachment_id).count()
                if link_count > 1:
                    # More than one link exists, so only remove the association.
                    session.delete(link)
                    self.log(
                        f"Deleted link for attachment '{link.attachment.name}' from message {message_id} (other links exist).")
                else:
                    # Only one link exists, so delete both the association and the attachment.
                    session.delete(link)
                    session.delete(link.attachment)
                    self.log(f"Deleted attachment '{link.attachment.name}' from message {message_id} (only link).")

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            self.log(f"Error deleting attachments for message ID {message_id}: {e}", isWarning=True)
            return False
        finally:
            session.remove()


    def clean_orphaned_attachments(self):
        """
        Checks for orphaned attachments in the database, i.e. attachments that have no
        MessageAttachment links to any messages. Optionally, deletes these orphaned attachments.

        Parameters:
            cleanup (bool): If True, deletes the orphaned attachments; if False, only returns them.

        Returns:
            If cleanup is False:
                list: A list of dictionaries representing the orphaned attachments.
            If cleanup is True:
                dict: A summary dictionary with the count of deleted attachments.
        """
        session = self.get_thread_scoped_session()
        try:
            orphaned = []
            # Get all attachments in the database.
            attachments = session.query(Attachment).all()
            for attachment in attachments:
                # Count the number of MessageAttachment links for this attachment.
                link_count = session.query(MessageAttachment).filter_by(attachment_id=attachment.id).count()
                if link_count == 0:
                    orphaned.append(attachment)

            for attachment in orphaned:
                self.log(f"Deleting orphaned attachment: {attachment.name}")
                session.delete(attachment)
            self.log(f"Checked for orphaned attachments")
            session.commit()
            return {'status': 'success', 'deleted_count': len(orphaned)}
        except Exception as e:
            session.rollback()
            self.log(f"Error checking orphaned attachments: {e}", isWarning=True)
            return None
        finally:
            session.remove()
