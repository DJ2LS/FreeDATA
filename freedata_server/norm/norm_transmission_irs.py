# file for handling received data
from norm.norm_transmission import NormTransmission

class NormTransmissionIRS(NormTransmission):
    MAX_PAYLOAD_SIZE = 96

    def __init__(self, frame):
        print("burst:", frame)

        is_last, msg_type, priority = self.decode_flags(frame["flag"])
        burst_number, total_bursts = self.decode_burst_info(frame["burst_info"])
        payload_size = frame["payload_size"]
        payload_data = frame["payload_data"]
        self.origin = frame["origin"]
        self.domain = frame["domain"]
        self.gridsquare = frame["gridsquare"]

        # FIXME
        #if payload_size > len(frame["payload_data"]) and total_bursts > 1:
        #    payload_data = frame["payload_data"]
        #else:
        #    payload_data = frame["payload_data"][:self.MAX_PAYLOAD_SIZE * burst_number]




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

        # TODO:
        # add data to database or update it