
import sys
import threading
import time
import lzma
from random import randrange
import hmac
import hashlib
import helpers
import modem
import numpy as np
from codec2 import FREEDV_MODE
from modem_frametypes import FRAME_TYPE as FR_TYPE

from data_handler_arq import ARQ

class ISS(ARQ):
    def __init__(self, config, event_queue, states):
        super().__init__(config, event_queue, states)

        self.tx_n_max_retries_per_burst = 40
        self.datachannel_opening_interval = self.duration_sig1_frame + self.channel_busy_timeout + 1  # time between attempts when opening data channel
        self.irs_buffer_position = 0
        # actual n retries of burst
        self.tx_n_retry_of_burst = 0
        self.burst_ack_snr = 0  # SNR from received burst ack frames



    def arq_transmit(self, data_out: bytes, hmac_salt: bytes):
        """
        Transmit ARQ frame

        Args:
          data_out:bytes:


        """

        # set signalling modes we want to listen to
        # we are in an ongoing arq transmission, so we don't need sig0 actually
        modem.RECEIVE_SIG0 = False
        modem.RECEIVE_SIG1 = True

        self.tx_n_retry_of_burst = 0  # retries we already sent data
        # Maximum number of retries to send before declaring a frame is lost

        # save len of data_out to TOTAL_BYTES for our statistics
        self.states.set("arq_total_bytes", len(data_out))

        self.arq_file_transfer = True
        frame_total_size = len(data_out).to_bytes(4, byteorder="big")

        # Compress data frame
        data_frame_compressed = lzma.compress(data_out)
        compression_factor = len(data_out) / len(data_frame_compressed)
        self.arq_compression_factor = np.clip(compression_factor, 0, 255)
        compression_factor = bytes([int(self.arq_compression_factor * 10)])

        self.send_data_to_socket_queue(
            freedata="modem-message",
            arq="transmission",
            status="transmitting",
            uuid=self.transmission_uuid,
            percent=self.states.arq_transmission_percent,
            bytesperminute=self.states.arq_bytes_per_minute,
            compression=self.arq_compression_factor,
            finished=self.states.arq_seconds_until_finish,
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            irs=helpers.bool_to_string(self.is_IRS)
        )

        self.log.info(
            "[Modem] | TX | DATACHANNEL",
            Bytes=self.states.arq_total_bytes,
        )

        data_out = data_frame_compressed

        # Reset data transfer statistics
        tx_start_of_transmission = time.time()
        self.calculate_transfer_rate_tx(tx_start_of_transmission, 0, len(data_out))

        # check if hmac signature is available
        if hmac_salt not in ['', False]:
            print(data_out)
            # create hmac digest
            hmac_digest = hmac.new(hmac_salt, data_out, hashlib.sha256).digest()
            # truncate to 32bit
            frame_payload_crc = hmac_digest[:4]
            self.log.debug("[Modem] frame payload HMAC:", crc=frame_payload_crc.hex())

        else:
            # Append a crc at the beginning and end of file indicators
            frame_payload_crc = helpers.get_crc_32(data_out)
            self.log.debug("[Modem] frame payload CRC:", crc=frame_payload_crc.hex())

        # Assemble the data frame
        data_out = (
                self.data_frame_bof
                + frame_payload_crc
                + frame_total_size
                + compression_factor
                + data_out
                + self.data_frame_eof
        )
        self.log.debug("[Modem] frame raw data:", data=data_out)
        # Initial bufferposition is 0
        bufferposition = 0
        bufferposition_end = 0
        bufferposition_burst_start = 0

        # Iterate through data_out buffer
        while not self.data_frame_ack_received and self.states.is_arq_state:
            # we have self.tx_n_max_retries_per_burst attempts for sending a burst
            for self.tx_n_retry_of_burst in range(self.tx_n_max_retries_per_burst):
                # Bound speed level to:
                # - minimum of either the speed or the length of mode list - 1
                # - maximum of either the speed or zero
                self.speed_level = min(self.speed_level, len(self.mode_list) - 1)
                self.speed_level = max(self.speed_level, 0)

                self.states.set("arq_speed_level", self.speed_level)
                data_mode = self.mode_list[self.speed_level]

                self.log.debug(
                    "[Modem] Speed-level:",
                    level=self.speed_level,
                    retry=self.tx_n_retry_of_burst,
                    mode=FREEDV_MODE(data_mode).name,
                )

                # Payload information
                payload_per_frame = modem.get_bytes_per_frame(data_mode) - 2

                self.log.info("[Modem] early buffer info",
                              bufferposition=bufferposition,
                              bufferposition_end=bufferposition_end,
                              bufferposition_burst_start=bufferposition_burst_start
                              )

                # check for maximum frames per burst for remaining data
                n_frames_per_burst = 1
                if self.max_n_frames_per_burst > 1:
                    while (payload_per_frame * n_frames_per_burst) % len(data_out[bufferposition_burst_start:]) == (
                            payload_per_frame * n_frames_per_burst):
                        threading.Event().wait(0.01)
                        # print((payload_per_frame * n_frames_per_burst) % len(data_out))
                        n_frames_per_burst += 1
                        if n_frames_per_burst == self.max_n_frames_per_burst:
                            break
                else:
                    n_frames_per_burst = 1
                self.log.info("[Modem] calculated frames_per_burst:", n=n_frames_per_burst)

                tempbuffer = []
                self.rpt_request_buffer = []
                # Append data frames with n_frames_per_burst to tempbuffer
                for n_frame in range(n_frames_per_burst):
                    arqheader = bytearray()
                    arqheader[:1] = bytes([FR_TYPE.BURST_01.value + n_frame])
                    #####arqheader[:1] = bytes([FR_TYPE.BURST_01.value])
                    arqheader[1:2] = bytes([n_frames_per_burst])
                    arqheader[2:3] = self.session_id

                    # only check for buffer position if at least one NACK received
                    self.log.info("[Modem] ----- data buffer position:", iss_buffer_pos=bufferposition,
                                  irs_bufferposition=self.irs_buffer_position)
                    if self.frame_nack_counter > 0 and self.irs_buffer_position != bufferposition:
                        self.log.error("[Modem] ----- data buffer offset:", iss_buffer_pos=bufferposition,
                                       irs_bufferposition=self.irs_buffer_position)
                        # only adjust buffer position for experimental versions
                        if self.enable_experimental_features:
                            self.log.warning("[Modem] ----- data adjustment enabled!")
                            bufferposition = self.irs_buffer_position

                    bufferposition_end = bufferposition + payload_per_frame - len(arqheader)

                    # Normal condition
                    if bufferposition_end <= len(data_out):
                        frame = data_out[bufferposition:bufferposition_end]
                        frame = arqheader + frame

                    # Pad the last bytes of a frame
                    else:
                        extended_data_out = data_out[bufferposition:]
                        extended_data_out += bytes([0]) * (
                                payload_per_frame - len(extended_data_out) - len(arqheader)
                        )
                        frame = arqheader + extended_data_out

                    ######tempbuffer = frame  # [frame]
                    tempbuffer.append(frame)
                    # add data to our repeat request buffer for easy access if we received a request
                    self.rpt_request_buffer.append(frame)
                    # set new buffer position
                    bufferposition = bufferposition_end

                    self.log.debug("[Modem] tempbuffer:", tempbuffer=tempbuffer)
                    self.log.info(
                        "[Modem] ARQ | TX | FRAMES",
                        mode=FREEDV_MODE(data_mode).name,
                        fpb=n_frames_per_burst,
                        retry=self.tx_n_retry_of_burst,
                    )

                self.enqueue_frame_for_tx(tempbuffer, c2_mode=data_mode)

                # After transmission finished, wait for an ACK or RPT frame
                while (
                        self.states.is_arq_state
                        and not self.burst_ack
                        and not self.burst_nack
                        and not self.rpt_request_received
                        and not self.data_frame_ack_received
                ):
                    threading.Event().wait(0.01)

                # Once we receive a burst ack, reset its state and break the RETRIES loop
                if self.burst_ack:
                    self.burst_ack = False  # reset ack state
                    self.tx_n_retry_of_burst = 0  # reset retries
                    self.log.debug(
                        "[Modem] arq_transmit: Received BURST ACK. Sending next chunk."
                        , irs_snr=self.burst_ack_snr)
                    # update temp bufferposition for n frames per burst early calculation
                    bufferposition_burst_start = bufferposition_end
                    break  # break retry loop

                if self.data_frame_ack_received:
                    self.log.debug(
                        "[Modem] arq_transmit: Received FRAME ACK. Braking retry loop."
                    )
                    break  # break retry loop

                if self.burst_nack:
                    self.tx_n_retry_of_burst += 1

                    self.log.warning(
                        "[Modem] arq_transmit: Received BURST NACK. Resending data",
                        bufferposition_burst_start=bufferposition_burst_start,
                        bufferposition=bufferposition
                    )

                    bufferposition = bufferposition_burst_start
                    self.burst_nack = False  # reset nack state

                # We need this part for leaving the repeat loop
                # self.states.is_arq_state == "DATA" --> when stopping transmission manually
                if not self.states.is_arq_state:
                    self.log.debug(
                        "[Modem] arq_transmit: ARQ State changed to FALSE. Breaking retry loop."
                    )
                    break

                self.calculate_transfer_rate_tx(
                    tx_start_of_transmission, bufferposition_end, len(data_out)
                )
                # NEXT ATTEMPT
                self.log.debug(
                    "[Modem] ATTEMPT:",
                    retry=self.tx_n_retry_of_burst,
                    maxretries=self.tx_n_max_retries_per_burst,
                )

            # update buffer position
            bufferposition = bufferposition_end

            # update stats
            self.calculate_transfer_rate_tx(
                tx_start_of_transmission, bufferposition_end, len(data_out)
            )

            self.send_data_to_socket_queue(
                freedata="modem-message",
                arq="transmission",
                status="transmitting",
                uuid=self.transmission_uuid,
                percent=self.states.arq_transmission_percent,
                bytesperminute=self.states.arq_bytes_per_minute,
                compression=self.arq_compression_factor,
                finished=self.states.arq_seconds_until_finish,
                irs_snr=self.burst_ack_snr,
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
                irs=helpers.bool_to_string(self.is_IRS)
            )

            # Stay in the while loop until we receive a data_frame_ack. Otherwise,
            # the loop exits after sending the last frame only once and doesn't
            # wait for an acknowledgement.
            if self.data_frame_ack_received and bufferposition > len(data_out):
                self.log.debug("[Modem] arq_tx: Last fragment sent and acknowledged.")
                break
                # GOING TO NEXT ITERATION

        if self.data_frame_ack_received:
            self.arq_transmit_success()
        else:
            self.arq_transmit_failed()

        if TESTMODE:
            # Quit after transmission
            self.log.debug("[Modem] TESTMODE: arq_transmit exiting.")
            sys.exit(0)

    def arq_transmit_success(self):
        """
        will be called if we successfully transmitted all of queued data

        """
        # we need to wait until sending "transmitted" state
        # gui database is too slow for handling this within 0.001 seconds
        # so let's sleep a little
        threading.Event().wait(0.2)
        self.send_data_to_socket_queue(
            freedata="modem-message",
            arq="transmission",
            status="transmitted",
            uuid=self.transmission_uuid,
            percent=self.states.arq_transmission_percent,
            bytesperminute=self.states.arq_bytes_per_minute,
            compression=self.arq_compression_factor,
            finished=self.states.arq_seconds_until_finish,
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            irs=helpers.bool_to_string(self.is_IRS),
            nacks=self.frame_nack_counter,
            speed_list=self.states.arq_speed_list
        )

        self.log.info(
            "[Modem] ARQ | TX | DATA TRANSMITTED!",
            BytesPerMinute=self.states.arq_bytes_per_minute,
            total_bytes=self.states.arq_total_bytes,
            BitsPerSecond=self.states.arq_bits_per_second,
        )

        # finally do an arq cleanup
        self.arq_cleanup()

    def arq_transmit_failed(self):
        """
        will be called if we not successfully transmitted all of queued data
        """
        self.send_data_to_socket_queue(
            freedata="modem-message",
            arq="transmission",
            status="failed",
            uuid=self.transmission_uuid,
            percent=self.states.arq_transmission_percent,
            bytesperminute=self.states.arq_bytes_per_minute,
            compression=self.arq_compression_factor,
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            irs=helpers.bool_to_string(self.is_IRS),
            nacks=self.frame_nack_counter,
            speed_list=self.states.arq_speed_list
        )

        self.log.info(
            "[Modem] ARQ | TX | TRANSMISSION FAILED OR TIME OUT!")

        self.stop_transmission()

    def burst_ack_nack_received(self, data_in: bytes, snr) -> None:
        """
        Received an ACK/NACK for a transmitted frame, keep track and
        make adjustments to speed level if needed.

        Args:
          data_in:bytes:

        Returns:

        """
        # Process data only if we are in ARQ and BUSY state
        if self.states.is_arq_state:
            self.dxgrid = b'------'
            helpers.add_to_heard_stations(
                self.dxcallsign,
                self.dxgrid,
                "DATA",
                snr,
                self.modem_frequency_offset,
                self.states.radio_frequency,
                self.states.heard_stations
            )

            frametype = int.from_bytes(bytes(data_in[:1]), "big")
            if frametype == FR_TYPE.BURST_ACK.value:
                # Increase speed level if we received a burst ack
                # self.speed_level = min(self.speed_level + 1, len(self.mode_list) - 1)
                # Force data retry loops of TX Modem to stop and continue with next frame
                self.burst_ack = True
                # Reset burst nack counter
                self.burst_nack_counter = 0
                # Reset n retries per burst counter
                self.n_retries_per_burst = 0
                self.irs_buffer_position = int.from_bytes(data_in[4:8], "big")

                self.burst_ack_snr = helpers.snr_from_bytes(data_in[2:3])
            else:

                # Decrease speed level if we received a burst nack
                # self.speed_level = max(self.speed_level - 1, 0)
                # Set flag to retry frame again.
                self.burst_nack = True
                # Increment burst nack counter
                self.burst_nack_counter += 1
                self.burst_ack_snr = 'NaN'
                self.irs_buffer_position = int.from_bytes(data_in[5:9], "big")

                self.log.warning(
                    "[Modem] ARQ | TX | Burst NACK received",
                    burst_nack_counter=self.burst_nack_counter,
                    irs_buffer_position=self.irs_buffer_position,
                )

            # Update data_channel timestamp
            self.data_channel_last_received = int(time.time())
            # self.burst_ack_snr = int.from_bytes(bytes(data_in[2:3]), "big")
            self.burst_ack_snr = helpers.snr_from_bytes(data_in[2:3])
            # self.log.info("SNR ON IRS", snr=self.burst_ack_snr)

            self.speed_level = int.from_bytes(bytes(data_in[3:4]), "big")
            self.states.set("arq_speed_level", self.speed_level)

    def frame_ack_received(
            self, data_in: bytes, snr  # pylint: disable=unused-argument,
    ) -> None:
        """Received an ACK for a transmitted frame"""
        # Process data only if we are in ARQ and BUSY state
        if self.states.is_arq_state:
            self.dxgrid = b'------'
            helpers.add_to_heard_stations(
                self.dxcallsign,
                self.dxgrid,
                "DATA",
                snr,
                self.modem_frequency_offset,
                self.states.radio_frequency,
                self.states.heard_stations
            )
            # Force data loops of Modem to stop and continue with next frame
            self.data_frame_ack_received = True
            # Update arq_session and data_channel timestamp
            self.data_channel_last_received = int(time.time())
            self.arq_session_last_received = int(time.time())

    def frame_nack_received(
            self, data_in: bytes, snr  # pylint: disable=unused-argument
    ) -> None:
        """
        Received a NACK for a transmitted frame

        Args:
          data_in:bytes:

        """
        self.log.warning("[Modem] ARQ FRAME NACK RECEIVED - cleanup!",
                         arq="transmission",
                         status="failed",
                         uuid=self.transmission_uuid,
                         percent=self.states.arq_transmission_percent,
                         bytesperminute=self.states.arq_bytes_per_minute,
                         mycallsign=str(self.mycallsign, 'UTF-8'),
                         dxcallsign=str(self.dxcallsign, 'UTF-8'),
                         irs=helpers.bool_to_string(self.is_IRS),
                         nacks=self.frame_nack_counter,
                         speed_list=self.states.arq_speed_list
                         )

        self.dxgrid = b'------'
        helpers.add_to_heard_stations(
            self.dxcallsign,
            self.dxgrid,
            "DATA",
            snr,
            self.modem_frequency_offset,
            self.states.radio_frequency,
            self.states.heard_stations
        )
        self.send_data_to_socket_queue(
            freedata="modem-message",
            arq="transmission",
            status="failed",
            uuid=self.transmission_uuid,
            percent=self.states.arq_transmission_percent,
            bytesperminute=self.states.arq_bytes_per_minute,
            compression=self.arq_compression_factor,
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            irs=helpers.bool_to_string(self.is_IRS),
            nacks=self.frame_nack_counter,
            speed_list=self.states.arq_speed_list
        )
        # Update data_channel timestamp
        self.arq_session_last_received = int(time.time())

        self.arq_cleanup()

    def burst_rpt_received(self, data_in: bytes, snr):
        """
        Repeat request frame received for transmitted frame

        Args:
          data_in:bytes:

        """
        # Only process data if we are in ARQ and BUSY state
        if not self.states.is_arq_state or not self.states.is_modem_busy:
            return
        self.dxgrid = b'------'
        helpers.add_to_heard_stations(
            self.dxcallsign,
            self.dxgrid,
            "DATA",
            snr,
            self.modem_frequency_offset,
            self.states.radio_frequency,
            self.states.heard_stations
        )

        self.log.info("[Modem] ARQ REPEAT RECEIVED")

        # self.rpt_request_received = True
        # Update data_channel timestamp
        self.data_channel_last_received = int(time.time())
        # self.rpt_request_buffer = []

        missing_area = bytes(data_in[2:12])  # 1:9
        missing_area = missing_area.strip(b"\x00")
        print(missing_area)
        print(self.rpt_request_buffer)

        tempbuffer_rptframes = []
        for i in range(len(missing_area)):
            print(missing_area[i])
            missing_frames_buffer_position = missing_area[i] - 1
            tempbuffer_rptframes.append(self.rpt_request_buffer[missing_frames_buffer_position])

        self.log.info("[Modem] SENDING REPEAT....")
        data_mode = self.mode_list[self.speed_level]
        self.enqueue_frame_for_tx(tempbuffer_rptframes, c2_mode=data_mode)


