from modem_frametypes import FRAME_TYPE as FR_TYPE
import helpers
import codec2

"""
How to use this class:

builder = DataFrameFactory()
payload = {
    "mycallsign" : helpers.callsign_to_bytes("DJ2LS-9"),
    "gridsquare": helpers.encode_grid("JN49ea"),
    "data": bytes(4)
}

frame = builder.construct(FR_TYPE.CQ, payload)
decoded_frame = builder.deconstruct(frame)
decoded_frame: {'frame_type': 'CQ', 'mycallsign': b'DJ2LS-9', 'gridsquare': 'JN49EA', 'data': bytearray(b'\x00\x00\x00\x00')}

"""


class DataFrameFactory:

    def __init__(self):
        self.myfullcall = f"{self.modem_config['STATION']['mycall']}-{self.modem_config['STATION']['myssid']}"
        self._load_broadcast_templates()
        self._load_ping_templates()
        self._load_fec_templates()

    def _load_broadcast_templates(self):
        # cq frame
        self.template_list[FR_TYPE.CQ.value] = {
            "frame_length": self.length_sig0_frame,
            "mycallsign": 6,
            "gridsquare": 4
        }

        # qrv frame
        self.template_list[FR_TYPE.QRV.value] = {
            "frame_length": self.length_sig0_frame,
            "mycallsign": 6,
            "gridsquare": 4,
            "snr": 1
        }

        # beacon frame
        self.template_list[FR_TYPE.BEACON.value] = {
            "frame_length": self.length_sig0_frame,
            "mycallsign": 6,
            "gridsquare": 4
        }

    def _load_ping_templates(self):
        # ping frame
        self.template_list[FR_TYPE.PING.value] = {
            "frame_length": self.length_sig0_frame,
            "dxcallsign_crc": 3,
            "mycallsign_crc": 3,
            "mycallsign": 6
        }

    def _load_fec_templates(self):
        # fec wakeup frame
        self.template_list[FR_TYPE.FEC_WAKEUP.value] = {
            "frame_length": self.length_sig0_frame,
            "mycallsign": 6,
            "mode": 1,
            "n_bursts": 1,
        }

        # fec frame
        self.template_list[FR_TYPE.FEC.value] = {
            "frame_length": self.length_sig0_frame,
            "data": self.length_sig0_frame - 1
        }

        # fec is writing frame
        self.template_list[FR_TYPE.IS_WRITING.value] = {
            "frame_length": self.length_sig0_frame,
            "mycallsign": 6
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
        extracted_data = {}
        buffer_position = 1

        # Extract frametype and get the corresponding template
        frametype = int.from_bytes(frame[:1], "big")
        frame_template = self.template_list.get(frametype)

        if not frame_template:
            # Handle the case where the frame type is not recognized
            raise ValueError(f"Unknown frame type: {frametype}")

        extracted_data["frame_type"] = FR_TYPE(frametype).name

        for key, item_length in frame_template.items():
            if key != "frame_length":
                data = frame[buffer_position: buffer_position + item_length]

                # Process the data based on the key
                if key == "mycallsign":
                    # we are overriding the tempaltes mycallsign, because it will become
                    # the dxcallsign when receiving
                    extracted_data["dxcallsign"] = helpers.bytes_to_callsign(data)
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

    def build_ping(self, dxcallsign):
        payload = {
            "dxcallsign_crc": helpers.get_crc_24(dxcallsign),
            "mycallsign_crc": helpers.get_crc_24(self.myfullcall),
            "mycallsign": helpers.callsign_to_bytes(self.myfullcall),
        }
        return self.construct(FR_TYPE.PING, payload)
    
    def build_cq(self):
        payload = {
            "mycallsign": helpers.callsign_to_bytes(self.myfullcall),
            "gridsquare": helpers.encode_grid(self.mygrid)
        }
        return self.construct(FR_TYPE.CQ, payload)

    def build_qrv(self, snr):
        payload = {
            "mycallsign": helpers.callsign_to_bytes(self.myfullcall),
            "gridsquare": helpers.encode_grid(self.mygrid),
            "snr": helpers.snr_to_bytes(snr)
        }
        return self.construct(FR_TYPE.QRV, payload)



    def build_beacon(self):
        payload = {
            "mycallsign": helpers.callsign_to_bytes(self.myfullcall),
            "gridsquare": helpers.encode_grid(self.mygrid)
        }
        return self.construct(FR_TYPE.BEACON, payload)

    def build_fec_is_writing(self):
        payload = {
            "mycallsign": helpers.callsign_to_bytes(self.myfullcall),
        }
        return self.construct(FR_TYPE.IS_WRITING, payload)

    def build_fec_wakeup(self, mode):
        mode_int = codec2.freedv_get_mode_value_by_name(mode)

        payload = {
            "mycallsign": helpers.FEC_WAKEUP(self.myfullcall),
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
