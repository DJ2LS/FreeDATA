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

        if not self.ctx.config_manager.config["EXP"]["enable_groupchat"]:
            return

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
        try:
            if not self.data:
                self.log("Data is empty", isWarning=True)
                raise ValueError("Data is empty")

            full_data = self.data
            total_bursts = (len(full_data) + self.MAX_PAYLOAD_SIZE - 1) // self.MAX_PAYLOAD_SIZE

            if total_bursts <= 0:
                self.log(
                    f"Invalid burst calculation (data length: {len(full_data)}, max payload: {self.MAX_PAYLOAD_SIZE})",
                    isWarning=True)
                raise ValueError("Invalid burst calculation")

            bursts = []
            for burst_number in range(1, total_bursts + 1):
                offset = (burst_number - 1) * self.MAX_PAYLOAD_SIZE
                payload = full_data[offset: offset + self.MAX_PAYLOAD_SIZE]

                if not payload:
                    self.log(f"Empty payload at burst {burst_number}", isWarning=True)
                    raise ValueError(f"Empty payload at burst {burst_number}")

                burst_info = self.encode_burst_info(burst_number, total_bursts)
                checksum = helpers.get_crc_24(full_data)
                is_last = (burst_number == total_bursts)
                print("so...")
                print("message type", self.message_type)
                print("priority", self.priority)
                print("is_last", is_last)
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

                self.log(
                    f"Burst {burst_number}/{total_bursts} created (offset={offset}, payload_size={len(payload)}, is_last={is_last})")

                bursts.append(burst_frame)

            self.log(f"All bursts created successfully (total={total_bursts})")
            return bursts

        except Exception as e:
            self.log(f"Error in create_data: {e}", isWarning=True)
            raise

    def create_repair(self, db_msg_obj: dict, burst_numbers: list[int]):
        try:
            if "payload_data" not in db_msg_obj or "final" not in db_msg_obj["payload_data"]:
                self.log("Missing payload data in db_msg_obj", isWarning=True)
                raise ValueError("Missing payload data")

            data = base64.b64decode(db_msg_obj["payload_data"]["final"])
            total_bursts = db_msg_obj.get("total_bursts")
            priority = db_msg_obj.get("priority")
            msg_type_val = db_msg_obj.get("msg_type")
            message_type = NORMMsgType[msg_type_val] if isinstance(msg_type_val, str) else msg_type_val
            checksum_hex = db_msg_obj.get("checksum")

            if not all([total_bursts, priority, message_type, checksum_hex]):
                self.log("Missing required fields in db_msg_obj", isWarning=True)
                raise ValueError("Missing required fields")

            checksum = bytes.fromhex(checksum_hex)
            repair_bursts = []

            for burst_number in burst_numbers:
                if burst_number < 1 or burst_number > total_bursts:
                    self.log(f"Invalid burst number {burst_number}", isWarning=True)
                    raise ValueError(f"Invalid burst number {burst_number}")

                offset = (burst_number - 1) * self.MAX_PAYLOAD_SIZE
                payload = data[offset: offset + self.MAX_PAYLOAD_SIZE]

                if not payload:
                    self.log(f"Empty payload for burst {burst_number}", isWarning=True)
                    raise ValueError(f"Empty payload for burst {burst_number}")

                burst_info = self.encode_burst_info(burst_number, total_bursts)
                is_last = (burst_number == total_bursts)
                flags = self.encode_flags(message_type, priority, is_last)

                burst_frame = self.frame_factory.build_norm_repair(
                    origin=db_msg_obj["origin"],
                    domain=db_msg_obj["domain"],
                    gridsquare=db_msg_obj["gridsquare"],
                    timestamp=int(db_msg_obj["timestamp"]),
                    burst_info=burst_info,
                    payload_size=len(data),
                    payload_data=payload,
                    flag=flags,
                    checksum=checksum
                )

                self.log(
                    f"Repair burst {burst_number}/{total_bursts} created (offset={offset}, payload_size={len(payload)}, is_last={is_last})")
                repair_bursts.append(burst_frame)

            self.log(f"All repair bursts created successfully (count={len(repair_bursts)})")
            return repair_bursts

        except Exception as e:
            self.log(f"Error in create_repair: {e}", isWarning=True)
            raise

    def transmit_bursts(self, bursts):
        try:
            if not bursts:
                self.log("No bursts to transmit", isWarning=True)
                return

            random_delay = np.random.randint(0, 6)
            self.log(f"Random delay before transmit: {random_delay}s")
            threading.Event().wait(random_delay)

            self.log("Waiting for channel busy condition")
            self.ctx.state_manager.channel_busy_condition_codec2.wait(0.5)

            for i, burst in enumerate(bursts, 1):
                self.ctx.rf_modem.transmit(FREEDV_MODE.datac4, 1, 200, burst)
                self.log(f"Transmitted burst {i}/{len(bursts)} (size={len(burst)})")

            self.log("All bursts transmitted successfully")

        except Exception as e:
            self.log(f"Error in transmit_bursts: {e}", isWarning=True)
            raise

    def add_to_database(self):
        try:
            db = DatabaseManagerBroadcasts(self.ctx)
            checksum = helpers.get_crc_24(self.data).hex()
            broadcast_id = self.create_broadcast_id(int(self.timestamp), self.domain, checksum)

            total_bursts = (len(self.data) + self.MAX_PAYLOAD_SIZE - 1) // self.MAX_PAYLOAD_SIZE

            if total_bursts < 1:
                self.log("No bursts to store in database", isWarning=True)
                return

            for burst_index in range(1, total_bursts + 1):
                offset = (burst_index - 1) * self.MAX_PAYLOAD_SIZE
                payload_data = self.data[offset: offset + self.MAX_PAYLOAD_SIZE]
                if not payload_data:
                    self.log(f"Empty payload at burst index {burst_index}", isWarning=True)
                    continue

                payload_b64 = base64.b64encode(payload_data).decode("ascii")
                nexttransmission_at = datetime.now(timezone.utc) + timedelta(hours=1)
                nexttransmission_at = nexttransmission_at.timestamp()

                expires_at = datetime.now(timezone.utc) + timedelta(days=1)
                expires_at = expires_at.timestamp()


                db.process_broadcast_message(
                    id=broadcast_id,
                    origin=self.origin,
                    timestamp=self.timestamp,
                    burst_index=burst_index,
                    burst_data=payload_b64,
                    total_bursts=total_bursts,
                    checksum=checksum,
                    repairing_callsigns=None,
                    domain=self.domain,
                    gridsquare=self.gridsquare,
                    msg_type=self.message_type.name if hasattr(self.message_type, "name") else str(self.message_type),
                    priority=self.priority.value if hasattr(self.priority, "value") else int(self.priority),
                    received_at=datetime.now(timezone.utc).timestamp(),
                    nexttransmission_at=nexttransmission_at,
                    expires_at=expires_at,
                    is_read=True,
                    direction="transmit",
                    status="assembling"
                )

                self.log(f"Stored burst {burst_index}/{total_bursts} in database (size={len(payload_data)})")

            self.log(f"All {total_bursts} bursts added to database successfully")

        except Exception as e:
            self.log(f"Error in add_to_database: {e}", isWarning=True)
            raise

    def retransmit_data(self, msg):
        self.origin = msg.origin
        self.domain = msg.domain
        self.gridsquare = msg.gridsquare
        self.data = base64.b64decode(msg.payload_data["final"])
        self.priority = msg.priority
        self.message_type = msg.msg_type
        self.payload_size = len(self.data)
        self.timestamp = int(msg.timestamp)

        bursts = self.create_data()
        #self.add_to_database()
        self.transmit_bursts(bursts)

