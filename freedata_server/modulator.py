import ctypes
import codec2
import structlog
from codec2 import FREEDV_MODE
from codec2 import FREEDV_ADVANCED_FSK


class Modulator:
    """Modulates data using Codec2 and handles transmission parameters.

    This class manages the modulation of data using the Codec2 library. It
    handles various FreeDV modes, adds preambles, postambles, and silence
    to the transmitted data, and creates bursts of modulated frames. It
    also initializes and manages Codec2 instances for different modes.
    """
    log = structlog.get_logger("RF")

    def __init__(self, config):
        """Initializes the Modulator with configuration parameters.

        Args:
            config (dict): Configuration dictionary containing modem settings.
        """
        self.config = config
        self.tx_delay = config['MODEM']['tx_delay']
        self.modem_sample_rate = codec2.api.FREEDV_FS_8000

        # Initialize codec2, rig control, and data threads
        self.init_codec2()

    def init_codec2(self):
        """Initializes Codec2 instances for different FreeDV modes.

        This method initializes multiple instances of the Codec2 library,
        each corresponding to a different FreeDV mode used for
        transmission. This allows for efficient switching between modes
        during operation.
        """
        # Open codec2 instances

        # INIT TX MODES - here we need all modes.
        self.freedv_datac0_tx = codec2.open_instance(codec2.FREEDV_MODE.datac0.value)
        self.freedv_datac1_tx = codec2.open_instance(codec2.FREEDV_MODE.datac1.value)
        self.freedv_datac3_tx = codec2.open_instance(codec2.FREEDV_MODE.datac3.value)
        self.freedv_datac4_tx = codec2.open_instance(codec2.FREEDV_MODE.datac4.value)
        self.freedv_datac13_tx = codec2.open_instance(codec2.FREEDV_MODE.datac13.value)
        self.freedv_datac14_tx = codec2.open_instance(codec2.FREEDV_MODE.datac14.value)
        self.data_ofdm_200_tx = codec2.open_instance(codec2.FREEDV_MODE.data_ofdm_200.value)
        self.data_ofdm_250_tx = codec2.open_instance(codec2.FREEDV_MODE.data_ofdm_250.value)
        self.data_ofdm_500_tx = codec2.open_instance(codec2.FREEDV_MODE.data_ofdm_500.value)
        self.data_ofdm_1700_tx = codec2.open_instance(codec2.FREEDV_MODE.data_ofdm_1700.value)
        self.data_ofdm_2438_tx = codec2.open_instance(codec2.FREEDV_MODE.data_ofdm_2438.value)
        self.data_vhf_1 = codec2.open_instance(codec2.FREEDV_MODE.data_vhf_1.value)

        #self.freedv_qam16c2_tx = codec2.open_instance(codec2.FREEDV_MODE.qam16c2.value)
        #self.data_qam_2438_tx = codec2.open_instance(codec2.FREEDV_MODE.data_qam_2438.value)

    def transmit_add_preamble(self, buffer, freedv):
        """Adds a preamble to the transmit buffer.

        This method adds a preamble to the given buffer based on the
        provided FreeDV instance. The preamble is generated using the
        `freedv_rawdatapreambletx` function from the Codec2 API.

        Args:
            buffer (bytes): The buffer to add the preamble to.
            freedv: The FreeDV instance.

        Returns:
            bytes: The buffer with the preamble appended.
        """
        # Init buffer for preample
        n_tx_preamble_modem_samples = codec2.api.freedv_get_n_tx_preamble_modem_samples(
            freedv
        )
        mod_out_preamble = ctypes.create_string_buffer(n_tx_preamble_modem_samples * 2)

        # Write preamble to txbuffer
        codec2.api.freedv_rawdatapreambletx(freedv, mod_out_preamble)
        buffer += bytes(mod_out_preamble)
        return buffer

    def transmit_add_postamble(self, buffer, freedv):
        """Adds a postamble to the transmit buffer.

        This method adds a postamble to the given buffer based on the
        provided FreeDV instance. The postamble is generated using the
        `freedv_rawdatapostambletx` function from the Codec2 API.

        Args:
            buffer (bytes): The buffer to add the postamble to.
            freedv: The FreeDV instance.

        Returns:
            bytes: The buffer with the postamble appended.
        """
        # Init buffer for postamble
        n_tx_postamble_modem_samples = (
            codec2.api.freedv_get_n_tx_postamble_modem_samples(freedv)
        )
        mod_out_postamble = ctypes.create_string_buffer(
            n_tx_postamble_modem_samples * 2
        )
        # Write postamble to txbuffer
        codec2.api.freedv_rawdatapostambletx(freedv, mod_out_postamble)
        # Append postamble to txbuffer
        buffer += bytes(mod_out_postamble)
        return buffer

    def transmit_add_silence(self, buffer, duration):
        """Adds silence to the transmit buffer.

        This method adds a specified duration of silence to the given buffer.
        The silence is represented as an empty buffer of the appropriate
        size based on the modem sample rate.

        Args:
            buffer (bytes): The buffer to add silence to.
            duration (int): The duration of silence in milliseconds.

        Returns:
            bytes: The buffer with the silence appended.
        """
        data_delay = int(self.modem_sample_rate * (duration / 1000))  # type: ignore
        mod_out_silence = ctypes.create_string_buffer(data_delay * 2)
        buffer += bytes(mod_out_silence)
        return buffer

    def transmit_create_frame(self, txbuffer, freedv, frame):
        """Creates and modulates a data frame.

        This method creates a data frame with a CRC checksum, modulates it
        using the provided FreeDV instance, and appends the modulated data
        to the given transmit buffer. It uses the Codec2 API for CRC
        generation and modulation.

        Args:
            txbuffer (bytes): The transmit buffer to append to.
            freedv: The FreeDV instance.
            frame (bytes): The data frame to modulate.

        Returns:
            bytes: The updated transmit buffer.
        """
        # Get number of bytes per frame for mode
        bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv) / 8)
        payload_bytes_per_frame = bytes_per_frame - 2
        #print(payload_bytes_per_frame)
        # Init buffer for data
        n_tx_modem_samples = codec2.api.freedv_get_n_tx_modem_samples(freedv)
        mod_out = ctypes.create_string_buffer(n_tx_modem_samples * 2)

        # Create buffer for data
        # Use this if CRC16 checksum is required (DATAc1-3)
        buffer = bytearray(payload_bytes_per_frame)
        # Set buffersize to length of data which will be sent
        buffer[: len(frame)] = frame  # type: ignore

        # Create crc for data frame -
        #   Use the crc function shipped with codec2
        #   to avoid CRC algorithm incompatibilities
        # Generate CRC16
        crc = ctypes.c_ushort(
            codec2.api.freedv_gen_crc16(bytes(buffer), payload_bytes_per_frame)
        )
        # Convert crc to 2-byte (16-bit) hex string
        crc = crc.value.to_bytes(2, byteorder="big")
        # Append CRC to data buffer
        buffer += crc
        assert (bytes_per_frame == len(buffer))
        data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
        # modulate DATA and save it into mod_out pointer
        codec2.api.freedv_rawdatatx(freedv, mod_out, data)
        txbuffer += bytes(mod_out)
        return txbuffer

    def create_burst(
            self, mode, repeats: int, repeat_delay: int, frames: bytearray
    ) -> bytes:
        """Creates a burst of modulated frames.

        This method creates a burst transmission by repeating the given
        frames multiple times with a specified delay between repetitions.
        It adds preambles, postambles, and silence to the transmission as
        needed. It selects the appropriate FreeDV instance based on the
        provided mode and handles potential mode transitions.

        Args:
            mode: The FreeDV mode to use for modulation.
            repeats (int): The number of times to repeat the frames.
            repeat_delay (int): The delay between repetitions in milliseconds.
            frames (bytearray or list): The frame(s) to modulate and transmit as a burst. Can be a single frame as a bytearray or a list of frames.

        Returns:
            bytes: The modulated burst data.
        """
        # get freedv instance by mode
        mode_transition = {
            codec2.FREEDV_MODE.signalling_ack: self.freedv_datac14_tx,
            codec2.FREEDV_MODE.signalling: self.freedv_datac13_tx,
            codec2.FREEDV_MODE.datac0: self.freedv_datac0_tx,
            codec2.FREEDV_MODE.datac1: self.freedv_datac1_tx,
            codec2.FREEDV_MODE.datac3: self.freedv_datac3_tx,
            codec2.FREEDV_MODE.datac4: self.freedv_datac4_tx,
            codec2.FREEDV_MODE.datac13: self.freedv_datac13_tx,
            codec2.FREEDV_MODE.datac14: self.freedv_datac14_tx,
            codec2.FREEDV_MODE.data_ofdm_200: self.data_ofdm_200_tx,
            codec2.FREEDV_MODE.data_ofdm_250: self.data_ofdm_250_tx,
            codec2.FREEDV_MODE.data_ofdm_500: self.data_ofdm_500_tx,
            codec2.FREEDV_MODE.data_ofdm_1700: self.data_ofdm_1700_tx,
            codec2.FREEDV_MODE.data_ofdm_2438: self.data_ofdm_2438_tx,
            #codec2.FREEDV_MODE.qam16c2: self.freedv_qam16c2_tx,
            #codec2.FREEDV_MODE.data_qam_2438: self.freedv_data_qam_2438_tx,
            codec2.FREEDV_MODE.data_vhf_1: self.data_vhf_1
        }
        if mode in mode_transition:
            freedv = mode_transition[mode]
        else:
            print("wrong mode.................")
            print(mode)
            #return False


        # Open codec2 instance
        self.MODE = mode
        self.log.debug(
            "[MDM] TRANSMIT", mode=self.MODE.name, delay=self.tx_delay
        )

        txbuffer = bytes()


        # Add empty data to handle ptt toggle time
        if self.tx_delay > 0:
            txbuffer = self.transmit_add_silence(txbuffer, self.tx_delay)

        if not isinstance(frames, list): frames = [frames]
        for _ in range(repeats):

            # Create modulation for all frames in the list
            for frame in frames:
                if not self.config['EXP'].get('enable_vhf'):
                    txbuffer = self.transmit_add_preamble(txbuffer, freedv)
                txbuffer = self.transmit_create_frame(txbuffer, freedv, frame)
                if not self.config['EXP'].get('enable_vhf'):
                    txbuffer = self.transmit_add_postamble(txbuffer, freedv)

            # Add delay to end of frames
            txbuffer = self.transmit_add_silence(txbuffer, repeat_delay)

        return txbuffer

