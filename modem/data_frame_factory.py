from modem_frametypes import FRAME_TYPE as FR_TYPE
import helpers
import codec2

class DataFrameFactory:

    def __init__(self):
        self.myfullcall = f"{self.modem_config['STATION']['mycall']}-{self.modem_config['STATION']['myssid']}"

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
        ping_frame = bytearray(self.length_sig0_frame)
        ping_frame[:1] = bytes(self.type.value)
        ping_frame[1:4] = helpers.get_crc_24(dxcallsign)
        ping_frame[4:7] = helpers.get_crc_24(self.myfullcall)
        ping_frame[7:13] = helpers.callsign_to_bytes(self.myfullcall)
        return ping_frame
    
    def build_cq(self):
        cq_frame = bytearray(self.length_sig0_frame)
        cq_frame[:1] = bytes([FR_TYPE.CQ.value])
        cq_frame[1:7] = helpers.callsign_to_bytes(self.myfullcall)
        cq_frame[7:11] = helpers.encode_grid(self.mygrid)
        return cq_frame

    def build_fec_is_writing(self):
        fec_frame = bytearray(14)
        fec_frame[:1] = bytes([FR_TYPE.IS_WRITING.value])
        fec_frame[1:7] = helpers.callsign_to_bytes(self.myfullcall)
        return fec_frame

    def build_qrv(self, snr):
        qrv_frame = bytearray(self.length_sig0_frame)
        qrv_frame[:1] = bytes([FR_TYPE.QRV.value])
        qrv_frame[1:7] = helpers.callsign_to_bytes(self.myfullcall)
        qrv_frame[7:11] = helpers.encode_grid(self.mygrid)
        qrv_frame[11:12] = helpers.snr_to_bytes(snr)
        return qrv_frame

    def build_beacon(self):
        beacon_frame = bytearray(self.length_sig0_frame)
        beacon_frame[:1] = bytes([FR_TYPE.BEACON.value])
        beacon_frame[1:7] = helpers.callsign_to_bytes(self.myfullcall)
        beacon_frame[7:11] = helpers.encode_grid(self.mygrid)
        return beacon_frame
    
    def build_fec_wakeup(self, mode):
        mode_int = codec2.freedv_get_mode_value_by_name(mode)
        mode_int_wakeup = codec2.freedv_get_mode_value_by_name("sig0")
        payload_per_wakeup_frame = codec2.get_bytes_per_frame(mode_int_wakeup) - 2
        fec_wakeup_frame = bytearray(payload_per_wakeup_frame)
        fec_wakeup_frame[:1] = bytes([FR_TYPE.FEC_WAKEUP.value])
        fec_wakeup_frame[1:7] = helpers.callsign_to_bytes(self.myfullcall)
        fec_wakeup_frame[7:8] = bytes([mode_int])
        fec_wakeup_frame[8:9] = bytes([1]) # n payload bursts
        return fec_wakeup_frame

    def build_fec(self, mode, payload):
        mode_int = codec2.freedv_get_mode_value_by_name(mode)
        payload_per_frame = codec2.get_bytes_per_frame(mode_int) - 2
        fec_payload_length = payload_per_frame - 1
        fec_frame = bytearray(payload_per_frame)
        fec_frame[:1] = bytes([FR_TYPE.FEC.value])
        fec_frame[1:payload_per_frame] = bytes(payload[:fec_payload_length])
        return fec_frame
