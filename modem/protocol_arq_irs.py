
import base64
import time
import uuid
import lzma
import helpers
import numpy as np
from codec2 import FREEDV_MODE
from queues import RX_BUFFER
from modem_frametypes import FRAME_TYPE as FR_TYPE

from protocol_arq import ARQ


class IRS(ARQ):
    def __init__(self, config, event_queue, states):
        super().__init__(config, event_queue, states)


        self.arq_rx_burst_buffer = []
        self.arq_rx_frame_buffer = b""
        self.rx_n_max_retries_per_burst = 40
        self.rx_n_frame_of_burst = 0
        self.rx_n_frames_per_burst = 0


        self.rx_frame_bof_received = False
        self.rx_frame_eof_received = False

        self.rx_start_of_transmission = 0  # time of transmission start


        # minimum payload for arq burst
        # import for avoiding byteorder bug and buffer search area
        self.arq_burst_header_size = 3
        self.arq_burst_minimum_payload = 56 - self.arq_burst_header_size
        self.arq_burst_maximum_payload = 510 - self.arq_burst_header_size
        # save last used payload for optimising buffer search area
        self.arq_burst_last_payload = self.arq_burst_maximum_payload




    def arq_process_received_data_frame(self, data_frame, snr, signed):
        """


        """
        # transmittion duration

        signed = "True" if signed else "False"

        duration = time.time() - self.rx_start_of_transmission
        self.calculate_transfer_rate_rx(
            self.rx_start_of_transmission, len(self.arq_rx_frame_buffer), snr
        )
        self.log.info("[Modem] ARQ | RX | DATA FRAME SUCCESSFULLY RECEIVED", nacks=self.frame_nack_counter,
                      bytesperminute=self.states.arq_bytes_per_minute, total_bytes=self.states.arq_total_bytes,
                      duration=duration, hmac_signed=signed)

        # Decompress the data frame
        data_frame_decompressed = lzma.decompress(data_frame)
        self.arq_compression_factor = len(data_frame_decompressed) / len(
            data_frame
        )
        data_frame = data_frame_decompressed

        self.transmission_uuid = str(uuid.uuid4())
        timestamp = int(time.time())

        # Re-code data_frame in base64, UTF-8 for JSON UI communication.
        base64_data = base64.b64encode(data_frame).decode("UTF-8")

        # check if RX_BUFFER isn't full
        if not RX_BUFFER.full():
            # make sure we have always the correct buffer size
            RX_BUFFER.maxsize = int(self.arq_rx_buffer_size)
        else:
            # if full, free space by getting an item
            self.log.info(
                "[Modem] ARQ | RX | RX_BUFFER FULL - dropping old data",
                buffer_size=RX_BUFFER.qsize(),
                maxsize=int(self.arq_rx_buffer_size)
            )
            RX_BUFFER.get()

        # add item to RX_BUFFER
        self.log.info(
            "[Modem] ARQ | RX | saving data to rx buffer",
            buffer_size=RX_BUFFER.qsize() + 1,
            maxsize=RX_BUFFER.maxsize
        )
        try:
            #  RX_BUFFER[0] = transmission uuid
            #  RX_BUFFER[1] = timestamp
            #  RX_BUFFER[2] = dxcallsign
            #  RX_BUFFER[3] = dxgrid
            #  RX_BUFFER[4] = data
            #  RX_BUFFER[5] = hmac signed
            #  RX_BUFFER[6] = compression factor
            #  RX_BUFFER[7] = bytes per minute
            #  RX_BUFFER[8] = duration
            #  RX_BUFFER[9] = self.frame_nack_counter
            #  RX_BUFFER[10] = speed list stats

            RX_BUFFER.put(
                [
                    self.transmission_uuid,
                    timestamp,
                    self.dxcallsign,
                    self.dxgrid,
                    base64_data,
                    signed,
                    self.arq_compression_factor,
                    self.states.arq_bytes_per_minute,
                    duration,
                    self.frame_nack_counter,
                    self.states.arq_speed_list
                ]
            )
        except Exception as e:
            # File "/usr/lib/python3.7/queue.py", line 133, in put
            #    if self.maxsize > 0
            # TypeError: '>' not supported between instances of 'str' and 'int'
            #
            # Occurs on Raspberry Pi and Python 3.7
            self.log.error(
                "[Modem] ARQ | RX | error occurred when saving data!",
                e=e,
                uuid=self.transmission_uuid,
                timestamp=timestamp,
                dxcall=self.dxcallsign,
                dxgrid=self.dxgrid,
                data=base64_data
            )

        self.event_manager.send_custom_event(
            freedata="modem-message",
            arq="transmission",
            status="received",
            uuid=self.transmission_uuid,
            percent=self.states.arq_transmission_percent,
            bytesperminute=self.states.arq_bytes_per_minute,
            compression=self.arq_compression_factor,
            timestamp=timestamp,
            finished=0,
            mycallsign=str(self.mycallsign, "UTF-8"),
            dxcallsign=str(self.dxcallsign, "UTF-8"),
            dxgrid=str(self.dxgrid, "UTF-8"),
            data=base64_data,
            irs=helpers.bool_to_string(self.is_IRS),
            hmac_signed=signed,
            duration=duration,
            nacks=self.frame_nack_counter,
            speed_list=self.states.arq_speed_list
        )

        if self.enable_stats:
            duration = time.time() - self.rx_start_of_transmission
            self.stats.push(frame_nack_counter=self.frame_nack_counter, status="received", duration=duration)

        self.log.info(
            "[Modem] ARQ | RX | SENDING DATA FRAME ACK")

        self.send_data_ack_frame(snr)
        # Update statistics AFTER the frame ACK is sent
        self.calculate_transfer_rate_rx(
            self.rx_start_of_transmission, len(self.arq_rx_frame_buffer), snr
        )

        self.log.info(
            "[Modem] | RX | DATACHANNEL ["
            + str(self.mycallsign, "UTF-8")
            + "]<< >>["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            snr=snr,
        )


    def arq_received_data_channel_opener(self, data_in: bytes, snr):
        """
        Received request to open data channel frame

        Args:
          data_in:bytes:

        """
        # We've arrived here from process_data which already checked that the frame
        # is intended for this station.

        # stop processing if we don't want to respond to a call when not in a arq session
        if not self.respond_to_call and not self.states.is_arq_session:
            return False

        # stop processing if not in arq session, but modem state is busy and we have a different session id
        # use-case we get a connection request while connecting to another station
        if not self.states.is_arq_session and self.states.is_modem_busy and data_in[13:14] != self.session_id:
            return False

        self.arq_file_transfer = True

        # check if callsign ssid override
        _, self.mycallsign = helpers.check_callsign(self.mycallsign, data_in[1:4], self.ssid_list)

        # ignore channel opener if already in ARQ STATE
        # use case: Station A is connecting to Station B while
        # Station B already tries connecting to Station A.
        # For avoiding ignoring repeated connect request in case of packet loss
        # we are only ignoring packets in case we are ISS
        if self.arq_state_event.is_set() and not self.is_IRS:
            return False

        self.is_IRS = True

        self.dxcallsign_crc = bytes(data_in[4:7])
        self.dxcallsign = helpers.bytes_to_callsign(bytes(data_in[7:13]))
        self.states.set("dxcallsign", self.dxcallsign)

        self.event_manager.send_custom_event(
            freedata="modem-message",
            arq="transmission",
            status="opening",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            irs=helpers.bool_to_string(self.is_IRS)
        )

        frametype = int.from_bytes(bytes(data_in[:1]), "big")
        # check if we received low bandwidth mode
        # possible channel constellations
        # ISS(w) <-> IRS(w)
        # ISS(w) <-> IRS(n)
        # ISS(n) <-> IRS(w)
        # ISS(n) <-> IRS(n)

        if frametype == FR_TYPE.ARQ_DC_OPEN_W.value and not self.low_bandwidth_mode:
            # ISS(w) <-> IRS(w)
            constellation = "ISS(w) <-> IRS(w)"
            self.received_LOW_BANDWIDTH_MODE = False
            self.mode_list = self.mode_list_high_bw
            self.time_list = self.time_list_high_bw
            self.snr_list = self.snr_list_high_bw
        elif frametype == FR_TYPE.ARQ_DC_OPEN_W.value:
            # ISS(w) <-> IRS(n)
            constellation = "ISS(w) <-> IRS(n)"
            self.received_LOW_BANDWIDTH_MODE = False
            self.mode_list = self.mode_list_low_bw
            self.time_list = self.time_list_low_bw
            self.snr_list = self.snr_list_low_bw
        elif frametype == FR_TYPE.ARQ_DC_OPEN_N.value and not self.low_bandwidth_mode:
            # ISS(n) <-> IRS(w)
            constellation = "ISS(n) <-> IRS(w)"
            self.received_LOW_BANDWIDTH_MODE = True
            self.mode_list = self.mode_list_low_bw
            self.time_list = self.time_list_low_bw
            self.snr_list = self.snr_list_low_bw
        elif frametype == FR_TYPE.ARQ_DC_OPEN_N.value:
            # ISS(n) <-> IRS(n)
            constellation = "ISS(n) <-> IRS(n)"
            self.received_LOW_BANDWIDTH_MODE = True
            self.mode_list = self.mode_list_low_bw
            self.time_list = self.time_list_low_bw
            self.snr_list = self.snr_list_low_bw
        else:
            constellation = "not matched"
            self.received_LOW_BANDWIDTH_MODE = True
            self.mode_list = self.mode_list_low_bw
            self.time_list = self.time_list_low_bw
            self.snr_list = self.snr_list_low_bw

        # get mode which fits to given SNR
        # initially set speed_level 0 in case of bad SNR and no matching mode
        self.speed_level = 0

        # calculate initial speed level in correlation to latest known SNR
        for i in range(len(self.mode_list)):
            if snr >= self.snr_list[i]:
                self.speed_level = i

        # check if speed level fits to busy condition
        if not self.check_if_mode_fits_to_busy_slot():
            self.speed_level = 0

        # Update modes we are listening to
        self.set_listening_modes(True, True, self.mode_list[self.speed_level])
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

        self.session_id = data_in[13:14]

        # check again if callsign ssid override
        _, self.mycallsign = helpers.check_callsign(self.mycallsign, data_in[1:4], self.ssid_list)

        self.log.info(
            "[Modem] ARQ | DATA | RX | ["
            + str(self.mycallsign, "UTF-8")
            + "]>> <<["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            channel_constellation=constellation,
        )

        # Reset data_channel/burst timestamps
        # TIMING TEST
        self.data_channel_last_received = int(time.time())
        self.burst_last_received = int(time.time() + 10)  # we might need some more time so lets increase this

        # Set ARQ State AFTER resetting timeouts
        # this avoids timeouts starting too early
        self.states.set("is_arq_state", True)
        self.states.set("is_modem_busy", True)

        self.reset_statistics()

        # Select the frame type based on the current Modem mode
        if self.low_bandwidth_mode or self.received_LOW_BANDWIDTH_MODE:
            frametype = bytes([FR_TYPE.ARQ_DC_OPEN_ACK_N.value])
            self.log.debug("[Modem] Responding with low bandwidth mode")
        else:
            frametype = bytes([FR_TYPE.ARQ_DC_OPEN_ACK_W.value])
            self.log.debug("[Modem] Responding with high bandwidth mode")


        connection_ack_frame = self.frame_factory.build_arq_connect_ack(
            session_id=self.session_id,
            speed_level=self.speed_level,
            arq_protocol_version=self.arq_protocol_version
        )

        self.enqueue_frame_for_tx([connection_ack_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1, repeat_delay=0)

        self.event_manager.send_custom_event(
            freedata="modem-message",
            arq="transmission",
            status="opened",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            irs=helpers.bool_to_string(self.is_IRS)
        )

        self.log.info(
            "[Modem] ARQ | DATA | RX | ["
            + str(self.mycallsign, "UTF-8")
            + "]>>|<<["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            bandwidth="wide",
            snr=snr,
        )

        # set start of transmission for our statistics
        self.rx_start_of_transmission = time.time()

        # TIMING TEST
        # Reset data_channel/burst timestamps once again for avoiding running into timeout
        # and therefore sending a NACK
        self.data_channel_last_received = int(time.time())
        self.burst_last_received = int(time.time() + 10)  # we might need some more time so lets increase this

    def calculate_transfer_rate_rx(
            self, rx_start_of_transmission: float, receivedbytes: int, snr
    ) -> list:
        """
        Calculate transfer rate for received data
        Args:
          rx_start_of_transmission:float:
          receivedbytes:int:

        Returns: List of:
            bits_per_second: float,
            bytes_per_minute: float,
            transmission_percent: float
        """
        try:
            if self.states.arq_total_bytes == 0:
                self.states.set("arq_total_bytes", 1)
            arq_transmission_percent = min(
                int(
                    (
                            receivedbytes
                            * self.arq_compression_factor
                            / self.states.arq_total_bytes
                    )
                    * 100
                ),
                100,
            )

            transmissiontime = time.time() - self.rx_start_of_transmission

            if receivedbytes > 0:
                arq_bits_per_second = int((receivedbytes * 8) / transmissiontime)
                bytes_per_minute = int(
                    receivedbytes / (transmissiontime / 60)
                )
                arq_seconds_until_finish = int(((self.states.arq_total_bytes - receivedbytes) / (
                        bytes_per_minute * self.arq_compression_factor)) * 60) - 20  # offset because of frame ack/nack

                speed_chart = {"snr": snr, "bpm": bytes_per_minute, "timestamp": int(time.time())}
                # check if data already in list
                if speed_chart not in self.states.arq_speed_list:
                    self.states.arq_speed_list.append(speed_chart)
            else:
                arq_bits_per_second = 0
                bytes_per_minute = 0
                arq_seconds_until_finish = 0
        except Exception as err:
            self.log.error(f"[Modem] calculate_transfer_rate_rx: Exception: {err}")
            arq_transmission_percent = 0.0
            arq_bits_per_second = 0
            bytes_per_minute = 0

        self.states.set("arq_bits_per_second", arq_bits_per_second)
        self.states.set("bytes_per_minute", bytes_per_minute)
        self.states.set("arq_transmission_percent", arq_transmission_percent)
        self.states.set("arq_compression_factor", self.arq_compression_factor)

        return [
            arq_bits_per_second,
            bytes_per_minute,
            arq_transmission_percent,
        ]

    def send_burst_nack_frame(self, snr: bytes) -> None:
        """Build and send NACK frame for received DATA frame"""

        # nack_frame = bytearray(self.length_sig1_frame)
        # nack_frame[:1] = bytes([FR_TYPE.FR_NACK.value])
        # nack_frame[1:2] = self.session_id
        # nack_frame[2:3] = helpers.snr_to_bytes(snr)
        # nack_frame[3:4] = bytes([int(self.speed_level)])
        # nack_frame[4:8] = len(self.arq_rx_frame_buffer).to_bytes(4, byteorder="big")


        nack_frame = self.frame_factory.build_arq_frame_nack(session_id=self.session_id,
                                                           snr=snr,
                                                           speed_level=self.speed_level,
                                                           len_arq_rx_frame_buffer=len(self.arq_rx_frame_buffer)
                                                           )
        # TRANSMIT NACK FRAME FOR BURST
        # TODO Do we have to send ident frame?
        # self.enqueue_frame_for_tx([ack_frame, self.send_ident_frame(False)], c2_mode=FREEDV_MODE.sig1.value, copies=3, repeat_delay=0)

        # wait if  we have a channel busy condition
        if self.states.channel_busy:
            self.channel_busy_handler()

        self.enqueue_frame_for_tx([nack_frame], c2_mode=FREEDV_MODE.sig1.value, copies=3, repeat_delay=0)
        # reset burst timeout in case we had to wait too long
        self.burst_last_received = time.time()


    def send_burst_nack_frame_watchdog(self, tx_n_frames_per_burst) -> None:
        """Build and send NACK frame for watchdog timeout"""

        # increment nack counter for transmission stats
        self.frame_nack_counter += 1

        # we need to clear our rx burst buffer
        self.arq_rx_burst_buffer = []

        # Create and send ACK frame
        self.log.info("[Modem] ARQ | RX | SENDING NACK")
        # nack_frame = bytearray(self.length_sig1_frame)
        # nack_frame[:1] = bytes([FR_TYPE.BURST_NACK.value])
        # nack_frame[1:2] = self.session_id
        # nack_frame[2:3] = helpers.snr_to_bytes(0)
        # nack_frame[3:4] = bytes([int(self.speed_level)])
        # nack_frame[4:5] = bytes([int(tx_n_frames_per_burst)])
        # nack_frame[5:9] = len(self.arq_rx_frame_buffer).to_bytes(4, byteorder="big")

        nack_frame = self.frame_factory.build_arq_burst_nack(session_id=self.session_id,
                                                             snr=0,
                                                             speed_level=self.speed_level,
                                                             len_arq_rx_frame_buffer=len(self.arq_rx_frame_buffer),
                                                             n_frames_per_burst=bytes([int(tx_n_frames_per_burst)])
                                                           )

        # wait if  we have a channel busy condition
        if self.states.channel_busy:
            self.channel_busy_handler()

        # TRANSMIT NACK FRAME FOR BURST
        self.enqueue_frame_for_tx([nack_frame], c2_mode=FREEDV_MODE.sig1.value, copies=1, repeat_delay=0)

        # reset frame counter for not increasing speed level
        self.frame_received_counter = 0

    def arq_data_received(
            self, deconstructed_frame: list, bytes_per_frame: int, snr: float, freedv
    ) -> None:
        """
        Args:
          data_in:bytes:
          bytes_per_frame:int:
          snr:float:
          freedv:

        Returns:
        """
        # We've arrived here from process_data which already checked that the frame
        # is intended for this station.
        data_in = deconstructed_frame["data"]

        # only process data if we are in ARQ and BUSY state else return to quit
        if not self.states.is_arq_state and not self.states.is_modem_busy:
            self.log.warning("[Modem] wrong modem state - dropping data", is_arq_state=self.states.is_arq_state,
                             modem_state=self.states.is_modem_busy)
            return

        self.arq_file_transfer = True

        self.states.set("is_modem_busy", True)
        self.states.set("is_arq_state", True)

        # Update data_channel timestamp
        self.data_channel_last_received = int(time.time())
        self.burst_last_received = int(time.time())

        # Extract some important data from the frame
        # Get sequence number of burst frame
        self.rx_n_frame_of_burst = int.from_bytes(bytes(data_in[:1]), "big") - 10
        # Get number of bursts from received frame
        self.rx_n_frames_per_burst = int.from_bytes(bytes(data_in[1:2]), "big")

        # The RX burst buffer needs to have a fixed length filled with "None".
        # We need this later for counting the "Nones" to detect missing data.
        # Check if burst buffer has expected length else create it
        if len(self.arq_rx_burst_buffer) != self.rx_n_frames_per_burst:
            self.arq_rx_burst_buffer = [None] * self.rx_n_frames_per_burst

        # Append data to rx burst buffer
        self.arq_rx_burst_buffer[self.rx_n_frame_of_burst] = data_in[self.arq_burst_header_size:]  # type: ignore

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

        # Check if we received all frames in the burst by checking if burst buffer has no more "Nones"
        # This is the ideal case because we received all data
        if None not in self.arq_rx_burst_buffer:
            # then iterate through burst buffer and stick the burst together
            # the temp burst buffer is needed for checking, if we already received data
            temp_burst_buffer = b""
            for value in self.arq_rx_burst_buffer:
                # self.arq_rx_frame_buffer += self.arq_rx_burst_buffer[i]
                temp_burst_buffer += bytes(value)  # type: ignore

            # free up burst buffer
            self.arq_rx_burst_buffer = []

            # TODO Needs to be removed as soon as mode error is fixed
            # catch possible modem error which leads into false byteorder
            # modem possibly decodes too late - data then is pushed to buffer
            # which leads into wrong byteorder
            # Lets put this in try/except so we are not crashing modem as its highly experimental
            # This might only work for datac1 and datac3
            try:
                # area_of_interest = (modem.get_bytes_per_frame(self.mode_list[speed_level] - 1) -3) * 2
                if self.arq_rx_frame_buffer.endswith(temp_burst_buffer[:246]) and len(temp_burst_buffer) >= 246:
                    self.log.warning(
                        "[Modem] ARQ | RX | wrong byteorder received - dropping data"
                    )
                    # we need to run a return here, so we are not sending an ACK
                    # return
            except Exception as e:
                self.log.warning(
                    "[Modem] ARQ | RX | wrong byteorder check failed", e=e
                )

            self.log.debug("[Modem] temp_burst_buffer", buffer=temp_burst_buffer)
            self.log.debug("[Modem] self.arq_rx_frame_buffer", buffer=self.arq_rx_frame_buffer)

            # if frame buffer ends not with the current frame, we are going to append new data
            # if data already exists, we received the frame correctly,
            # but the ACK frame didn't receive its destination (ISS)
            if self.arq_rx_frame_buffer.endswith(temp_burst_buffer):
                self.log.info(
                    "[Modem] ARQ | RX | Frame already received - sending ACK again"
                )

            else:
                # Here we are going to search for our data in the last received bytes.
                # This reduces the chance we will lose the entire frame in the case of signalling frame loss

                # self.arq_rx_frame_buffer --> existing data
                # temp_burst_buffer --> new data
                # search_area --> area where we want to search

                search_area = self.arq_burst_last_payload * self.rx_n_frames_per_burst

                search_position = len(self.arq_rx_frame_buffer) - search_area
                # if search position < 0, then search position = 0
                search_position = max(0, search_position)

                # find position of data. returns -1 if nothing found in area else >= 0
                # we are beginning from the end, so if data exists twice or more,
                # only the last one should be replaced
                # we are going to only check position against minimum data frame payload
                # use case: receive data, which already contains received data
                # while the payload of data received before is shorter than actual payload
                get_position = self.arq_rx_frame_buffer[search_position:].rfind(
                    temp_burst_buffer[:self.arq_burst_minimum_payload]
                )
                # if we find data, replace it at this position with the new data and strip it
                if get_position >= 0:
                    self.arq_rx_frame_buffer = self.arq_rx_frame_buffer[
                                               : search_position + get_position
                                               ]
                    self.log.warning(
                        "[Modem] ARQ | RX | replacing existing buffer data",
                        area=search_area,
                        pos=get_position,
                    )
                else:
                    self.log.debug("[Modem] ARQ | RX | appending data to buffer")

                self.arq_rx_frame_buffer += temp_burst_buffer

                self.arq_burst_last_payload = len(temp_burst_buffer)

            # Check if we didn't receive a BOF and EOF yet to avoid sending
            # ack frames if we already received all data
            if (
                    not self.rx_frame_bof_received
                    and not self.rx_frame_eof_received
                    and data_in.find(self.data_frame_eof) < 0
            ):
                self.arq_calculate_speed_level(snr)

                # TIMING TEST
                # self.data_channel_last_received = int(time.time()) + 6 + 6
                # self.burst_last_received = int(time.time()) + 6 + 6
                self.data_channel_last_received = int(time.time())
                self.burst_last_received = int(time.time())

                # Create and send ACK frame
                self.log.info("[Modem] ARQ | RX | SENDING ACK", finished=self.states.arq_seconds_until_finish,
                              bytesperminute=self.states.arq_bytes_per_minute)

                self.send_burst_ack_frame(snr)

                # Reset n retries per burst counter
                self.n_retries_per_burst = 0

                # calculate statistics
                self.calculate_transfer_rate_rx(
                    self.rx_start_of_transmission, len(self.arq_rx_frame_buffer), snr
                )

                # send a network message with information
                self.event_manager.send_custom_event(
                    freedata="modem-message",
                    arq="transmission",
                    status="receiving",
                    uuid=self.transmission_uuid,
                    percent=self.states.arq_transmission_percent,
                    bytesperminute=self.states.arq_bytes_per_minute,
                    compression=self.arq_compression_factor,
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                    finished=self.states.arq_seconds_until_finish,
                    irs=helpers.bool_to_string(self.is_IRS)
                )
        else:
            self.log.warning(
                "[Modem] data_handler: missing data in burst buffer...",
                frame=self.rx_n_frame_of_burst + 1,
                frames=self.rx_n_frames_per_burst
            )

        # We have a BOF and EOF flag in our data. If we received both we received our frame.
        # In case of loosing data, but we received already a BOF and EOF we need to make sure, we
        # received the complete last burst by checking it for Nones
        bof_position = self.arq_rx_frame_buffer.find(self.data_frame_bof)
        eof_position = self.arq_rx_frame_buffer.find(self.data_frame_eof)

        # get total bytes per transmission information as soon we received a frame with a BOF

        if bof_position >= 0:
            self.arq_extract_statistics_from_data_frame(bof_position, eof_position, snr)
        if (
                bof_position >= 0
                and eof_position > 0
                and None not in self.arq_rx_burst_buffer
        ):
            self.log.debug(
                "[Modem] arq_data_received:",
                bof_position=bof_position,
                eof_position=eof_position,
            )
            self.rx_frame_bof_received = True
            self.rx_frame_eof_received = True

            # Extract raw data from buffer
            payload = self.arq_rx_frame_buffer[
                      bof_position + len(self.data_frame_bof): eof_position
                      ]
            # Get the data frame crc
            data_frame_crc = payload[:4]  # 0:4 = 4 bytes
            # Get the data frame length
            frame_length = int.from_bytes(payload[4:8], "big")  # 4:8 = 4 bytes
            self.states.set("arq_total_bytes", frame_length)
            # 8:9 = compression factor

            data_frame = payload[9:]
            data_frame_crc_received = helpers.get_crc_32(data_frame)

            # check if hmac signing enabled
            if self.enable_hmac:
                self.log.info(
                    "[Modem] [HMAC] Enabled",
                )
                # now check if we have valid hmac signature - returns salt or bool
                salt_found = helpers.search_hmac_salt(self.dxcallsign, self.mycallsign, data_frame_crc, data_frame,
                                                      token_iters=100)

                if salt_found:
                    # hmac digest received
                    self.arq_process_received_data_frame(data_frame, snr, signed=True)

                else:

                    # hmac signature wrong
                    self.arq_process_received_data_frame(data_frame, snr, signed=False)
            elif data_frame_crc == data_frame_crc_received:
                self.log.warning(
                    "[Modem] [HMAC] Disabled, using CRC",
                )
                self.arq_process_received_data_frame(data_frame, snr, signed=False)
            else:
                self.event_manager.send_custom_event(
                    freedata="modem-message",
                    arq="transmission",
                    status="failed",
                    uuid=self.transmission_uuid,
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                    irs=helpers.bool_to_string(self.is_IRS)
                )

                duration = time.time() - self.rx_start_of_transmission
                self.log.warning(
                    "[Modem] ARQ | RX | DATA FRAME NOT SUCCESSFULLY RECEIVED!",
                    e="wrong crc",
                    expected=data_frame_crc.hex(),
                    received=data_frame_crc_received.hex(),
                    nacks=self.frame_nack_counter,
                    duration=duration,
                    bytesperminute=self.states.arq_bytes_per_minute,
                    compression=self.arq_compression_factor,
                    data=data_frame,

                )
                if self.enable_stats:
                    self.stats.push(frame_nack_counter=self.frame_nack_counter, status="wrong_crc", duration=duration)

                self.log.info("[Modem] ARQ | RX | Sending NACK", finished=self.states.arq_seconds_until_finish,
                              bytesperminute=self.states.arq_bytes_per_minute)
                self.send_burst_nack_frame(snr)

            # Update arq_session timestamp
            self.arq_session_last_received = int(time.time())

            # Finally cleanup our buffers and states,
            self.arq_cleanup()

    def arq_extract_statistics_from_data_frame(self, bof_position, eof_position, snr):
        payload = self.arq_rx_frame_buffer[
                  bof_position + len(self.data_frame_bof): eof_position
                  ]
        frame_length = int.from_bytes(payload[4:8], "big")  # 4:8 4bytes
        self.states.set("arq_total_bytes", frame_length)
        compression_factor = int.from_bytes(payload[8:9], "big")  # 4:8 4bytes
        # limit to max value of 255
        compression_factor = np.clip(compression_factor, 0, 255)
        self.arq_compression_factor = compression_factor / 10
        self.calculate_transfer_rate_rx(
            self.rx_start_of_transmission, len(self.arq_rx_frame_buffer), snr
        )
    def send_burst_ack_frame(self, snr) -> None:
        """Build and send ACK frame for burst DATA frame"""

        # ack_frame = bytearray(self.length_sig1_frame)
        # ack_frame[:1] = bytes([FR_TYPE.BURST_ACK.value])
        # ack_frame[1:2] = self.session_id
        # ack_frame[2:3] = helpers.snr_to_bytes(snr)
        # ack_frame[3:4] = bytes([int(self.speed_level)])
        # ack_frame[4:8] = len(self.arq_rx_frame_buffer).to_bytes(4, byteorder="big")

        ack_frame = self.frame_factory.build_arq_burst_ack(session_id=self.session_id,
                                                           snr=snr,
                                                           speed_level=self.speed_level,
                                                           len_arq_rx_frame_buffer=len(self.arq_rx_frame_buffer)
                                                           )

        # wait if  we have a channel busy condition
        if self.states.channel_busy:
            self.channel_busy_handler()

        # Transmit frame
        self.enqueue_frame_for_tx([ack_frame], c2_mode=FREEDV_MODE.sig1.value)

    def send_data_ack_frame(self, snr) -> None:
        """Build and send ACK frame for received DATA frame"""

        # ack_frame = bytearray(self.length_sig1_frame)
        # ack_frame[:1] = bytes([FR_TYPE.FR_ACK.value])
        # ack_frame[1:2] = self.session_id
        # ack_frame[2:3] = helpers.snr_to_bytes(snr)

        ack_frame = self.frame_factory.build_arq_frame_ack(session_id=self.session_id, snr=snr)
        # wait if  we have a channel busy condition
        if self.states.channel_busy:
            self.channel_busy_handler()

        # Transmit frame
        self.enqueue_frame_for_tx([ack_frame], c2_mode=FREEDV_MODE.sig1.value, copies=3, repeat_delay=0)


    def send_retransmit_request_frame(self) -> None:
        # check where a None is in our burst buffer and do frame+1, because lists start at 0
        # FIXME Check to see if there's a `frame - 1` in the receive portion. Remove both if there is.
        missing_frames = [
            frame + 1
            for frame, element in enumerate(self.arq_rx_burst_buffer)
            if element is None
        ]

        rpt_frame = bytearray(self.length_sig1_frame)
        rpt_frame[:1] = bytes([FR_TYPE.FR_REPEAT.value])
        rpt_frame[1:2] = self.session_id
        rpt_frame[2:2 + len(missing_frames)] = missing_frames

        self.log.info("[Modem] ARQ | RX | Requesting", frames=missing_frames)
        # Transmit frame
        self.enqueue_frame_for_tx([rpt_frame], c2_mode=FREEDV_MODE.sig1.value, copies=1, repeat_delay=0)
