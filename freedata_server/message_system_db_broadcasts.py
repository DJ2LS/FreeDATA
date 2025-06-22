from message_system_db_manager import DatabaseManager
from message_system_db_attachments import DatabaseManagerAttachments
from message_system_db_model import Status, BroadcastMessage
from message_system_db_station import DatabaseManagerStations
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import json
import os
from exceptions import MessageStatusError
import helpers
class DatabaseManagerBroadcasts(DatabaseManager):

    def __init__(self, ctx):
        super().__init__(ctx)

        self.stations_manager = DatabaseManagerStations(self.ctx)

    def process_broadcast_message(
            self,
            id: str,
            origin: str,
            burst_index: int,
            burst_data: str,
            total_bursts: int,
            checksum: str,
            repairing_callsigns: dict = None,
            domain: str = None,
            gridsquare: str = None,
            msg_type: str = None,
            received_at: datetime = None,
            expires_at: datetime = None,
            priority: int = 1,
            is_read: bool = True,
            status: str = "queued",
            error_reason: str = None
    ) -> bool:
        """
        Handles both creation of a new broadcast message and addition of bursts.

        If the message does not exist, it will be created.
        If it exists, the burst will be added.
        When all bursts are present, the final payload will be assembled and CRC checked.
        """
        session = self.get_thread_scoped_session()
        try:
            # Try to find existing message
            msg = session.query(BroadcastMessage).filter_by(id=id).first()

            if not msg:
                # Create station and status
                origin_station = self.stations_manager.get_or_create_station(origin, session)
                status_obj = self.get_or_create_status(session, status) if status else None
                received_at = received_at or datetime.utcnow()

                # New message
                msg = BroadcastMessage(
                    id=id,
                    origin=origin_station.callsign,
                    repairing_callsigns=repairing_callsigns,
                    domain=domain,
                    gridsquare=gridsquare,
                    priority=priority,
                    is_read=is_read,
                    payload_size=0,
                    payload_data={"bursts": {str(burst_index): burst_data}},
                    msg_type=msg_type,
                    total_bursts=total_bursts,
                    checksum=checksum,
                    received_at=received_at,
                    expires_at=expires_at,
                    status_id=status_obj.id if status_obj else None,
                    error_reason=error_reason
                )
                session.add(msg)
                self.log(f"Created new broadcast message {id}")

            else:
                # Add burst to existing message
                if not msg.payload_data:
                    msg.payload_data = {}

                if "bursts" not in msg.payload_data:
                    msg.payload_data["bursts"] = {}

                msg.payload_data["bursts"][str(burst_index)] = burst_data
                self.log(f"Added burst {burst_index} to message {id}")

            # Check for final assembly
            received = msg.payload_data["bursts"]
            total = msg.total_bursts or 0

            if total > 0 and len(received) == total and all(str(i) in received for i in range(total)):
                ordered = [received[str(i)] for i in range(total)]
                final = "".join(ordered)

                # CRC check
                crc = helpers.get_crc_24(final)
                if msg.checksum is None:
                    self.log(f"Missing checksum for {id}", isWarning=True)
                elif crc != msg.checksum:
                    self.log(f"Checksum mismatch for {id}: expected {msg.checksum}, got {crc}", isWarning=True)
                else:
                    msg.payload_data["final"] = final
                    msg.payload_size = len(final.encode("utf-8"))
                    self.log(f"Final payload assembled and verified for {id}")

            session.commit()
            self.ctx.event_manager.freedata_message_db_change(message_id=msg.id)
            return True

        except Exception as e:
            session.rollback()
            self.log(f"Error processing broadcast message {id}: {e}", isWarning=True)
            return False

        finally:
            session.remove()
