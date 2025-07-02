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

    def __init__(self, ctx, origin, domain, gridsquare, data, priority=NORMMsgPriority.NORMAL, message_type=NORMMsgType.UNDEFINED, send_only_bursts=None):

        super().__init__(ctx, origin, domain)
        self.ctx = ctx
        self.origin = origin
        self.domain = domain
        self.gridsquare = gridsquare
        self.data = data
        self.priority = priority
        self.message_type = message_type
        self.payload_size = len(data)

        self.send_only_bursts = send_only_bursts

        self.timestamp = int(time.time())

        self.state = NORM_ISS_State.NEW

        self.log("Initialized")

    def prepare_and_transmit(self):
        bursts = self.create_bursts()
        print("add to database...")
        self.add_to_database()
        print("transmit bursts...")
        self.transmit_bursts(bursts)
        print("done...")
    def create_bursts(self):
        self.message_type = NORMMsgType.MESSAGE
        self.message_priority = NORMMsgPriority.NORMAL


        full_data = self.data
        print(self.data)
        total_bursts = (len(full_data) + self.MAX_PAYLOAD_SIZE - 1) // self.MAX_PAYLOAD_SIZE
        print("total_bursts: ", total_bursts)
        print("MAX_PAYLOAD_SIZE: ", self.MAX_PAYLOAD_SIZE)
        print("len full data: ", len(full_data))


        bursts = []
        if not self.send_only_bursts:

            for burst_number in range(1, total_bursts + 1):
                offset = (burst_number-1) * self.MAX_PAYLOAD_SIZE
                payload = full_data[offset: offset + self.MAX_PAYLOAD_SIZE]
                print("payload: ", len(payload))

                burst_info = self.encode_burst_info(burst_number, total_bursts)
                checksum = helpers.get_crc_24(full_data)
                # set flag for last burst
                is_last = (burst_number == total_bursts)
                flags = self.encode_flags(
                    msg_type=self.message_type,
                    priority=self.message_priority,
                    is_last=is_last
                )

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
                print(burst_frame)
                bursts.append(burst_frame)

        else:
            for burst_number in self.send_only_bursts:
                offset = (burst_number - 1) * self.MAX_PAYLOAD_SIZE
                payload = full_data[offset: offset + self.MAX_PAYLOAD_SIZE]
                print("payload: ", len(payload))

                burst_info = self.encode_burst_info(burst_number, total_bursts)
                checksum = helpers.get_crc_24(full_data)
                # set flag for last burst
                is_last = (burst_number == total_bursts)
                flags = self.encode_flags(
                    msg_type=self.message_type,
                    priority=self.message_priority,
                    is_last=is_last
                )
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
                print(burst_frame)

                bursts.append(burst_frame)
        return bursts

    def transmit_bursts(self, bursts):

        # wait some random time and wait if we have an ongoing codec2 transmission
        # on our channel. This should prevent some packet collision
        random_delay = np.random.randint(0, 6)
        threading.Event().wait(random_delay)
        self.ctx.state_manager.channel_busy_condition_codec2.wait(0.5)
        print("bursts: ", bursts)
        for burst in bursts:
            print("transmitting burst: ", burst)
            self.ctx.rf_modem.transmit(FREEDV_MODE.datac4, 1, 200, burst)
        #self.ctx.rf_modem.transmit(FREEDV_MODE.datac4, 1, 200, bursts)
    def add_to_database(self):
        db = DatabaseManagerBroadcasts(self.ctx)
        self.timestamp_dt = datetime.fromtimestamp(self.timestamp, tz=timezone.utc)
        self.checksum = helpers.get_crc_24(self.data).hex()
        self.id = self.create_broadcast_id(self.timestamp_dt, self.domain, self.checksum)
        print(self.create_broadcast_id(self.timestamp_dt, self.domain, self.checksum), self.create_broadcast_id(self.timestamp, self.domain, self.checksum))
        print(self.timestamp, self.timestamp_dt)

        total_bursts = (len(self.data) + self.MAX_PAYLOAD_SIZE - 1) // self.MAX_PAYLOAD_SIZE

        for burst_index in range(1, total_bursts + 1):
            offset = (burst_index - 1) * self.MAX_PAYLOAD_SIZE
            payload_data = self.data[offset: offset + self.MAX_PAYLOAD_SIZE]
            payload_b64 = base64.b64encode(payload_data).decode("ascii")

            db.process_broadcast_message(
                id=self.id,
                origin=self.origin,
                timestamp=self.timestamp_dt,
                burst_index=burst_index,
                burst_data=payload_b64,
                total_bursts=total_bursts,
                checksum=self.checksum,
                repairing_callsigns=None,
                domain=self.domain,
                gridsquare=self.gridsquare,
                msg_type=self.message_type.name if hasattr(self.message_type, 'name') else str(self.message_type),
                priority=self.priority.value if hasattr(self.priority, 'value') else int(self.priority),
                received_at=datetime.now(timezone.utc),
                nexttransmission_at = datetime.now(timezone.utc) + timedelta(hours=1),
                expires_at=datetime.now(timezone.utc),
                is_read=True,
                direction="transmit",
                status="assembling"
            )
