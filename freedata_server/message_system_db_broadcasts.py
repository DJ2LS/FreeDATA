from message_system_db_manager import DatabaseManager
from message_system_db_attachments import DatabaseManagerAttachments
from message_system_db_model import Status, BroadcastMessage
from message_system_db_station import DatabaseManagerStations
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime, timedelta
import json
import os
from datetime import timezone
from exceptions import MessageStatusError
import helpers
import base64



class DatabaseManagerBroadcasts(DatabaseManager):

    def __init__(self, ctx):
        super().__init__(ctx)

        self.stations_manager = DatabaseManagerStations(self.ctx)

    def process_broadcast_message(
            self,
            id: str,
            origin: str,
            timestamp: datetime,
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
            nexttransmission_at: datetime = None,
            priority: int = 1,
            is_read: bool = True,
            direction: str = None,
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

            self.log(f"Broadcast ID: {id}, Burst: {burst_index}, Exists: {'yes' if msg else 'no'}")

            if not msg:
                # Create station and status
                origin_station = self.stations_manager.get_or_create_station(origin, session)
                status_obj = self.get_or_create_status(session, status) if status else None

                # New message
                msg = BroadcastMessage(
                    id=id,
                    origin=origin_station.callsign,
                    timestamp=timestamp,
                    repairing_callsigns=repairing_callsigns,
                    domain=domain,
                    gridsquare=gridsquare,
                    priority=priority,
                    is_read=is_read,
                    direction=direction,
                    payload_size=0,
                    payload_data={"bursts": {str(burst_index): burst_data}},
                    msg_type=msg_type,
                    total_bursts=total_bursts,
                    checksum=checksum,
                    received_at=received_at,
                    nexttransmission_at=nexttransmission_at,
                    expires_at=expires_at,
                    status_id=status_obj.id if status_obj else None,
                    error_reason=error_reason
                )
                session.add(msg)
                self.log(f"Created new broadcast message {id}")
                self.ctx.event_manager.freedata_message_db_change(message_id=id)

            else:
                # Add burst to existing message
                if not msg.payload_data:
                    msg.payload_data = {}

                if "bursts" not in msg.payload_data:
                    msg.payload_data["bursts"] = {}

                msg.payload_data["bursts"][str(burst_index)] = burst_data
                flag_modified(msg, "payload_data")

                self.log(f"Added burst {burst_index} to message {id}")
                self.ctx.event_manager.freedata_message_db_change(message_id=id)
            # Check for final assembly
            received = msg.payload_data["bursts"]
            total = msg.total_bursts

            if total > 0 and len(received) == total and all(str(i) in received for i in range(1, total + 1)):

                ordered = [received[str(i)] for i in range(1, total + 1)]
                final_bytes = b"".join(base64.b64decode(b64part) for b64part in ordered)

                # CRC check
                crc = helpers.get_crc_24(final_bytes).hex()

                if msg.checksum is None:
                    self.log(f"Missing checksum for {id}", isWarning=True)
                elif crc != msg.checksum:
                    self.log(f"Checksum mismatch for {id}: expected {msg.checksum}, got {crc}", isWarning=True)
                    status_obj = self.get_or_create_status(session, "failed_checksum")
                    msg.status_id = status_obj.id

                else:
                    msg.payload_data["final"] = base64.b64encode(final_bytes).decode()
                    msg.payload_size = len(final_bytes)

                    status_obj = self.get_or_create_status(session, "received")
                    msg.status_id = status_obj.id


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

    def get_all_broadcasts_json(self) -> list:
        """
        Returns all broadcast messages in JSON-serializable dict format.
        """
        session = self.get_thread_scoped_session()
        try:
            messages = session.query(BroadcastMessage).all()
            result = []

            for msg in messages:
                result.append({
                    "id": msg.id,
                    "origin": msg.origin,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    "repairing_callsigns": msg.repairing_callsigns,
                    "domain": msg.domain,
                    "gridsquare": msg.gridsquare,
                    "frequency": msg.frequency,
                    "priority": msg.priority,
                    "is_read": msg.is_read,
                    "direction": msg.direction,
                    "payload_size": msg.payload_size,
                    "payload_data": msg.payload_data,
                    "msg_type": msg.msg_type,
                    "total_bursts": msg.total_bursts,
                    "checksum": msg.checksum,
                    "received_at": msg.received_at.isoformat() if msg.received_at else None,
                    "expires_at": msg.expires_at.isoformat() if msg.expires_at else None,
                    "nexttransmission_at": msg.nexttransmission_at.isoformat() if msg.nexttransmission_at else None,
                    "status": msg.status.name if msg.status else None,
                    "error_reason": msg.error_reason
                })

            return result

        except Exception as e:
            self.log(f"Error fetching broadcasts: {e}", isWarning=True)
            return []

        finally:
            session.remove()

    def get_broadcast_domains_json(self) -> dict:
        """
        Returns a JSON-compatible dictionary where each key is a domain (e.g. 'BB1AA-2'),
        and each value is a dict containing message stats for that domain.
        """
        session = self.get_thread_scoped_session()
        try:
            messages = (
                session.query(BroadcastMessage)
                .filter(BroadcastMessage.domain.isnot(None))
                .order_by(BroadcastMessage.timestamp.desc())
                .all()
            )

            result = {}
            for msg in messages:
                domain = msg.domain
                if domain not in result:
                    result[domain] = {
                        "message_count": 1,
                        "last_message_id": msg.id,
                        "last_message_timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                        "last_origin": msg.origin
                    }
                else:
                    result[domain]["message_count"] += 1

            return result

        except Exception as e:
            self.log(f"Error fetching domain summary: {e}", isWarning=True)
            return {}

        finally:
            session.remove()

    def get_broadcasts_per_domain_json(self, domain: str = None) -> dict:

        session = self.get_thread_scoped_session()
        try:
            query = session.query(BroadcastMessage).order_by(BroadcastMessage.timestamp.asc())

            if domain:
                query = query.filter(BroadcastMessage.domain == domain)

            messages = query.all()
            result = {}

            for msg in messages:
                d = msg.domain or "unknown"

                if domain and d != domain:
                    continue  # just in case

                if d not in result:
                    result[d] = []

                result[d].append({
                    "id": msg.id,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    "origin": msg.origin,
                    "gridsquare": msg.gridsquare,
                    "msg_type": msg.msg_type,
                    "payload_size": msg.payload_size,
                    "payload_data": msg.payload_data,
                    "direction": msg.direction,
                    "status": msg.status.name if msg.status else None,
                    "error_reason": msg.error_reason,
                    "received_at": msg.received_at.isoformat() if msg.received_at else None,
                    "nexttransmission_at": msg.nexttransmission_at.isoformat() if msg.nexttransmission_at else None,
                    "expires_at": msg.expires_at.isoformat() if msg.expires_at else None
                })

            return result

        except Exception as e:
            self.log(f"Error collecting broadcasts for domain '{domain}': {e}", isWarning=True)
            return {}

        finally:
            session.remove()

    def delete_broadcast_message_or_domain(self, id) -> dict:

        session = self.get_thread_scoped_session()
        try:
            msg = session.query(BroadcastMessage).filter_by(id=id).first()
            if msg:
                session.delete(msg)
                session.commit()
                self.log(f"Deleted broadcast message {id}")
                self.ctx.event_manager.freedata_message_db_change(message_id=id)
                return {
                    "status": "success",
                    "deleted": 1,
                    "type": "message",
                    "id": id
                }

            messages = session.query(BroadcastMessage).filter_by(domain=id).all()
            if messages:
                count = len(messages)
                for m in messages:
                    session.delete(m)
                session.commit()
                self.log(f"Deleted {count} messages from domain '{id}'")
                self.ctx.event_manager.freedata_message_db_change(message_id=id)
                return {
                    "status": "success",
                    "deleted": count,
                    "type": "domain",
                    "domain": id
                }

            return {
                "status": "error",
                "message": f"Neither broadcast message ID '{id}' nor domain found."
            }

        except Exception as e:
            session.rollback()
            self.log(f"Error deleting broadcast message or domain '{id}': {e}", isWarning=True)
            return {
                "status": "error",
                "message": str(e)
            }

        finally:
            session.remove()

    def check_missing_bursts(self):
        session = self.get_thread_scoped_session()
        try:
            one_minute_ago = datetime.now(timezone.utc) - timedelta(minutes=1)

            messages = (
                session.query(BroadcastMessage)
                .filter(
                    BroadcastMessage.direction == "receive",
                    BroadcastMessage.received_at < one_minute_ago,
                    BroadcastMessage.total_bursts > 0
                )
                .order_by(BroadcastMessage.received_at.asc())
                .all()
            )

            for msg in messages:
                if not msg.payload_data or "bursts" not in msg.payload_data:
                    continue

                # break if we reached maximum attempts
                if msg.attempts >= 30:
                    return None

                bursts = msg.payload_data["bursts"]
                total = msg.total_bursts

                if "final" in msg.payload_data:
                    continue  # bereits komplett

                missing = [
                    i for i in range(1, total + 1)
                    if str(i) not in bursts
                ]

                if missing:
                    return {
                        "id": msg.id,
                        "origin": msg.origin,
                        "domain": msg.domain,
                        "missing_bursts": missing,
                        "total_bursts": total,
                        "received_bursts": list(bursts.keys()),
                        "received_at": msg.received_at.isoformat() if msg.received_at else None
                    }

            return None

        except Exception as e:
            self.log(f"Fehler bei check_missing_bursts: {e}", isWarning=True)
            return None

        finally:
            session.remove()


    def get_broadcast_per_id(self, id):
        session = self.get_thread_scoped_session()
        try:
            msg = session.query(BroadcastMessage).filter_by(id=id).first()
            if not msg:
                return None

            return {
                "id": msg.id,
                "origin": msg.origin,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                "repairing_callsigns": msg.repairing_callsigns,
                "domain": msg.domain,
                "gridsquare": msg.gridsquare,
                "frequency": msg.frequency,
                "priority": msg.priority,
                "is_read": msg.is_read,
                "direction": msg.direction,
                "payload_size": msg.payload_size,
                "payload_data": msg.payload_data,
                "msg_type": msg.msg_type,
                "total_bursts": msg.total_bursts,
                "checksum": msg.checksum,
                "received_at": msg.received_at.isoformat() if msg.received_at else None,
                "expires_at": msg.expires_at.isoformat() if msg.expires_at else None,
                "nexttransmission_at": msg.nexttransmission_at.isoformat() if msg.nexttransmission_at else None,
                "status": msg.status.name if msg.status else None,
                "error_reason": msg.error_reason,
                "attempts": msg.attempts
            }

        except Exception as e:
            self.log(f"Error fetching broadcast by id '{id}': {e}", isWarning=True)
            return None

        finally:
            session.remove()

    def increment_attempts(self, message_id: str):
        session = self.get_thread_scoped_session()
        try:
            msg = session.query(BroadcastMessage).filter_by(id=message_id).first()
            if msg:
                msg.attempts = (msg.attempts or 0) + 1
                session.commit()
                self.log(f"Increased attempts for message {message_id} to {msg.attempts}")
            else:
                self.log(f"Message {message_id} not found", isWarning=True)
        except Exception as e:
            session.rollback()
            self.log(f"Error incrementing attempts for {message_id}: {e}", isWarning=True)
        finally:
            session.remove()
