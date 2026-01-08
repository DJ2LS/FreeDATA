# file for handling received data
from norm.norm_transmission import NormTransmission
from message_system_db_broadcasts import DatabaseManagerBroadcasts
import base64
from datetime import datetime, timezone, timedelta

class NormTransmissionIRS(NormTransmission):
    MAX_PAYLOAD_SIZE = 26

    def __init__(self, ctx, frame):
        self.ctx = ctx

        if not self.ctx.config_manager.config["EXP"]["enable_groupchat"]:
            return

        print("burst:", frame)


        is_last, msg_type, priority = self.decode_flags(frame["flag"])
        burst_number, total_bursts = self.decode_burst_info(frame["burst_info"])
        payload_size = frame["payload_size"]
        payload_data = frame["payload_data"]


        if total_bursts == 1:
            payload_data = payload_data[:self.MAX_PAYLOAD_SIZE]

        if is_last:#
            end = self.MAX_PAYLOAD_SIZE - ((total_bursts * self.MAX_PAYLOAD_SIZE) - payload_size)
            print(end)
            payload_data = payload_data[:end]

        #payload_data = payload_data[:payload_size]

        self.origin = frame["origin"]
        self.domain = frame["domain"]
        self.gridsquare = frame["gridsquare"]
        self.checksum = frame["checksum"]
        self.timestamp = frame["timestamp"]
        print("####################################")
        print("payload_size:", payload_size)
        print("payload_data:", payload_data)
        print("origin", self.origin)
        print("domain", self.domain)
        print("gridsquare", self.gridsquare)
        print("is_last", is_last)
        print("msg_type", msg_type)
        print("priority", priority)
        print("burst_number", burst_number)
        print("total_bursts", total_bursts)
        print("checksum", self.checksum)
        print("timestamp", self.timestamp)


        payload_b64 = base64.b64encode(payload_data).decode("ascii")
        print("payload_b64", payload_b64)

        self.id = self.create_broadcast_id(self.timestamp, self.domain, self.checksum)
        print("id", self.id)
        print("len-id", len(self.id))

        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        expires_at = expires_at.timestamp()

        db = DatabaseManagerBroadcasts(self.ctx)
        success = db.process_broadcast_message(
            id=self.id,
            origin=self.origin,
            timestamp=self.timestamp,
            burst_index=burst_number,
            burst_data=payload_b64,
            total_bursts=total_bursts,
            checksum=self.checksum,
            repairing_callsigns=frame.get("repairing_callsigns"),
            domain=self.domain,
            gridsquare=self.gridsquare,
            msg_type=msg_type.name,
            priority=priority,
            received_at=datetime.now(timezone.utc).timestamp(),
            expires_at=expires_at,
            nexttransmission_at=datetime.now(timezone.utc).timestamp(),
            is_read=False,
            direction="receive",
            status="assembling"
        )

        if not success:
            print("Failed to process burst in database.")

