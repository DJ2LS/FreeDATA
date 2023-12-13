from modem_frametypes import FRAME_TYPE as FR_TYPE
import helpers
import codec2

class DataFrameFactory:

    LENGTH_SIG0_FRAME = 14
    LENGTH_SIG1_FRAME = 14

    def __init__(self, config):
        self.myfullcall = f"{config['STATION']['mycall']}-{config['STATION']['myssid']}"
        self.mygrid = config['STATION']['mygrid']

        # table for holding our frame templates
        self.template_list = {}

        self._load_broadcast_templates()
        self._load_ping_templates()
        self._load_fec_templates()
        self._load_arq_templates()

    def _load_broadcast_templates(self):
        # cq frame
        self.template_list[FR_TYPE.CQ.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "origin": 6,
            "gridsquare": 4
        }

        # qrv frame
        self.template_list[FR_TYPE.QRV.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "origin": 6,
            "gridsquare": 4,
            "snr": 1
        }

        # beacon frame
        self.template_list[FR_TYPE.BEACON.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "origin": 6,
            "gridsquare": 4
        }

    def _load_ping_templates(self):
        # ping frame
        self.template_list[FR_TYPE.PING.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "destination_crc": 3,
            "origin_crc": 3,
            "origin": 6
        }

        # ping ack
        self.template_list[FR_TYPE.PING_ACK.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "destination_crc": 3,
            "origin_crc": 3,
            "gridsquare": 4,
            "snr": 1,
        }

    def _load_fec_templates(self):
        # fec wakeup frame
        self.template_list[FR_TYPE.FEC_WAKEUP.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "origin": 6,
            "mode": 1,
            "n_bursts": 1,
        }

        # fec frame
        self.template_list[FR_TYPE.FEC.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "data": self.LENGTH_SIG0_FRAME - 1
        }

        # fec is writing frame
        self.template_list[FR_TYPE.IS_WRITING.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "origin": 6
        }

    def _load_arq_templates(self):

        self.template_list[FR_TYPE.ARQ_SESSION_OPEN.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "destination_crc": 3,
            "origin": 6,
            "session_id": 1,
        }

        self.template_list[FR_TYPE.ARQ_SESSION_OPEN_ACK.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "session_id": 1,
            "origin": 6,
            "destination_crc": 3,
            "version": 1,
            "snr": 1,
        }

        self.template_list[FR_TYPE.ARQ_SESSION_INFO.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "session_id": 1,
            "total_length": 4,
            "total_crc": 4,
            "snr": 1,
        }

        self.template_list[FR_TYPE.ARQ_SESSION_INFO_ACK.value] = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "session_id": 1,
            "total_crc": 4,
            "snr": 1,
            "speed_level": 1,
            "frames_per_burst": 1,
        }

        # arq burst frame
        self.template_list[FR_TYPE.BURST_FRAME.value] = {
            "frame_length": None,
            "session_id": 1,
            "offset": 4,
            "data": "dynamic",
        }

        # arq burst ack
        self.template_list[FR_TYPE.BURST_ACK.value] = {
            "frame_length": self.LENGTH_SIG1_FRAME,
            "session_id": 1,
            "offset":4,
            "speed_level": 1,
            "frames_per_burst": 1,
            "snr": 1,
        }

        # arq burst nack
        self.template_list[FR_TYPE.BURST_NACK.value] = {
            "frame_length": self.LENGTH_SIG1_FRAME,
            "session_id": 1,
            "offset":4,
            "speed_level": 1,
            "frames_per_burst": 1,
            "snr": 1,
        }

    def construct(self, frametype, content, frame_length = LENGTH_SIG1_FRAME):

        frame_template = self.template_list[frametype.value]

        if isinstance(frame_template["frame_length"], int):
            length = frame_template["frame_length"]
        else:
            length = frame_length

        frame = bytearray(frame_length)
        frame[:1] = bytes([frametype.value])

        buffer_position = 1
        for key, item_length in frame_template.items():
            if key == "frame_length":
                continue

            if not isinstance(item_length, int):
                item_length = len(content[key])

            if buffer_position + item_length > frame_length:
                raise OverflowError("Frame data overflow!")
            
            frame[buffer_position: buffer_position + item_length] = content[key]
            buffer_position += item_length

        return frame

    def deconstruct(self, frame):
        buffer_position = 1
        # Extract frametype and get the corresponding template
        frametype = int.from_bytes(frame[:1], "big")
        frame_template = self.template_list.get(frametype)

        if not frame_template:
            # Handle the case where the frame type is not recognized
            raise ValueError(f"Unknown frame type: {frametype}")

        extracted_data = {"frame_type": FR_TYPE(frametype).name, "frame_type_int": frametype}

        for key, item_length in frame_template.items():
            if key == "frame_length":
                continue

            # data is always on the last payload slots
            if item_length in ["dynamic"] and key in["data"]:
                data = frame[buffer_position:]
                item_length = len(data)
            else:
                data = frame[buffer_position: buffer_position + item_length]

            # Process the data based on the key
            if key in ["origin", "destination"]:
                extracted_data[key] = helpers.bytes_to_callsign(data).decode()

            elif key in ["origin_crc", "destination_crc"]:
                extracted_data[key] = data.hex()

            elif key == "gridsquare":
                extracted_data[key] = helpers.decode_grid(data)

            elif key in ["session_id", "speed_level", 
                            "frames_per_burst", "version",
                            "snr", "offset"]:
                extracted_data[key] = int.from_bytes(data, 'big')

            else:
                extracted_data[key] = data

            buffer_position += item_length

        return extracted_data


    def get_bytes_per_frame(self, mode: codec2.FREEDV_MODE) -> int:
        freedv = codec2.open_instance(mode.value)
        bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv) / 8)
        return bytes_per_frame

    def build_ping(self, destination):
        payload = {
            "destination_crc": helpers.get_crc_24(destination),
            "origin_crc": helpers.get_crc_24(self.myfullcall),
            "origin": helpers.callsign_to_bytes(self.myfullcall),
        }
        return self.construct(FR_TYPE.PING, payload)

    def build_ping_ack(self, destination, snr):
        payload = {
            "destination_crc": helpers.get_crc_24(destination),
            "origin_crc": helpers.get_crc_24(self.myfullcall),
            "gridsquare": helpers.encode_grid(self.mygrid),
            "snr": helpers.snr_to_bytes(snr)
        }
        return self.construct(FR_TYPE.PING_ACK, payload)

    def build_cq(self):
        payload = {
            "origin": helpers.callsign_to_bytes(self.myfullcall),
            "gridsquare": helpers.encode_grid(self.mygrid)
        }
        return self.construct(FR_TYPE.CQ, payload)

    def build_qrv(self, snr):
        payload = {
            "origin": helpers.callsign_to_bytes(self.myfullcall),
            "gridsquare": helpers.encode_grid(self.mygrid),
            "snr": helpers.snr_to_bytes(snr)
        }
        return self.construct(FR_TYPE.QRV, payload)

    def build_beacon(self):
        payload = {
            "origin": helpers.callsign_to_bytes(self.myfullcall),
            "gridsquare": helpers.encode_grid(self.mygrid)
        }
        return self.construct(FR_TYPE.BEACON, payload)

    def build_fec_is_writing(self):
        payload = {
            "origin": helpers.callsign_to_bytes(self.myfullcall),
        }
        return self.construct(FR_TYPE.IS_WRITING, payload)

    def build_fec_wakeup(self, mode):
        mode_int = codec2.freedv_get_mode_value_by_name(mode)

        payload = {
            "origin": helpers.callsign_to_bytes(self.myfullcall),
            "mode": bytes([mode_int]),
            "n_bursts": bytes([1]) # n payload bursts,

        }
        return self.construct(FR_TYPE.FEC_WAKEUP, payload)

    def build_fec(self, mode, payload):
        mode_int = codec2.freedv_get_mode_value_by_name(mode)
        payload_per_frame = codec2.get_bytes_per_frame(mode_int) - 2
        fec_payload_length = payload_per_frame - 1
        fec_frame = bytearray(payload_per_frame)
        fec_frame[:1] = bytes([FR_TYPE.FEC.value])
        fec_frame[1:payload_per_frame] = bytes(payload[:fec_payload_length])
        return fec_frame

    def build_test(self):
        test_frame = bytearray(126)
        test_frame[:1] = bytes([FR_TYPE.TEST_FRAME.value])
        return test_frame

    def build_arq_session_open(self, destination, session_id):
        payload = {
            "destination_crc": helpers.get_crc_24(destination),
            "origin": helpers.callsign_to_bytes(self.myfullcall),
            "session_id": session_id.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.ARQ_SESSION_OPEN, payload)

    def build_arq_session_open_ack(self, session_id, destination, version, snr):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
            "origin": helpers.callsign_to_bytes(self.myfullcall),
            "destination_crc": helpers.get_crc_24(destination),
            "version": bytes([version]),
            "snr": snr.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.ARQ_SESSION_OPEN_ACK, payload)
    
    def build_arq_session_info(self, session_id: int, total_length: int, total_crc: bytes, snr):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
            "total_length": total_length.to_bytes(4, 'big'),
            "total_crc": total_crc,
            "snr": snr.to_bytes(1, 'big'),
        }
        return self.construct(FR_TYPE.ARQ_SESSION_INFO, payload)

    def build_arq_session_info_ack(self, session_id, total_crc, snr, speed_level, frames_per_burst):
        payload = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "session_id": session_id.to_bytes(1, 'big'),
            "total_crc": total_crc,
            "snr": snr.to_bytes(1, 'big'),
            "speed_level": speed_level.to_bytes(1, 'big'),
            "frames_per_burst": frames_per_burst.to_bytes(1, 'big'),
        }        
        return self.construct(FR_TYPE.ARQ_SESSION_INFO_ACK, payload)

    def build_arq_burst_frame(self, freedv_mode: codec2.FREEDV_MODE, session_id: int, offset: int, data: bytes):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
            "offset": offset.to_bytes(4, 'big'),
            "data": data,
        }
        return self.construct(FR_TYPE.BURST_FRAME, payload, self.get_bytes_per_frame(freedv_mode))

    def build_arq_burst_ack(self, session_id: bytes, offset, speed_level: int, 
                            frames_per_burst: int, snr: int):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
            "offset": offset.to_bytes(4, 'big'),
            "speed_level": speed_level.to_bytes(1, 'big'),
            "frames_per_burst": frames_per_burst.to_bytes(1, 'big'),
            "snr": helpers.snr_to_bytes(snr),
        }
        return self.construct(FR_TYPE.BURST_ACK, payload)

    def build_arq_burst_nack(self, session_id: bytes, offset, speed_level: int, 
                            frames_per_burst: int, snr: int):
        payload = {
            "session_id": session_id.to_bytes(1, 'big'),
            "offset": offset.to_bytes(4, 'big'),
            "speed_level": speed_level.to_bytes(1, 'big'),
            "frames_per_burst": frames_per_burst.to_bytes(1, 'big'),
            "snr": helpers.snr_to_bytes(snr),
        }
        return self.construct(FR_TYPE.BURST_NACK, payload)