############################################################################################################
    # ARQ SESSION HANDLER
    ############################################################################################################
    def arq_session_handler(self, mycallsign, dxcallsign) -> bool:
        """
        Create a session with `self.dxcallsign` and wait until the session is open.

        Returns:
            True if the session was opened successfully
            False if the session open request failed
        """

        encoded_call = helpers.callsign_to_bytes(mycallsign)
        mycallsign = helpers.bytes_to_callsign(encoded_call)

        encoded_call = helpers.callsign_to_bytes(dxcallsign)
        dxcallsign = helpers.bytes_to_callsign(encoded_call)

        self.states.set("dxcallsign", dxcallsign)
        dxcallsign_crc = helpers.get_crc_24(dxcallsign)

        self.log.info(
            "[Modem] SESSION ["
            + str(mycallsign, "UTF-8")
            + "]>> <<["
            + str(dxcallsign, "UTF-8")
            + "]",
            self.states.arq_session_state,
        )

        # wait if  we have a channel busy condition
        if self.states.channel_busy:
            self.channel_busy_handler()

        self.open_session()

        # wait until data channel is open
        while not self.states.is_arq_session and not self.arq_session_timeout:
            threading.Event().wait(0.01)
            self.states.set("arq_session_state", "connecting")
            self.send_data_to_socket_queue(
                freedata="modem-message",
                arq="session",
                status="connecting",
                mycallsign=str(mycallsign, 'UTF-8'),
                dxcallsign=str(dxcallsign, 'UTF-8'),
            )
        if self.states.is_arq_session and self.states.arq_session_state == "connected":
            # self.states.set("arq_session_state", "connected")
            self.send_data_to_socket_queue(
                freedata="modem-message",
                arq="session",
                status="connected",
                mycallsign=str(mycallsign, 'UTF-8'),
                dxcallsign=str(dxcallsign, 'UTF-8'),
            )
            return True

        self.log.warning(
            "[Modem] SESSION FAILED ["
            + str(mycallsign, "UTF-8")
            + "]>>X<<["
            + str(dxcallsign, "UTF-8")
            + "]",
            attempts=self.session_connect_max_retries,  # Adjust for 0-based for user display
            reason="maximum connection attempts reached",
            state=self.states.arq_session_state,
        )
        self.states.set("arq_session_state", "failed")
        self.send_data_to_socket_queue(
            freedata="modem-message",
            arq="session",
            status="failed",
            reason="timeout",
            mycallsign=str(mycallsign, 'UTF-8'),
            dxcallsign=str(dxcallsign, 'UTF-8'),
        )
        return False

    def open_session(self) -> bool:
        """
        Create and send the frame to request a connection.

        Returns:
            True if the session was opened successfully
            False if the session open request failed
        """
        self.IS_ARQ_SESSION_MASTER = True
        self.states.set("arq_session_state", "connecting")

        # create a random session id
        self.session_id = np.random.bytes(1)

        connection_frame = bytearray(self.length_sig0_frame)
        connection_frame[:1] = bytes([FR_TYPE.ARQ_SESSION_OPEN.value])
        connection_frame[1:2] = self.session_id
        connection_frame[2:5] = self.dxcallsign_crc
        connection_frame[5:8] = self.mycallsign_crc
        connection_frame[8:14] = helpers.callsign_to_bytes(self.mycallsign)

        while not self.states.is_arq_session:
            threading.Event().wait(0.01)
            for attempt in range(self.session_connect_max_retries):
                self.log.info(
                    "[Modem] SESSION ["
                    + str(self.mycallsign, "UTF-8")
                    + "]>>?<<["
                    + str(self.dxcallsign, "UTF-8")
                    + "]",
                    a=f"{str(attempt + 1)}/{str(self.session_connect_max_retries)}",
                    state=self.states.arq_session_state,
                )

                self.send_data_to_socket_queue(
                    freedata="modem-message",
                    arq="session",
                    status="connecting",
                    attempt=attempt + 1,
                    maxattempts=self.session_connect_max_retries,
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                )

                self.enqueue_frame_for_tx([connection_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1, repeat_delay=0)

                # Wait for a time, looking to see if `self.states.is_arq_session`
                # indicates we've received a positive response from the far station.
                timeout = time.time() + 3
                while time.time() < timeout:
                    threading.Event().wait(0.01)
                    # Stop waiting if data channel is opened
                    if self.states.is_arq_session:
                        return True

                    # Stop waiting and interrupt if data channel is getting closed while opening
                    if self.states.arq_session_state == "disconnecting":
                        # disabled this session close as its called twice
                        # self.close_session()
                        return False

            # Session connect timeout, send close_session frame to
            # attempt to clean up the far-side, if it received the
            # open_session frame and can still hear us.
            if not self.states.is_arq_session:
                self.close_session()
                return False

        # Given the while condition, it will only exit when `self.states.is_arq_session` is True
        self.send_data_to_socket_queue(
            freedata="modem-message",
            arq="session",
            status="connected",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )
        return True

    def open_dc_and_transmit(
            self,
            data_out: bytes,
            transmission_uuid: str,
            mycallsign,
            dxcallsign,
    ) -> bool:
        """
        Open data channel and transmit data

        Args:
          data_out:bytes:
          transmission_uuid:str:
          mycallsign:bytes:

        Returns:
            True if the data session was opened and the data was sent
            False if the data session was not opened
        """
        self.mycallsign = mycallsign

        # additional step for being sure our callsign is correctly
        # in case we are not getting a station ssid
        # then we are forcing a station ssid = 0
        if not self.states.is_arq_session:
            dxcallsign = helpers.callsign_to_bytes(dxcallsign)
            dxcallsign = helpers.bytes_to_callsign(dxcallsign)
            self.dxcallsign = dxcallsign

        self.dxcallsign_crc = helpers.get_crc_24(self.dxcallsign)

        # check if hmac hash is provided
        try:
            self.log.info("[SCK] [HMAC] Looking for salt/token", local=mycallsign, remote=dxcallsign)
            hmac_salt = helpers.get_hmac_salt(dxcallsign, mycallsign)
            self.log.info("[SCK] [HMAC] Salt info", local=mycallsign, remote=dxcallsign, salt=hmac_salt)
        except Exception:
            self.log.warning("[SCK] [HMAC] No salt/token found")
            hmac_salt = ''

        self.states.set("is_modem_busy", True)
        self.arq_file_transfer = True
        self.beacon_paused = True

        self.transmission_uuid = transmission_uuid

        # wait a moment for the case, a heartbeat is already on the way back to us
        # this makes channel establishment more clean
        if self.states.is_arq_session:
            threading.Event().wait(2.5)

        # init arq state event
        self.arq_state_event = threading.Event()

        # finally start the channel opening procedure
        self.arq_open_data_channel(mycallsign)

        # if data channel is open, return true else false
        if self.arq_state_event.is_set():
            # start arq transmission
            self.arq_transmit(data_out, hmac_salt)
            return True

        else:
            self.log.debug(
                "[Modem] arq_open_data_channel:", transmission_uuid=self.transmission_uuid
            )

            self.send_data_to_socket_queue(
                freedata="modem-message",
                arq="transmission",
                status="failed",
                reason="unknown",
                uuid=self.transmission_uuid,
                percent=self.states.arq_transmission_percent,
                bytesperminute=self.states.arq_bytes_per_minute,
                compression=self.arq_compression_factor,
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
                irs=helpers.bool_to_string(self.is_IRS),
                nacks=self.frame_nack_counter,
                speed_list=self.states.arq_speed_list
            )

            self.log.warning(
                "[Modem] ARQ | TX | DATA ["
                + str(mycallsign, "UTF-8")
                + "]>>X<<["
                + str(self.dxcallsign, "UTF-8")
                + "]"
            )

            # Attempt to clean up the far-side, if it received the
            # open_session frame and can still hear us.
            self.close_session()

            # release beacon pause
            self.beacon_paused = False

            # otherwise return false
            return False

    def arq_open_data_channel(
            self, mycallsign
    ) -> bool:
        """
        Open an ARQ data channel.

        Args:
          mycallsign:bytes:

        Returns:
            True if the data channel was opened successfully
            False if the data channel failed to open
        """
        # set IRS indicator to false, because we are IRS
        self.is_IRS = False

        # init a new random session id if we are not in an arq session
        if not self.states.is_arq_session:
            self.session_id = np.random.bytes(1)

        # Update data_channel timestamp
        self.data_channel_last_received = int(time.time())

        # check if the Modem is running in low bandwidth mode
        # then set the corresponding frametype and build frame
        if self.low_bandwidth_mode:
            frametype = bytes([FR_TYPE.ARQ_DC_OPEN_N.value])
            self.log.debug("[Modem] Requesting low bandwidth mode")
        else:
            frametype = bytes([FR_TYPE.ARQ_DC_OPEN_W.value])
            self.log.debug("[Modem] Requesting high bandwidth mode")

        connection_frame = bytearray(self.length_sig0_frame)
        connection_frame[:1] = frametype
        connection_frame[1:4] = self.dxcallsign_crc
        connection_frame[4:7] = self.mycallsign_crc
        connection_frame[7:13] = helpers.callsign_to_bytes(mycallsign)
        connection_frame[13:14] = self.session_id

        for attempt in range(self.data_channel_max_retries):

            self.send_data_to_socket_queue(
                freedata="modem-message",
                arq="transmission",
                status="opening",
                mycallsign=mycallsign,
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
                irs=helpers.bool_to_string(self.is_IRS)
            )

            self.log.info(
                "[Modem] ARQ | DATA | TX | ["
                + mycallsign
                + "]>> <<["
                + str(self.dxcallsign, "UTF-8")
                + "]",
                attempt=f"{str(attempt + 1)}/{str(self.data_channel_max_retries)}",
            )

            # Let's check if we have a busy channel and if we are not in a running arq session.
            if self.states.channel_busy and not self.arq_state_event.is_set() or self.states.is_codec2_traffic:
                self.channel_busy_handler()

            # if channel free, enqueue frame for tx
            if not self.arq_state_event.is_set():
                self.enqueue_frame_for_tx([connection_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1, repeat_delay=0)

            # wait until timeout or event set

            random_wait_time = randrange(int(self.duration_sig1_frame * 10),
                                         int(self.datachannel_opening_interval * 10), 1) / 10
            self.arq_state_event.wait(timeout=random_wait_time)

            if self.arq_state_event.is_set():
                return True
            if not self.states.is_modem_busy:
                return False

        # `data_channel_max_retries` attempts have been sent. Aborting attempt & cleaning up
        return False

    def arq_received_channel_is_open(self, data_in: bytes, snr) -> None:
        """
        Called if we received a data channel opener
        Args:
          data_in:bytes:

        """
        protocol_version = int.from_bytes(bytes(data_in[13:14]), "big")
        if protocol_version == self.arq_protocol_version:
            self.send_data_to_socket_queue(
                freedata="modem-message",
                arq="transmission",
                status="opened",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
                irs=helpers.bool_to_string(self.is_IRS)
            )
            frametype = int.from_bytes(bytes(data_in[:1]), "big")

            if frametype == FR_TYPE.ARQ_DC_OPEN_ACK_N.value:
                self.received_LOW_BANDWIDTH_MODE = True
                self.mode_list = self.mode_list_low_bw
                self.time_list = self.time_list_low_bw
                self.log.debug("[Modem] low bandwidth mode", modes=self.mode_list)
            else:
                self.received_LOW_BANDWIDTH_MODE = False
                self.mode_list = self.mode_list_high_bw
                self.time_list = self.time_list_high_bw
                self.log.debug("[Modem] high bandwidth mode", modes=self.mode_list)

            # set speed level from session opener frame delegation
            self.speed_level = int.from_bytes(bytes(data_in[8:9]), "big")
            self.log.debug("[Modem] speed level selected for given SNR", speed_level=self.speed_level)

            self.dxgrid = b'------'
            helpers.add_to_heard_stations(
                self.dxcallsign,
                self.dxgrid,
                "DATA",
                snr,
                self.modem_frequency_offset,
                self.states.radio_frequency,
                self.states.heard_stations
            )

            self.log.info(
                "[Modem] ARQ | DATA | TX | ["
                + str(self.mycallsign, "UTF-8")
                + "]>>|<<["
                + str(self.dxcallsign, "UTF-8")
                + "]",
                snr=snr,
            )

            # as soon as we set ARQ_STATE to True, transmission starts
            self.states.set("is_arq_state", True)
            # also set the ARQ event
            self.arq_state_event.set()

            # Update data_channel timestamp
            self.data_channel_last_received = int(time.time())

        else:
            self.send_data_to_socket_queue(
                freedata="modem-message",
                arq="transmission",
                status="failed",
                reason="protocol version missmatch",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
                irs=helpers.bool_to_string(self.is_IRS)
            )
            self.log.warning(
                "[Modem] protocol version mismatch:",
                received=protocol_version,
                own=self.arq_protocol_version,
            )
            self.stop_transmission()

    def calculate_transfer_rate_tx(
            self, tx_start_of_transmission: float, sentbytes: int, tx_buffer_length: int
    ) -> list:
        """
        Calculate transfer rate for transmission
        Args:
          tx_start_of_transmission:float:
          sentbytes:int:
          tx_buffer_length:int:

        Returns: List of:
            bits_per_second: float,
            bytes_per_minute: float,
            transmission_percent: float
        """
        try:
            arq_transmission_percent = min(
                int((sentbytes / tx_buffer_length) * 100), 100
            )

            transmissiontime = time.time() - tx_start_of_transmission

            if sentbytes > 0:
                arq_bits_per_second = int((sentbytes * 8) / transmissiontime)
                bytes_per_minute = int(sentbytes / (transmissiontime / 60))
                arq_seconds_until_finish = int(((tx_buffer_length - sentbytes) / (
                        bytes_per_minute * self.arq_compression_factor)) * 60)

                speed_chart = {"snr": self.burst_ack_snr, "bpm": bytes_per_minute,
                               "timestamp": int(time.time())}
                # check if data already in list
                if speed_chart not in self.states.arq_speed_list:
                    self.states.arq_speed_list.append(speed_chart)

            else:
                arq_bits_per_second = 0
                bytes_per_minute = 0
                arq_seconds_until_finish = 0

        except Exception as err:
            self.log.error(f"[Modem] calculate_transfer_rate_tx: Exception: {err}")
            arq_transmission_percent = 0.0
            arq_bits_per_second = 0
            bytes_per_minute = 0

        self.states.set("arq_bits_per_second", arq_bits_per_second)
        self.states.set("bytes_per_minute", bytes_per_minute)
        self.states.set("arq_transmission_percent", arq_transmission_percent)
        self.states.set("arq_compression_factor", self.arq_compression_factor)
