from message_system_db_manager import DatabaseManager
from message_system_db_model import MessageAttachment, Attachment, P2PMessage
import json
import hashlib
import os


class DatabaseManagerAttachments(DatabaseManager):
    def __init__(self, event_manager):
        super().__init__(event_manager)


    def add_attachment(self, session, message, attachment_data):
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
        attachments = self.get_attachments_by_message_id(message_id)
        return json.dumps(attachments)

    def get_attachment_by_sha512(self, hash_sha512):
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
