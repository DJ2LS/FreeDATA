# file for handling transmitting data
from norm.norm_transmission import NormTransmission
from norm.norm_transmission import NORMMsgType, NORMMsgPriority
from enum import Enum
import time
from codec2 import FREEDV_MODE
import helpers
from datetime import datetime, timezone, timedelta
import base64
from message_system_db_broadcasts import DatabaseManagerBroadcasts
import threading
import numpy as np

class NORM_ISS_State(Enum):
    NEW = 0
    TRANSMITTING = 1
    ENDED = 2
    FAILED = 3
    ABORTING = 4
    ABORTED = 5

class NormTransmissionISS(NormTransmission):
    MAX_PAYLOAD_SIZE = 26

    def __init__(self, ctx):
        super().__init__(ctx)
        self.ctx = ctx
        self.state = NORM_ISS_State.NEW
        self.log("Initialized")

    def prepare_and_transmit_data(self, origin, domain, gridsquare, data, priority=NORMMsgPriority.NORMAL, message_type=NORMMsgType.UNDEFINED):
        self.origin = origin
        self.domain = domain
        self.gridsquare = gridsquare
        self.data = data
        self.priority = priority
        self.message_type = message_type
        self.payload_size = len(data)
        self.timestamp = int(time.time())

        bursts = self.create_data()
        self.add_to_database()
        self.transmit_bursts(bursts)

    def create_data(self):
        full_data = self.data
        total_bursts = (len(full_data) + self.MAX_PAYLOAD_SIZE - 1) // self.MAX_PAYLOAD_SIZE

        bursts = []
        for burst_number in range(1, total_bursts + 1):
            offset = (burst_number - 1) * self.MAX_PAYLOAD_SIZE
            payload = full_data[offset: offset + self.MAX_PAYLOAD_SIZE]
            burst_info = self.encode_burst_info(burst_number, total_bursts)
            checksum = helpers.get_crc_24(full_data)
            is_last = (burst_number == total_bursts)
            flags = self.encode_flags(self.message_type, self.priority, is_last)

            burst_frame = self.frame_factory.build_norm_data(
                origin=self.origin,
                domain=self.domain,
                gridsquare=self.gridsquare,
                timestamp=self.timestamp,
                burst_info=burst_info,
                payload_size=len(full_data),
                payload_data=payload,
                flag=flags,
                checksum=checksum
            )
            bursts.append(burst_frame)
        return bursts

    def create_repair(self, db_msg_obj: dict, burst_numbers: list[int]):
        repair_bursts = []
        data = base64.b64decode(db_msg_obj["payload_data"]["final"])
        total_bursts = db_msg_obj["total_bursts"]
        priority = db_msg_obj["priority"]
        message_type = NORMMsgType[db_msg_obj["msg_type"]] if isinstance(db_msg_obj["msg_type"], str) else db_msg_obj["msg_type"]
        checksum = bytes.fromhex(db_msg_obj["checksum"])

        for burst_number in burst_numbers:
            offset = (burst_number - 1) * self.MAX_PAYLOAD_SIZE
            payload = data[offset: offset + self.MAX_PAYLOAD_SIZE]
            burst_info = self.encode_burst_info(burst_number, total_bursts)
            is_last = (burst_number == total_bursts)
            flags = self.encode_flags(message_type, priority, is_last)

            burst_frame = self.frame_factory.build_norm_repair(
                origin=db_msg_obj["origin"],
                domain=db_msg_obj["domain"],
                gridsquare=db_msg_obj["gridsquare"],
                timestamp=int(datetime.fromisoformat(db_msg_obj["timestamp"]).timestamp()),
                burst_info=burst_info,
                payload_size=len(data),
                payload_data=payload,
                flag=flags,
                checksum=checksum
            )
            repair_bursts.append(burst_frame)

        return repair_bursts

    def transmit_bursts(self, bursts):
        random_delay = np.random.randint(0, 6)
        threading.Event().wait(random_delay)
        self.ctx.state_manager.channel_busy_condition_codec2.wait(0.5)

        for burst in bursts:
            self.ctx.rf_modem.transmit(FREEDV_MODE.datac4, 1, 200, burst)

    def add_to_database(self):
        db = DatabaseManagerBroadcasts(self.ctx)
        timestamp_dt = datetime.fromtimestamp(self.timestamp, tz=timezone.utc)
        checksum = helpers.get_crc_24(self.data).hex()
        broadcast_id = self.create_broadcast_id(timestamp_dt, self.domain, checksum)

        total_bursts = (len(self.data) + self.MAX_PAYLOAD_SIZE - 1) // self.MAX_PAYLOAD_SIZE

        for burst_index in range(1, total_bursts + 1):
            offset = (burst_index - 1) * self.MAX_PAYLOAD_SIZE
            payload_data = self.data[offset: offset + self.MAX_PAYLOAD_SIZE]
            payload_b64 = base64.b64encode(payload_data).decode("ascii")

            db.process_broadcast_message(
                id=broadcast_id,
                origin=self.origin,
                timestamp=timestamp_dt,
                burst_index=burst_index,
                burst_data=payload_b64,
                total_bursts=total_bursts,
                checksum=checksum,
                repairing_callsigns=None,
                domain=self.domain,
                gridsquare=self.gridsquare,
                msg_type=self.message_type.name if hasattr(self.message_type, 'name') else str(self.message_type),
                priority=self.priority.value if hasattr(self.priority, 'value') else int(self.priority),
                received_at=datetime.now(timezone.utc),
                nexttransmission_at=datetime.now(timezone.utc) + timedelta(hours=1),
                expires_at=datetime.now(timezone.utc),
                is_read=True,
                direction="transmit",
                status="assembling"
            )
