from message_system_db_manager import DatabaseManager
from message_system_db_model import MessageAttachment, Attachment, P2PMessage
import json
import hashlib
import os


class DatabaseManagerAttachments(DatabaseManager):
    def __init__(self, db_file=None):
        if not db_file:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, 'freedata-messages.db')
            db_file = 'sqlite:///' + db_path
        super().__init__(db_file)


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