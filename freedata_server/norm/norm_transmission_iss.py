# file for handling transmitting data
from norm.norm_transmission import NormTransmission
from norm.norm_transmission import NORMMsgType, NORMMsgPriority
from enum import Enum
import time
from codec2 import FREEDV_MODE

class NORM_ISS_State(Enum):
    NEW = 0
    TRANSMITTING = 1
    ENDED = 2
    FAILED = 3
    ABORTING = 4
    ABORTED = 5

class NormTransmissionISS(NormTransmission):
    MAX_PAYLOAD_SIZE = 96

    def __init__(self, ctx, origin, domain, gridsquare, data, priority=NORMMsgPriority.NORMAL, message_type=NORMMsgType.UNDEFINED):

        super().__init__(ctx, origin, domain)
        self.ctx = ctx
        self.origin = origin
        self.domain = domain
        self.gridsquare = gridsquare
        self.data = data
        self.priority = priority
        self.message_type = message_type
        self.payload_size = len(data)

        self.timestamp = int(time.time())

        self.state = NORM_ISS_State.NEW

        self.log("Initialized")

    def prepare_and_transmit(self):
        bursts = self.create_bursts()
        self.transmit_bursts(bursts)

    def create_bursts(self):
        self.message_type = NORMMsgType.MESSAGE
        self.message_priority = NORMMsgPriority.NORMAL


        full_data = self.data

        total_bursts = (len(full_data) + self.MAX_PAYLOAD_SIZE - 1) // self.MAX_PAYLOAD_SIZE
        bursts = []

        for burst_number in range(1, total_bursts + 1):
            offset = (burst_number-1) * self.MAX_PAYLOAD_SIZE
            payload = full_data[offset: offset + self.MAX_PAYLOAD_SIZE]

            burst_info = self.encode_burst_info(burst_number, total_bursts)

            # set flag for last burst
            is_last = (burst_number == total_bursts - 1)
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
                payload_size=len(payload),
                payload_data=payload,
                flag=flags
            )
            print(burst_frame)
            bursts.append(burst_frame)

        return bursts

    def transmit_bursts(self, bursts):

        for burst in bursts:
            self.ctx.rf_modem.transmit(FREEDV_MODE.datac4, 1, 100, burst)