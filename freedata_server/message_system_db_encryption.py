from sqlalchemy.exc import SQLAlchemyError
from freedata_server.message_system_db_manager import DatabaseManager
from freedata_server.message_system_db_model import PendingEncryptedMessage, P2PMessage, Status


class DatabaseManagerEncryption(DatabaseManager):
    """Database operations for encrypted messaging.

    Keeps received messages that can't be decrypted yet (no or wrong key) and
    tracks outgoing messages waiting for a key (status "key_required").
    """

    KEY_REQUIRED_STATUS = "key_required"

    def add_pending(self, callsign, data, statistics=None, frequency=None):
        """Stores a received, still encrypted message until its key is entered.

        Returns:
            int or None: The id of the pending entry, None on error.
        """
        session = self.get_thread_scoped_session()
        try:
            if not isinstance(frequency, int):
                frequency = None
            pending = PendingEncryptedMessage(
                callsign=callsign, data=bytes(data), statistics=statistics, frequency=frequency
            )
            session.add(pending)
            session.commit()
            self.log(f"Stored encrypted message from {callsign} until the key is available")
            return pending.id
        except SQLAlchemyError as e:
            session.rollback()
            self.log(f"Failed to store encrypted message from {callsign}: {e}", isWarning=True)
            return None
        finally:
            session.remove()

    def get_pending(self, callsign):
        """Returns the pending encrypted messages of a station as a list of dicts
        with id, data, statistics and frequency, oldest first."""
        session = self.get_thread_scoped_session()
        try:
            rows = (
                session.query(PendingEncryptedMessage)
                .filter_by(callsign=callsign)
                .order_by(PendingEncryptedMessage.id)
                .all()
            )
            return [
                {"id": r.id, "data": r.data, "statistics": r.statistics or {}, "frequency": r.frequency} for r in rows
            ]
        except SQLAlchemyError as e:
            self.log(f"Failed to read encrypted messages from {callsign}: {e}", isWarning=True)
            return []
        finally:
            session.remove()

    def count_pending(self, callsign):
        session = self.get_thread_scoped_session()
        try:
            return session.query(PendingEncryptedMessage).filter_by(callsign=callsign).count()
        except SQLAlchemyError as e:
            self.log(f"Failed to count encrypted messages from {callsign}: {e}", isWarning=True)
            return 0
        finally:
            session.remove()

    def delete_pending(self, pending_id):
        session = self.get_thread_scoped_session()
        try:
            session.query(PendingEncryptedMessage).filter_by(id=pending_id).delete()
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            self.log(f"Failed to delete encrypted message {pending_id}: {e}", isWarning=True)
            return False
        finally:
            session.remove()

    def _key_required_query(self, session, callsign):
        status = session.query(Status).filter_by(name=self.KEY_REQUIRED_STATUS).first()
        if not status:
            return None
        return session.query(P2PMessage).filter_by(
            status_id=status.id, destination_callsign=callsign, direction="transmit"
        )

    def count_key_required(self, callsign):
        """Number of outgoing messages to a station that wait for its key."""
        session = self.get_thread_scoped_session()
        try:
            query = self._key_required_query(session, callsign)
            return query.count() if query is not None else 0
        except SQLAlchemyError as e:
            self.log(f"Failed to count messages waiting for a key: {e}", isWarning=True)
            return 0
        finally:
            session.remove()

    def requeue_key_required(self, callsign):
        """Puts outgoing messages that waited for a station's key back in the queue.

        Returns:
            int: The number of re-queued messages.
        """
        session = self.get_thread_scoped_session()
        try:
            query = self._key_required_query(session, callsign)
            if query is None:
                return 0
            messages = query.all()
            if messages:
                queued = self.get_or_create_status(session, "queued")
                for message in messages:
                    message.status_id = queued.id
                session.commit()
                self.ctx.event_manager.freedata_message_db_change()
            return len(messages)
        except SQLAlchemyError as e:
            session.rollback()
            self.log(f"Failed to re-queue messages for {callsign}: {e}", isWarning=True)
            return 0
        finally:
            session.remove()
