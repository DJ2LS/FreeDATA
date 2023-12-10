import threading
import data_frame_factory
import queue
import arq_session

class ARQSessionIRS(arq_session.ARQSession):

    STATE_CONN_REQ_RECEIVED = 0
    STATE_WAITING_DATA = 1
    STATE_FAILED = 2
    STATE_ENDED = 10

    RETRIES_CONNECT = 3
    RETRIES_TRANSFER = 3

    TIMEOUT_DATA = 6

    def __init__(self, config: dict, tx_frame_queue: queue.Queue, dxcall: str, session_id: int):
        super().__init__(config, tx_frame_queue, dxcall)

        self.id = session_id

        self.state = self.STATE_CONN_REQ_RECEIVED

        self.event_data_received = threading.Event()
        
        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)

        # naming:
        # frame = single frame
        # burst = one or more frames. A burst will be acknowledged with a ACK

        # this is the buffer which holds received data temporarily for each burst
        self.arq_rx_burst_buffer = []
        # this is our buffer, holding data, after we received a full burst
        self.arq_rx_frame_buffer = b""
        # this variable holds the amount/size of data we've received the last time
        self.arq_burst_last_data_size = 0

    def generate_id(self):
        pass

    def log(self, message):
        pass

    def set_state(self, state):
        self.log(f"ARQ Session IRS {self.id} state {self.state}")
        self.state = state

    def set_modem_decode_modes(self, modes):
        pass

    def runner(self):
        isWideband = True
        speed = 1
        version = 1

        ack_frame = self.frame_factory.build_arq_session_connect_ack(isWideband, self.id, speed, version)
        self.transmit_frame(ack_frame)

        self.set_modem_decode_modes(None)
        self.state = self.STATE_WAITING_DATA
        while self.state == self.STATE_WAITING_DATA:
            if not self.event_data_received.wait(self.TIMEOUT_DATA):
                self.log("Timeout waiting for data")
                self.state = self.STATE_FAILED
                return

        self.log("Finished ARQ IRS session")

    def run(self):
        self.thread = threading.Thread(target=self.runner, name=f"ARQ IRS Session {self.id}", daemon=True)
        self.thread.start()


    def on_data_received(self, data_frame):
        if self.state != self.STATE_WAITING_DATA:
            raise RuntimeError(f"ARQ Session: Received data while in state {self.state}, expected {self.STATE_WAITING_DATA}")

        self.rx_data_chain(data_frame)
        self.event_data_received.set()


    def on_transfer_ack_received(self, ack):
        self.event_transfer_ack_received.set()
        self.speed_level = ack['speed_level']

    def on_transfer_nack_received(self, nack):
        self.speed_level = nack['speed_level']

    def on_disconnect_received(self):
        self.abort()

    def abort(self):
        self.state = self.STATE_DISCONNECTED
        self.event_connection_ack_received.set()
        self.event_connection_ack_received.clear()
        self.event_transfer_feedback.set()
        self.event_transfer_feedback.clear()

    def rx_data_chain(self, data_frame):
        """
        Function for processing received frames in correct order
        Args:
            data_frame: {'frame_type': 'BURST_01', 'frame_type_int': 1, 'n_frames_per_burst': 1, 'session_id': 118, 'data': b'Hello world!'}



        Returns:

        """

        # unpack some parameters from frame
        data = data_frame["data"]
        rx_n_frame_of_burst = data_frame["frame_type_int"]
        rx_n_frames_per_burst = data_frame["n_frames_per_burst"]
        session_id = data_frame["session_id"]

        self.init_rx_buffer()
        self.append_data_to_burst_buffer(data)

        # Check if we received all frames in the burst by checking if burst buffer has no more "Nones"
        if None not in self.arq_rx_burst_buffer:
            # Stick burst together in case we received multiple frames per burst
            burst_data = self.stick_burst_together()
            
            # check if we already received the burst in a transmission before
            # use case: ACK packet from IRS to ISS got lost
            if self.arq_rx_frame_buffer.endswith(burst_data):
                self.log.info("[Modem] ARQ | RX | Frame already received - sending ACK again")
            else:
                # add burst to our data buffer
                self.proces_burst(burst_data)
                
                # Check if we didn't receive a BOF and EOF yet to avoid sending
                # ack frames if we already received all data
                if not self.check_if_last_data_received(data):
                    self.acknowledge_burst()
                    return
                    
        else:
            # burst is missing some data...can happen for N > 1 frames per burst in case of packet loss
            self.log.warning("[Modem] data_handler: missing data in burst buffer!",frame=rx_n_frame_of_burst + 1, frames=rx_n_frames_per_burst)
        
            
        # check if we have a BOF ( Begin Of Frame ) or EOF (End Of Frame) flag in our data
        bof_position, eof_position = self.search_for_bof_eof_flag()
        if bof_position >= 0:
            self.arq_extract_statistics_from_data_frame(bof_position, eof_position, snr)

        # now check if we received the entire data by BOF and EOF position
        if self.check_if_entire_data_received(bof_position, eof_position):
            # meanwhile we have our data + header information, we want't to separate them now
            data, checksum, size, compression_factor = self.deconstruct_arq_frame(bof_position, eof_position)
            self.states.set("arq_total_bytes", size)
            
            # do some HMAC and checksum related stuff
            # TODO We need to split the calculate checksums so the entire logics is visible here
            self.calculate_checksums(data, checksum)

            # Finally cleanup our buffers and states,
            self.arq_cleanup()
            
        else:
            print("something bad happened...")
        
        
        
    # --------------------------------------------------------------------    
    # THIS AREA HOLDS RX CHAIN FUNCTIONS IN CHRONOLOGICAL PROCESSING ORDER

    def init_rx_buffer(self, rx_n_frames_per_burst):
        # The RX burst buffer needs to have a fixed length filled with "None".
        # We need this later for counting the "Nones" to detect missing data.
        # Check if burst buffer has expected length else create it
        if len(self.arq_rx_burst_buffer) != rx_n_frames_per_burst:
            self.arq_rx_burst_buffer = [None] * rx_n_frames_per_burst

    def append_data_to_burst_buffer(self, data):
        # Append data to rx burst buffer
        self.arq_rx_burst_buffer[self.rx_n_frame_of_burst] = data_in[self.arq_burst_header_size:]  # type: ignore

    def stick_burst_together(self):
        # then iterate through burst buffer and stick the burst together
        # the temp burst buffer is needed for checking, if we already received data
        burst_data = b""
        for frame in self.arq_rx_burst_buffer:
            burst_data += bytes(frame)  # type: ignore

        # free up burst buffer
        self.arq_rx_burst_buffer = []
        return burst_data
        
    def process_burst(self, burst_data):
        # Here we are going to search for our data in the last received bytes.
        # This reduces the chance we will lose the entire frame in the case of signalling frame loss

        # self.arq_rx_frame_buffer --> existing data
        # temp_burst_buffer --> new data
        # search_area --> area where we want to search

        search_area = self.arq_burst_last_data_size * self.rx_n_frames_per_burst

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
            burst_data[:self.arq_burst_minimum_payload]
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

        # append data to our data store
        self.arq_rx_frame_buffer += burst_data

        # finally update the data size, so we can use it for the next burst
        self.arq_burst_last_data_size = len(burst_data)
        
    def check_if_last_data_received(self, frame):
        # Check if we didn't receive a BOF and EOF yet to avoid sending
        # ack frames if we already received all data
        return bool(
            self.rx_frame_bof_received
            or self.rx_frame_eof_received
            or frame.find(self.data_frame_eof) >= 0
        )
    
    def acknowledge_burst(self):
        # TODO WIP
        self.arq_calculate_speed_level(snr)
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
    
    def search_for_bof_eof_flag(self):
        # We have a BOF and EOF flag in our data. If we received both we received our frame.
        # In case of loosing data, but we received already a BOF and EOF we need to make sure, we
        # received the complete last burst by checking it for Nones
        bof_position = self.arq_rx_frame_buffer.find(self.data_frame_bof)
        eof_position = self.arq_rx_frame_buffer.find(self.data_frame_eof)
        return bof_position, eof_position
    
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
    
    def check_if_entire_data_received(self, bof_position, eof_position):
        return (
            bof_position >= 0
            and eof_position > 0
            and None not in self.arq_rx_burst_buffer
        )
    
    def deconstruct_arq_frame(self, bof_position, eof_position):
        # Extract raw data from buffer
        payload = self.arq_rx_frame_buffer[bof_position + len(self.data_frame_bof): eof_position]
        # Get the data frame crc
        checksum = payload[:4]  # 0:4 = 4 bytes
        # Get the data frame length
        size = int.from_bytes(payload[4:8], "big")  # 4:8 = 4 bytes
        compression_factor = int.from_bytes(payload[8:9], "big")  # 8:9 = 1 byte
        data = payload[9:] # this is our data
        
        return data, checksum, size, compression_factor


    def calculate_checksums(self, data, checksum_expected):
        # TODO WIP, we need to fix this
        # lets do a crc calculation for our recevied data
        checksum_received = helpers.get_crc_32(data)


        # check if hmac signing enabled
        if self.enable_hmac:
            self.log.info(
                "[Modem] [HMAC] Enabled",
            )
            if salt_found := helpers.search_hmac_salt(
                self.dxcallsign,
                self.mycallsign,
                checksum_expected,
                data,
                token_iters=100,
            ):
                # hmac digest received
                self.arq_process_received_data_frame(data, snr, signed=True)

            else:
                # hmac signature wrong
                self.arq_process_received_data_frame(data, snr, signed=False)
        elif checksum_expected == checksum_received:
            self.log.warning(
                "[Modem] [HMAC] Disabled, using CRC",
            )
            self.arq_process_received_data_frame(data, snr, signed=False)
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
                expected=checksum_expected.hex(),
                received=checksum_received.hex(),
                nacks=self.frame_nack_counter,
                duration=duration,
                bytesperminute=self.states.arq_bytes_per_minute,
                compression=self.arq_compression_factor,
                data=data,

            )
            if self.enable_stats:
                self.stats.push(frame_nack_counter=self.frame_nack_counter, status="wrong_crc", duration=duration)

            self.log.info("[Modem] ARQ | RX | Sending NACK", finished=self.states.arq_seconds_until_finish,
                          bytesperminute=self.states.arq_bytes_per_minute)
            self.send_burst_nack_frame(snr)

    def arq_process_received_data_frame(self):
        # TODO We need to port arq_process_received_data_frame function from deprecated_protocol_arq_session_irs to this place
        #  A smiley for the brave ones reading until this area
        #  :-) :-) :-) :-)
        pass