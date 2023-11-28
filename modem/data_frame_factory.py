from modem_frametypes import FRAME_TYPE as FR_TYPE
import helpers
import codec2

"""
How to use this class:

builder = DataFrameFactory()
payload = {
    "origin" : helpers.callsign_to_bytes("DJ2LS-9"),
    "gridsquare": helpers.encode_grid("JN49ea"),
    "data": bytes(4)
}

frame = builder.construct(FR_TYPE.CQ, payload)
decoded_frame = builder.deconstruct(frame)
decoded_frame: {'frame_type': 'CQ', 'origin': b'DJ2LS-9', 'gridsquare': 'JN49EA', 'data': bytearray(b'\x00\x00\x00\x00')}

"""


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

        # same structure for narrow and wide types
        arq_dc_open_ack = {
            "frame_length": self.LENGTH_SIG0_FRAME,
            "destination_crc": 3,
            "origin_crc": 3,
            "origin": 6,
            "session_id": 1,
        }
        # arq connect frames
        self.template_list[FR_TYPE.ARQ_DC_OPEN_ACK_N.value] = arq_dc_open_ack
        self.template_list[FR_TYPE.ARQ_DC_OPEN_ACK_W.value] = arq_dc_open_ack

        # arq burst ack 
        self.template_list[FR_TYPE.BURST_ACK.value] = {
            "frame_length": self.LENGTH_SIG1_FRAME,
            "session_id": 1,
            "snr":1,
            "speed_level": 1,
            "len_arq_rx_frame_buffer": 4
        }

        # arq frame ack TODO We should rename this to "session ack"
        self.template_list[FR_TYPE.FR_ACK.value] = {
            "frame_length": self.LENGTH_SIG1_FRAME,
            "session_id": 1,
            "snr":1
        }
        
        # arq burst nack
        self.template_list[FR_TYPE.BURST_NACK.value] = {
            "frame_length": self.LENGTH_SIG1_FRAME,
            "session_id": 1,
            "snr": 1,
            "speed_level": 1,
            "len_arq_rx_frame_buffer": 4,
            "n_frames_per_burst": 1

        }

        # arq frame nack --> TODO We should rename this to "session nack"
        self.template_list[FR_TYPE.FR_NACK.value] = {
            "frame_length": self.LENGTH_SIG1_FRAME,
            "session_id": 1,
            "snr": 1,
            "speed_level": 1,
            "len_arq_rx_frame_buffer": 4,
            "n_frames_per_burst": 1

        }

    def construct(self, frametype, content):
        frame_template = self.template_list[frametype.value]
        frame_length = frame_template["frame_length"]
        frame = bytearray(frame_length)

        buffer_position = 1
        for key, item_length in frame_template.items():
            if key != "frame_length":
                frame[buffer_position: buffer_position + item_length] = content[key]
                buffer_position += item_length

        frame[:1] = bytes([frametype.value])
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
            if key != "frame_length":
                data = frame[buffer_position: buffer_position + item_length]

                # Process the data based on the key
                if key in ["origin", "destination"]:
                    extracted_data[key] = helpers.bytes_to_callsign(data).decode()

                elif key == "gridsquare":
                    extracted_data[key] = helpers.decode_grid(data)
                else:
                    extracted_data[key] = data

                buffer_position += item_length

        return extracted_data


    def get_bytes_per_frame(mode: int) -> int:
        """
        Provide bytes per frame information for accessing from data handler

        :param mode: Codec2 mode to query
        :type mode: int or str
        :return: Bytes per frame of the supplied codec2 data mode
        :rtype: int
        """
        freedv = codec2.open_instance(mode)
        # TODO add close session
        # get number of bytes per frame for mode
        return int(codec2.api.freedv_get_bits_per_modem_frame(freedv) / 8)

    def build_ping(self, destination):
        payload = {
            "destination_crc": helpers.get_crc_24(destination),
            "origin_crc": helpers.get_crc_24(self.myfullcall),
            "origin": helpers.callsign_to_bytes(self.myfullcall),
        }
        return self.construct(FR_TYPE.PING, payload)
    
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

    def build_arq_connect(self, isWideband, destination, session_id):
        
        payload = {
            "destination_crc": helpers.get_crc_24(destination),
            "origin_crc": helpers.get_crc_24(self.myfullcall),
            "origin": helpers.callsign_to_bytes(self.myfullcall),
            "session_id": session_id.to_bytes(1, 'big'),
        }

        channel_type = FR_TYPE.ARQ_DC_OPEN_ACK_W if isWideband else FR_TYPE.ARQ_DC_OPEN_ACK_N
        return self.construct(channel_type, payload)

    def build_arq_burst_ack(self, session_id: bytes, snr: int, speed_level: int, len_arq_rx_frame_buffer: int):
        # ack_frame = bytearray(self.length_sig1_frame)
        # ack_frame[:1] = bytes([FR_TYPE.BURST_ACK.value])
        # ack_frame[1:2] = self.session_id
        # ack_frame[2:3] = helpers.snr_to_bytes(snr)
        # ack_frame[3:4] = bytes([int(self.speed_level)])
        # ack_frame[4:8] = len(self.arq_rx_frame_buffer).to_bytes(4, byteorder="big")
        
        payload = {
            "session_id": session_id,
            "snr": helpers.snr_to_bytes(snr),
            "speed_level": bytes([speed_level]),
            "len_arq_rx_frame_buffer": bytes([len_arq_rx_frame_buffer])
        }
        return self.construct(FR_TYPE.BURST_ACK, payload)

    def build_arq_frame_ack(self, session_id: bytes, snr: int):
        # ack_frame = bytearray(self.length_sig1_frame)
        # ack_frame[:1] = bytes([FR_TYPE.FR_ACK.value])
        # ack_frame[1:2] = self.session_id
        # ack_frame[2:3] = helpers.snr_to_bytes(snr)

        payload = {
            "session_id": session_id,
            "snr": helpers.snr_to_bytes(snr)
        }
        return self.construct(FR_TYPE.FR_ACK, payload)


    def build_arq_burst_nack(self, session_id: bytes, snr: int, speed_level: int, len_arq_rx_frame_buffer: int, n_frames_per_burst: int):
        # nack_frame = bytearray(self.length_sig1_frame)
        # nack_frame[:1] = bytes([FR_TYPE.BURST_NACK.value])
        # nack_frame[1:2] = self.session_id
        # nack_frame[2:3] = helpers.snr_to_bytes(0)
        # nack_frame[3:4] = bytes([int(self.speed_level)])
        # nack_frame[4:5] = bytes([int(tx_n_frames_per_burst)])
        # nack_frame[5:9] = len(self.arq_rx_frame_buffer).to_bytes(4, byteorder="big")
        payload = {
            "session_id": session_id,
            "snr": helpers.snr_to_bytes(snr),
            "speed_level": bytes([speed_level]),
            "len_arq_rx_frame_buffer": bytes([len_arq_rx_frame_buffer]),
            "n_frames_per_burst": bytes([n_frames_per_burst])
        }
        return self.construct(FR_TYPE.BURST_NACK, payload)
    
    def build_arq_frame_nack(self, session_id: bytes, snr: int, speed_level: int, len_arq_rx_frame_buffer: int, n_frames_per_burst: int):
        # nack_frame = bytearray(self.length_sig1_frame)
        # nack_frame[:1] = bytes([FR_TYPE.FR_NACK.value])
        # nack_frame[1:2] = self.session_id
        # nack_frame[2:3] = helpers.snr_to_bytes(snr)
        # nack_frame[3:4] = bytes([int(self.speed_level)])
        # nack_frame[4:8] = len(self.arq_rx_frame_buffer).to_bytes(4, byteorder="big")

        payload = {
            "session_id": session_id,
            "snr": helpers.snr_to_bytes(snr),
            "speed_level": bytes([speed_level]),
            "len_arq_rx_frame_buffer": bytes([len_arq_rx_frame_buffer]),
            "n_frames_per_burst": bytes([n_frames_per_burst])

        }
        return self.construct(FR_TYPE.FR_NACK, payload)
