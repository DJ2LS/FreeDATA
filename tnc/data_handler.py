#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 27 20:43:40 2020

@author: DJ2LS
"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel

import base64
import queue
import sys
import threading
import time
import uuid
import zlib
from random import randrange

import codec2
import helpers
import modem
import numpy as np
import sock
import static
import structlog
import ujson as json

TESTMODE = False

DATA_QUEUE_TRANSMIT = queue.Queue()
DATA_QUEUE_RECEIVED = queue.Queue()


class DATA:
    """ Terminal Node Controller for FreeDATA """
    log = structlog.get_logger("DATA")

    def __init__(self):
        self.mycallsign = static.MYCALLSIGN  # initial call sign. Will be overwritten later

        self.data_queue_transmit = DATA_QUEUE_TRANSMIT
        self.data_queue_received = DATA_QUEUE_RECEIVED

        # ------- ARQ SESSION
        self.arq_file_transfer = False
        self.IS_ARQ_SESSION_MASTER = False
        self.arq_session_last_received = 0
        self.arq_session_timeout = 30
        self.session_connect_max_retries = 3

        self.transmission_uuid = ""

        self.received_mycall_crc = b""  # Received my callsign crc if we received a crc for another ssid

        self.data_channel_last_received = 0.0  # time of last "live sign" of a frame
        self.burst_ack_snr = 0  # SNR from received ack frames
        self.burst_ack = False  # if we received an acknowledge frame for a burst
        self.data_frame_ack_received = False  # if we received an acknowledge frame for a data frame
        self.rpt_request_received = False  # if we received a request for repeater frames
        self.rpt_request_buffer = []  # requested frames, saved in a list
        self.rx_start_of_transmission = 0  # time of transmission start

        self.data_frame_bof = b"BOF"  # 2 bytes for the BOF End of File indicator in a data frame
        self.data_frame_eof = b"EOF"  # 2 bytes for the EOF End of File indicator in a data frame

        self.rx_n_max_retries_per_burst = 50
        self.n_retries_per_burst = 0

        self.received_LOW_BANDWIDTH_MODE = False  # indicator if we recevied a low bandwidth mode channel opener

        self.data_channel_max_retries = 5
        self.datachannel_timeout = False

        self.mode_list_low_bw = [14, 12]
        self.time_list_low_bw = [3, 7]

        self.mode_list_high_bw = [14, 12, 10]  # mode list of available modes,each mode will be used 2 times per level
        self.time_list_high_bw = [3, 7, 8, 30]  # list for time to wait for corresponding mode in seconds

        # mode list for selecting between low bandwidth ( 500Hz ) and normal modes with higher bandwidth
        if static.LOW_BANDWIDTH_MODE:
            self.mode_list = self.mode_list_low_bw  # mode list of available modes, each mode will be used 2times per speed level

            self.time_list = self.time_list_low_bw  # list for time to wait for corresponding mode in seconds

        else:
            self.mode_list = self.mode_list_high_bw  # mode list of available modes, each mode will be used 2times per speed level
            self.time_list = self.time_list_high_bw  # list for time to wait for corresponding mode in seconds

        self.speed_level = len(self.mode_list) - 1  # speed level for selecting mode
        static.ARQ_SPEED_LEVEL = self.speed_level

        self.is_IRS = False
        self.burst_nack = False
        self.burst_nack_counter = 0
        self.frame_received_counter = 0

        self.rx_frame_bof_received = False
        self.rx_frame_eof_received = False

        self.transmission_timeout = 360  # transmission timeout in seconds

        worker_thread_transmit = threading.Thread(target=self.worker_transmit, name="worker thread transmit",
                                                  daemon=True)
        worker_thread_transmit.start()

        worker_thread_receive = threading.Thread(target=self.worker_receive, name="worker thread receive",
                                                    daemon=True)
        worker_thread_receive.start()

        # START THE THREAD FOR THE TIMEOUT WATCHDOG
        watchdog_thread = threading.Thread(target=self.watchdog, name="watchdog", daemon=True)
        watchdog_thread.start()

        arq_session_thread = threading.Thread(target=self.heartbeat, name="watchdog", daemon=True)
        arq_session_thread.start()

        self.beacon_interval = 0
        self.beacon_thread = threading.Thread(target=self.run_beacon, name="watchdog", daemon=True)
        self.beacon_thread.start()

    def worker_transmit(self):
        """ """
        while True:
            data = self.data_queue_transmit.get()

            # [0] == Command
            if data[0] == "CQ":
                self.transmit_cq()

            elif data[0] == "STOP":
                self.stop_transmission()

            elif data[0] == "PING":
                # [1] dxcallsign
                self.transmit_ping(data[1])

            elif data[0] == "BEACON":
                # [1] INTERVAL int
                # [2] STATE bool
                if data[2]:
                    self.beacon_interval = data[1]
                    static.BEACON_STATE = True
                else:
                    static.BEACON_STATE = False

            elif data[0] == "ARQ_RAW":
                # [1] DATA_OUT bytes
                # [2] MODE int
                # [3] N_FRAMES_PER_BURST int
                # [4] self.transmission_uuid str
                # [5] mycallsign with ssid
                self.open_dc_and_transmit(data[1], data[2], data[3], data[4], data[5])

            elif data[0] == "CONNECT":
                # [1] DX CALLSIGN
                self.arq_session_handler(data[1])

            elif data[0] == "DISCONNECT":
                # [1] DX CALLSIGN
                self.close_session()

            elif data[0] == "SEND_TEST_FRAME":
                # [1] DX CALLSIGN
                self.send_test_frame()
            else:
                self.log.error("[TNC] worker_transmit: received invalid command:", data=data)

    def worker_receive(self):
        """ """
        while True:
            data = self.data_queue_received.get()
            # [0] bytes
            # [1] freedv instance
            # [2] bytes_per_frame
            self.process_data(bytes_out=data[0], freedv=data[1], bytes_per_frame=data[2])

    def process_data(self, bytes_out, freedv, bytes_per_frame: int):
        """

        Args:
          bytes_out:
          freedv:
          bytes_per_frame:

        Returns:

        """
        self.log.debug("[TNC] process_data:", n_retries_per_burst=self.n_retries_per_burst)

        # forward data only if broadcast, or we are the receiver
        # bytes_out[1:4] == callsign check for signalling frames,
        # bytes_out[2:5] == transmission
        # we could also create an own function, which returns True.
        frametype = int.from_bytes(bytes(bytes_out[:1]), "big")
        _valid1, _ = helpers.check_callsign(self.mycallsign, bytes(bytes_out[1:4]))
        _valid2, _ = helpers.check_callsign(self.mycallsign, bytes(bytes_out[2:5]))
        if _valid1 or _valid2 or frametype in [200, 201, 210, 250]:

            # CHECK IF FRAMETYPE IS BETWEEN 10 and 50 ------------------------
            frame = frametype - 10
            n_frames_per_burst = int.from_bytes(bytes(bytes_out[1:2]), "big")

            if 50 >= frametype >= 10:
                # get snr of received data
                # snr = self.calculate_snr(freedv)
                # we need to find a way of fixing this because after moving to class system this doesn't work anymore
                snr = static.SNR
                self.log.debug("[TNC] RX SNR", snr=snr)
                # send payload data to arq checker without CRC16
                self.arq_data_received(bytes(bytes_out[:-2]), bytes_per_frame, snr, freedv)

                # if we received the last frame of a burst or the last remaining rpt frame, do a modem unsync
                # if static.RX_BURST_BUFFER.count(None) <= 1 or (frame+1) == n_frames_per_burst:
                #    self.log.debug(f"[TNC] LAST FRAME OF BURST --> UNSYNC {frame+1}/{n_frames_per_burst}")
                #    self.c_lib.freedv_set_sync(freedv, 0)

            # BURST ACK
            elif frametype == 60:
                self.log.debug("[TNC] ACK RECEIVED....")
                self.burst_ack_received(bytes_out[:-2])

            # FRAME ACK
            elif frametype == 61:
                self.log.debug("[TNC] FRAME ACK RECEIVED....")
                self.frame_ack_received()

            # FRAME RPT
            elif frametype == 62:
                self.log.debug("[TNC] REPEAT REQUEST RECEIVED....")
                self.burst_rpt_received(bytes_out[:-2])

            # FRAME NACK
            elif frametype == 63:
                self.log.debug("[TNC] FRAME NACK RECEIVED....")
                self.frame_nack_received(bytes_out[:-2])

            # BURST NACK
            elif frametype == 64:
                self.log.debug("[TNC] BURST NACK RECEIVED....")
                self.burst_nack_received(bytes_out[:-2])

            # CQ FRAME
            elif frametype == 200:
                self.log.debug("[TNC] CQ RECEIVED....")
                self.received_cq(bytes_out[:-2])

            # QRV FRAME
            elif frametype == 201:
                self.log.debug("[TNC] QRV RECEIVED....")
                self.received_qrv(bytes_out[:-2])

            # PING FRAME
            elif frametype == 210:
                self.log.debug("[TNC] PING RECEIVED....")
                self.received_ping(bytes_out[:-2])

            # PING ACK
            elif frametype == 211:
                self.log.debug("[TNC] PING ACK RECEIVED....")
                self.received_ping_ack(bytes_out[:-2])

            # SESSION OPENER
            elif frametype == 221:
                self.log.debug("[TNC] OPEN SESSION RECEIVED....")
                self.received_session_opener(bytes_out[:-2])

            # SESSION HEARTBEAT
            elif frametype == 222:
                self.log.debug("[TNC] SESSION HEARTBEAT RECEIVED....")
                self.received_session_heartbeat(bytes_out[:-2])

            # SESSION CLOSE
            elif frametype == 223:
                self.log.debug("[TNC] CLOSE ARQ SESSION RECEIVED....")
                self.received_session_close(bytes_out[:-2])

            # ARQ FILE TRANSFER RECEIVED!
            elif frametype in [225, 227]:
                self.log.debug("[TNC] ARQ arq_received_data_channel_opener")
                self.arq_received_data_channel_opener(bytes_out[:-2])

            # ARQ CHANNEL IS OPENED
            elif frametype in [226, 228]:
                self.log.debug("[TNC] ARQ arq_received_channel_is_open")
                self.arq_received_channel_is_open(bytes_out[:-2])

            # ARQ MANUAL MODE TRANSMISSION
            elif 230 <= frametype <= 240:
                self.log.debug("[TNC] ARQ manual mode")
                self.arq_received_data_channel_opener(bytes_out[:-2])

            # ARQ STOP TRANSMISSION
            elif frametype == 249:
                self.log.debug("[TNC] ARQ received stop transmission")
                self.received_stop_transmission()

            # this is outdated and we may remove it
            elif frametype == 250:
                self.log.debug("[TNC] BEACON RECEIVED")
                self.received_beacon(bytes_out[:-2])

            # TESTFRAMES
            elif frametype == 255:
                self.log.debug("[TNC] TESTFRAME RECEIVED", frame=bytes_out[:])

            # Unknown frame type
            else:
                self.log.warning("[TNC] ARQ - other frame type", frametype=frametype)

        else:
            # for debugging purposes to receive all data
            self.log.debug("[TNC] Unknown frame received", frame=bytes_out[:-2])

    def enqueue_frame_for_tx(self, frame_to_tx: bytearray, c2_mode=14, copies=1, repeat_delay=0):
        """
        Send (transmit) supplied frame to TNC

        :param frame_to_tx: Frame data to send
        :type frame_to_tx: bytearray
        :param c2_mode: Codec2 mode to use, defaults to "datac0" (14)
        :type c2_mode: str, optional
        :param copies: Number of frame copies to send, defaults to 1
        :type copies: int, optional
        :param repeat_delay: Delay time before sending repeat frame, defaults to 0
        :type repeat_delay: int, optional
        """
        self.log.debug("[TNC] enqueue_frame_for_tx", c2_mode=c2_mode)
        if isinstance(c2_mode, str):
            _mode = codec2.freedv_get_mode_value_by_name(c2_mode.lower())
        else:
            _mode = int(c2_mode)
        static.TRANSMITTING = True
        modem.MODEM_TRANSMIT_QUEUE.put([_mode, copies, repeat_delay, [frame_to_tx]])
        # Wait while transmitting
        while static.TRANSMITTING:
            time.sleep(0.01)

    def send_burst_ack_frame(self, snr):
        """ Build and send ACK frame for burst DATA frame """
        ack_frame = bytearray(14)
        ack_frame[:1] = bytes([60])
        ack_frame[1:4] = static.DXCALLSIGN_CRC
        ack_frame[4:7] = static.MYCALLSIGN_CRC
        ack_frame[7:8] = bytes([int(snr)])
        ack_frame[8:9] = bytes([int(self.speed_level)])

        # Transmit frame
        self.enqueue_frame_for_tx(ack_frame)

    def send_data_ack_frame(self, snr):
        """ Build and send ACK frame for received DATA frame """
        ack_frame = bytearray(14)
        ack_frame[:1] = bytes([61])
        ack_frame[1:4] = static.DXCALLSIGN_CRC
        ack_frame[4:7] = static.MYCALLSIGN_CRC
        ack_frame[7:8] = bytes([int(snr)])
        ack_frame[8:9] = bytes([int(self.speed_level)])

        # Transmit frame
        self.enqueue_frame_for_tx(ack_frame, copies=3, repeat_delay=100)

    def send_retransmit_request_frame(self, freedv):
        # check where a None is in our burst buffer and do frame+1, because lists start at 0
        missing_frames = [frame + 1 for frame, element in enumerate(static.RX_BURST_BUFFER) if element is None]

        # set n frames per burst to modem
        # this is an idea, so it's not getting lost....
        # we need to work on this
        codec2.api.freedv_set_frames_per_burst(freedv, len(missing_frames))

        # TODO: Trim `missing_frames` bytesarray to [7:13] (6) frames, if it's larger.

        # then create a repeat frame
        rpt_frame = bytearray(14)
        rpt_frame[:1] = bytes([62])
        rpt_frame[1:4] = static.DXCALLSIGN_CRC
        rpt_frame[4:7] = static.MYCALLSIGN_CRC
        rpt_frame[7:13] = missing_frames

        self.log.info("[TNC] ARQ | RX | Requesting", frames=missing_frames)
        # Transmit frame
        self.enqueue_frame_for_tx(rpt_frame)

    def send_burst_nack_frame(self, snr=0):
        """ Build and send NACK frame for received DATA frame """
        nack_frame = bytearray(14)
        nack_frame[:1] = bytes([63])
        nack_frame[1:4] = static.DXCALLSIGN_CRC
        nack_frame[4:7] = static.MYCALLSIGN_CRC
        nack_frame[7:8] = bytes([int(snr)])
        nack_frame[8:9] = bytes([int(self.speed_level)])

        # TRANSMIT NACK FRAME FOR BURST
        self.enqueue_frame_for_tx(nack_frame)

    def send_burst_nack_frame_watchdog(self, snr=0):
        """ Build and send NACK frame for watchdog timeout """
        nack_frame = bytearray(14)
        nack_frame[:1] = bytes([64])
        nack_frame[1:4] = static.DXCALLSIGN_CRC
        nack_frame[4:7] = static.MYCALLSIGN_CRC
        nack_frame[7:8] = bytes([int(snr)])
        nack_frame[8:9] = bytes([int(self.speed_level)])

        # TRANSMIT NACK FRAME FOR BURST
        self.enqueue_frame_for_tx(nack_frame)

    def send_disconnect_frame(self):
        """ Build and send a disconnect frame """
        disconnection_frame = bytearray(14)
        disconnection_frame[:1] = bytes([223])
        disconnection_frame[1:4] = static.DXCALLSIGN_CRC
        disconnection_frame[4:7] = static.MYCALLSIGN_CRC
        disconnection_frame[7:13] = helpers.callsign_to_bytes(self.mycallsign)

        self.enqueue_frame_for_tx(disconnection_frame, copies=5, repeat_delay=250)

    def arq_data_received(self, data_in: bytes, bytes_per_frame: int, snr: int, freedv):
        """
        Args:
          data_in:bytes:
          bytes_per_frame:int:
          snr:int:
          freedv:

        Returns:
        """
        data_in = bytes(data_in)

        # get received crc for different mycall ssids
        self.received_mycall_crc = data_in[2:5]

        # check if callsign ssid override
        valid, mycallsign = helpers.check_callsign(self.mycallsign, self.received_mycall_crc)
        if not valid:
            # ARQ data packet not for me.
            if not TESTMODE:
                self.arq_cleanup()
            return

        # only process data if we are in ARQ and BUSY state else return to quit
        if not static.ARQ_STATE and static.TNC_STATE != "BUSY":
            return

        self.arq_file_transfer = True

        static.TNC_STATE = "BUSY"
        static.ARQ_STATE = True
        static.INFO.append("ARQ;RECEIVING")
        self.data_channel_last_received = int(time.time())

        # get some important data from the frame
        RX_N_FRAME_OF_BURST = int.from_bytes(bytes(data_in[:1]), "big") - 10  # get number of burst frame
        RX_N_FRAMES_PER_BURST = int.from_bytes(bytes(data_in[1:2]), "big")  # get number of bursts from received frame

        # The RX burst buffer needs to have a fixed length filled with "None".
        # We need this later for counting the "Nones" to detect missing data.
        # Check if burst buffer has expected length else create it
        if len(static.RX_BURST_BUFFER) != RX_N_FRAMES_PER_BURST:
            static.RX_BURST_BUFFER = [None] * RX_N_FRAMES_PER_BURST

        # Append data to rx burst buffer
        static.RX_BURST_BUFFER[RX_N_FRAME_OF_BURST] = data_in[8:]  # [frame_type][n_frames_per_burst][CRC24][CRC24]

        self.log.debug("[TNC] static.RX_BURST_BUFFER", buffer=static.RX_BURST_BUFFER)

        helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "DATA-CHANNEL",
                                        snr, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)

        # Check if we received all frames in the burst by checking if burst buffer has no more "Nones"
        # This is the ideal case because we received all data
        if None not in static.RX_BURST_BUFFER:
            # then iterate through burst buffer and stick the burst together
            # the temp burst buffer is needed for checking, if we already recevied data
            temp_burst_buffer = b""
            for value in static.RX_BURST_BUFFER:
                # static.RX_FRAME_BUFFER += static.RX_BURST_BUFFER[i]
                temp_burst_buffer += bytes(value)

            # if frame buffer ends not with the current frame, we are going to append new data
            # if data already exists, we received the frame correctly, but the ACK frame didn't receive its destination (ISS)
            if static.RX_FRAME_BUFFER.endswith(temp_burst_buffer):
                self.log.info("[TNC] ARQ | RX | Frame already received - sending ACK again")
                static.RX_BURST_BUFFER = []

            else:
                # Here we are going to search for our data in the last received bytes.
                # This reduces the chance we will lose the entire frame in the case of signalling frame loss

                # static.RX_FRAME_BUFFER --> existing data
                # temp_burst_buffer --> new data
                # search_area --> area where we want to search
                search_area = 510

                search_position = len(static.RX_FRAME_BUFFER) - search_area
                # find position of data. returns -1 if nothing found in area else >= 0
                # we are beginning from the end, so if data exists twice or more, only the last one should be replaced
                get_position = static.RX_FRAME_BUFFER[search_position:].rfind(temp_burst_buffer)
                # if we find data, replace it at this position with the new data and strip it
                if get_position >= 0:
                    static.RX_FRAME_BUFFER = static.RX_FRAME_BUFFER[:search_position + get_position]
                    static.RX_FRAME_BUFFER += temp_burst_buffer

                    self.log.warning("[TNC] ARQ | RX | replacing existing buffer data",
                        area=search_area, pos=get_position)
                # if we don't find data n this range, we really have new data and going to replace it
                else:
                    static.RX_FRAME_BUFFER += temp_burst_buffer
                    self.log.debug("[TNC] ARQ | RX | appending data to buffer")

            # lets check if we didn't receive a BOF and EOF,yet
            # to avoid sending ack frames, if we already received all data
            if (not self.rx_frame_bof_received and
                    not self.rx_frame_eof_received and
                    data_in.find(self.data_frame_eof) < 0):

                self.frame_received_counter += 1
                if self.frame_received_counter >= 2:
                    self.frame_received_counter = 0
                    self.speed_level += 1
                    if self.speed_level >= len(self.mode_list):
                        self.speed_level = len(self.mode_list) - 1
                        static.ARQ_SPEED_LEVEL = self.speed_level

                # Update modes we are listening to
                self.set_listening_modes(self.mode_list[self.speed_level])

                # Create and send ACK frame
                self.log.info("[TNC] ARQ | RX | SENDING ACK")
                self.send_burst_ack_frame(snr)

                # Reset n retries per burst counter
                self.n_retries_per_burst = 0

                # calculate statistics
                self.calculate_transfer_rate_rx(self.rx_start_of_transmission, len(static.RX_FRAME_BUFFER))

        elif RX_N_FRAME_OF_BURST == RX_N_FRAMES_PER_BURST - 1:
            # We have "Nones" in our rx buffer,
            # Check if we received last frame of burst - this is an indicator for missed frames.
            # With this way of doing this, we always MUST receive the last frame of a burst otherwise the entire
            # burst is lost
            self.log.debug("[TNC] all frames in burst received:", frame=RX_N_FRAME_OF_BURST,
                frames=RX_N_FRAMES_PER_BURST)
            self.send_retransmit_request_frame(freedv)
            self.calculate_transfer_rate_rx(self.rx_start_of_transmission, len(static.RX_FRAME_BUFFER))

        # Should never reach this point
        else:
            self.log.error("[TNC] data_handler: Should not reach this point...",
                frame=RX_N_FRAME_OF_BURST, frames=RX_N_FRAMES_PER_BURST)

        # We have a BOF and EOF flag in our data. If we received both we received our frame.
        # In case of loosing data, but we received already a BOF and EOF we need to make sure, we
        # received the complete last burst by checking it for Nones
        bof_position = static.RX_FRAME_BUFFER.find(self.data_frame_bof)
        eof_position = static.RX_FRAME_BUFFER.find(self.data_frame_eof)

        # get total bytes per transmission information as soon we recevied a frame with a BOF

        if bof_position >= 0:
            payload = static.RX_FRAME_BUFFER[bof_position + len(self.data_frame_bof):eof_position]
            frame_length = int.from_bytes(payload[4:8], "big")  # 4:8 4bytes
            static.TOTAL_BYTES = frame_length
            compression_factor = int.from_bytes(payload[8:9], "big")  # 4:8 4bytes
            compression_factor = np.clip(compression_factor, 0, 255)  # limit to max value of 255
            static.ARQ_COMPRESSION_FACTOR = compression_factor / 10
            self.calculate_transfer_rate_rx(self.rx_start_of_transmission, len(static.RX_FRAME_BUFFER))

        if bof_position >= 0 and eof_position > 0 and None not in static.RX_BURST_BUFFER:
            self.log.debug("[TNC] arq_data_received:", bof_position=bof_position,
                eof_position=eof_position)
            # print(f"bof_position {bof_position} / eof_position {eof_position}")
            self.rx_frame_bof_received = True
            self.rx_frame_eof_received = True

            # Extract raw data from buffer
            payload = static.RX_FRAME_BUFFER[bof_position + len(self.data_frame_bof):eof_position]
            # Get the data frame crc
            data_frame_crc = payload[:4]  # 0:4 4bytes
            # Get the data frame length
            frame_length = int.from_bytes(payload[4:8], "big")  # 4:8 4bytes
            static.TOTAL_BYTES = frame_length
            # 8:9 = compression factor

            data_frame = payload[9:]
            data_frame_crc_received = helpers.get_crc_32(data_frame)

            # Check if data_frame_crc is equal with received crc
            if data_frame_crc == data_frame_crc_received:
                self.log.info("[TNC] ARQ | RX | DATA FRAME SUCESSFULLY RECEIVED")

                # Decompress the data frame
                data_frame_decompressed = zlib.decompress(data_frame)
                static.ARQ_COMPRESSION_FACTOR = len(data_frame_decompressed) / len(data_frame)
                data_frame = data_frame_decompressed

                uniqueid = str(uuid.uuid4())
                timestamp = int(time.time())

                # check if callsign ssid override
                valid, mycallsign = helpers.check_callsign(self.mycallsign, self.received_mycall_crc)
                if not valid:
                    # ARQ data packet not for me.
                    if not TESTMODE:
                        self.arq_cleanup()
                    return

                # Re-code data_frame in base64, UTF-8 for JSON UI communication.
                base64_data = base64.b64encode(data_frame).decode("utf-8")
                static.RX_BUFFER.append([uniqueid, timestamp, static.DXCALLSIGN, static.DXGRID, base64_data])
                jsondata = {"arq": "received", "uuid": uniqueid, "timestamp": timestamp,
                            "mycallsign": str(mycallsign, "utf-8"),
                            "dxcallsign": str(static.DXCALLSIGN, "utf-8"),
                            "dxgrid": str(static.DXGRID, "utf-8"), "data": base64_data}
                json_data_out = json.dumps(jsondata)
                self.log.debug("[TNC] arq_data_received:", jsondata=jsondata)
                sock.SOCKET_QUEUE.put(json_data_out)
                static.INFO.append("ARQ;RECEIVING;SUCCESS")

                self.log.info("[TNC] ARQ | RX | SENDING DATA FRAME ACK", snr=snr,
                    crc=data_frame_crc.hex())
                self.send_data_ack_frame(snr)
                # update our statistics AFTER the frame ACK
                self.calculate_transfer_rate_rx(self.rx_start_of_transmission, len(static.RX_FRAME_BUFFER))

                self.log.info("[TNC] | RX | DATACHANNEL [" + str(self.mycallsign, "utf-8") +
                    "]<< >>[" + str(static.DXCALLSIGN, "utf-8") + "]", snr=snr)

            else:
                static.INFO.append("ARQ;RECEIVING;FAILED")
                self.log.warning("[TNC] ARQ | RX | DATA FRAME NOT SUCESSFULLY RECEIVED!",
                    e="wrong crc", expected=data_frame_crc,
                    received=data_frame_crc_received,
                    overflows=static.BUFFER_OVERFLOW_COUNTER)

                self.log.info("[TNC] ARQ | RX | Sending NACK")
                self.send_burst_nack_frame(snr)

            # update session timeout
            self.arq_session_last_received = int(time.time())  # we need to update our timeout timestamp

            # And finally we do a cleanup of our buffers and states
            # do cleanup only when not in testmode
            if not TESTMODE:
                self.arq_cleanup()

    def arq_transmit(self, data_out: bytes, mode: int, n_frames_per_burst: int):
        """

        Args:
          data_out:bytes:
          mode:int:
          n_frames_per_burst:int:

        Returns:

        """
        self.arq_file_transfer = True

        self.speed_level = len(self.mode_list) - 1  # speed level for selecting mode
        static.ARQ_SPEED_LEVEL = self.speed_level

        TX_N_SENT_BYTES = 0  # already sent bytes per data frame
        self.tx_n_retry_of_burst = 0  # retries we already sent data
        TX_N_MAX_RETRIES_PER_BURST = 50  # max amount of retries we sent before frame is lost
        TX_N_FRAMES_PER_BURST = n_frames_per_burst  # amount of n frames per burst
        TX_BUFFER = []  # our buffer for appending new data

        # TIMEOUTS
        BURST_ACK_TIMEOUT_SECONDS = 3.0  # timeout for burst  acknowledges
        DATA_FRAME_ACK_TIMEOUT_SECONDS = 3.0  # timeout for data frame acknowledges
        RPT_ACK_TIMEOUT_SECONDS = 3.0  # timeout for rpt frame acknowledges

        # save len of data_out to TOTAL_BYTES for our statistics --> kBytes
        # static.TOTAL_BYTES = round(len(data_out) / 1024, 2)
        static.TOTAL_BYTES = len(data_out)
        frame_total_size = len(data_out).to_bytes(4, byteorder="big")
        static.INFO.append("ARQ;TRANSMITTING")

        jsondata = {"arq": "transmission", "status": "transmitting", "uuid": self.transmission_uuid,
                    "percent": static.ARQ_TRANSMISSION_PERCENT, "bytesperminute": static.ARQ_BYTES_PER_MINUTE}
        json_data_out = json.dumps(jsondata)
        sock.SOCKET_QUEUE.put(json_data_out)

        self.log.info("[TNC] | TX | DATACHANNEL", mode=mode, Bytes=static.TOTAL_BYTES)

        # Compress data frame
        data_frame_compressed = zlib.compress(data_out)
        compression_factor = len(data_out) / len(data_frame_compressed)
        static.ARQ_COMPRESSION_FACTOR = np.clip(compression_factor, 0, 255)
        compression_factor = bytes([int(static.ARQ_COMPRESSION_FACTOR * 10)])

        data_out = data_frame_compressed

        # Reset data transfer statistics
        tx_start_of_transmission = time.time()
        self.calculate_transfer_rate_tx(tx_start_of_transmission, 0, len(data_out))

        # Append a crc at the beginning and end of file indicators
        frame_payload_crc = helpers.get_crc_32(data_out)
        self.log.debug("[TNC] frame payload CRC:", crc=frame_payload_crc)

        # data_out = self.data_frame_bof + frame_payload_crc + data_out + self.data_frame_eof
        data_out = self.data_frame_bof + frame_payload_crc + frame_total_size + compression_factor + data_out + self.data_frame_eof

        # initial bufferposition is 0
        bufferposition = bufferposition_end = 0

        # iterate through data out buffer
        while bufferposition < len(data_out) and not self.data_frame_ack_received and static.ARQ_STATE:

            # we have TX_N_MAX_RETRIES_PER_BURST attempts for sending a burst
            for self.tx_n_retry_of_burst in range(TX_N_MAX_RETRIES_PER_BURST):
                # AUTO MODE SELECTION
                # mode 255 == AUTO MODE
                # force usage of selected mode
                if mode != 255:
                    data_mode = mode
                    self.log.debug("[TNC] FIXED MODE:", mode=data_mode)
                else:
                    # we are doing a modulo check of transmission retries of the actual burst
                    # every 2nd retry which fails, decreases speedlevel by 1.
                    # as soon as we received an ACK for the current burst, speed_level will increase
                    # by 1.
                    # They can be optimised by checking the optimal speed level for the current conditions
                    '''
                    if not self.tx_n_retry_of_burst % 2 and self.tx_n_retry_of_burst > 0:
                        self.speed_level -= 1
                        if self.speed_level < 0:
                            self.speed_level = 0
                    '''

                    # if self.tx_n_retry_of_burst <= 1:
                    #    self.speed_level += 1
                    #    if self.speed_level >= len(self.mode_list)-1:
                    #        self.speed_level = len(self.mode_list)-1

                    # if speed level is greater than our available modes, set speed level to maximum = lenght of mode list -1

                    # if speed level is greater than our available modes, set speed level to maximum = lenght of mode list -1
                    if self.speed_level >= len(self.mode_list):
                        self.speed_level = len(self.mode_list) - 1
                        static.ARQ_SPEED_LEVEL = self.speed_level
                    data_mode = self.mode_list[self.speed_level]

                    self.log.debug("[TNC] Speed-level:", level=self.speed_level,
                        retry=self.tx_n_retry_of_burst, mode=data_mode)

                # payload information
                payload_per_frame = modem.get_bytes_per_frame(data_mode) - 2

                # tempbuffer list for storing our data frames
                tempbuffer = []

                # append data frames with TX_N_FRAMES_PER_BURST to tempbuffer
                # TODO: this part needs a complete rewrite!
                # TX_N_FRAMES_PER_BURST = 1 is working

                arqheader = bytearray()
                arqheader[:1] = bytes([10])  # bytes([10 + i])
                arqheader[1:2] = bytes([TX_N_FRAMES_PER_BURST])
                arqheader[2:5] = static.DXCALLSIGN_CRC
                arqheader[5:8] = static.MYCALLSIGN_CRC

                bufferposition_end = (bufferposition + payload_per_frame - len(arqheader))

                # normal behavior
                if bufferposition_end <= len(data_out):
                    frame = data_out[bufferposition:bufferposition_end]
                    frame = arqheader + frame

                # this point shouldn't reach that often
                elif bufferposition > len(data_out):
                    break

                # the last bytes of a frame
                else:
                    extended_data_out = data_out[bufferposition:]
                    extended_data_out += bytes([0]) * (payload_per_frame - len(extended_data_out) - len(arqheader))
                    frame = arqheader + extended_data_out

                # append frame to tempbuffer for transmission
                tempbuffer.append(frame)

                self.log.debug("[TNC] tempbuffer:", tempbuffer=tempbuffer)
                self.log.info("[TNC] ARQ | TX | FRAMES", mode=data_mode,
                    fpb=TX_N_FRAMES_PER_BURST, retry=self.tx_n_retry_of_burst)

                # we need to set our TRANSMITTING flag before we are adding an object the transmit queue
                # this is not that nice, we could improve this somehow
                static.TRANSMITTING = True
                modem.MODEM_TRANSMIT_QUEUE.put([data_mode, 1, 0, tempbuffer])

                # wait while transmitting
                while static.TRANSMITTING:
                    time.sleep(0.01)

                # after transmission finished  wait for an ACK or RPT frame
                '''
                burstacktimeout = time.time() + BURST_ACK_TIMEOUT_SECONDS + 100
                while not self.burst_ack and not self.burst_nack and not self.rpt_request_received and not self.data_frame_ack_received and time.time() < burstacktimeout and static.ARQ_STATE:
                    time.sleep(0.01)
                '''
                # burstacktimeout = time.time() + BURST_ACK_TIMEOUT_SECONDS + 100
                while (static.ARQ_STATE and not
                (self.burst_ack or self.burst_nack or
                 self.rpt_request_received or self.data_frame_ack_received)):
                    time.sleep(0.01)

                # once we received a burst ack, reset its state and break the RETRIES loop
                if self.burst_ack:
                    self.burst_ack = False  # reset ack state
                    self.tx_n_retry_of_burst = 0  # reset retries
                    break  # break retry loop

                if self.burst_nack:
                    self.burst_nack = False  # reset nack state

                # not yet implemented
                if self.rpt_request_received:
                    pass

                if self.data_frame_ack_received:
                    break  # break retry loop

                # we need this part for leaving the repeat loop
                # static.ARQ_STATE == "DATA" --> when stopping transmission manually
                if not static.ARQ_STATE:
                    # print("not ready for data...leaving loop....")
                    break

                self.calculate_transfer_rate_tx(tx_start_of_transmission, bufferposition_end, len(data_out))
                # NEXT ATTEMPT
                self.log.debug("[TNC] ATTEMPT:", retry=self.tx_n_retry_of_burst,
                    maxretries=TX_N_MAX_RETRIES_PER_BURST, overflows=static.BUFFER_OVERFLOW_COUNTER)

            # update buffer position
            bufferposition = bufferposition_end

            # update stats
            self.calculate_transfer_rate_tx(tx_start_of_transmission, bufferposition_end, len(data_out))

            jsondata = {"arq": "transmission", "status": "transmitting", "uuid": self.transmission_uuid,
                "percent": static.ARQ_TRANSMISSION_PERCENT, "bytesperminute": static.ARQ_BYTES_PER_MINUTE}
            json_data_out = json.dumps(jsondata)
            sock.SOCKET_QUEUE.put(json_data_out)

            # GOING TO NEXT ITERATION

        if self.data_frame_ack_received:
            static.INFO.append("ARQ;TRANSMITTING;SUCCESS")
            jsondata = {"arq": "transmission", "status": "success", "uuid": self.transmission_uuid,
                "percent": static.ARQ_TRANSMISSION_PERCENT, "bytesperminute": static.ARQ_BYTES_PER_MINUTE}
            json_data_out = json.dumps(jsondata)
            sock.SOCKET_QUEUE.put(json_data_out)

            self.log.info("[TNC] ARQ | TX | DATA TRANSMITTED!",
                BytesPerMinute=static.ARQ_BYTES_PER_MINUTE, BitsPerSecond=static.ARQ_BITS_PER_SECOND,
                overflows=static.BUFFER_OVERFLOW_COUNTER)

        else:
            static.INFO.append("ARQ;TRANSMITTING;FAILED")
            jsondata = {"arq": "transmission", "status": "failed", "uuid": self.transmission_uuid,
                        "percent": static.ARQ_TRANSMISSION_PERCENT,
                        "bytesperminute": static.ARQ_BYTES_PER_MINUTE}
            json_data_out = json.dumps(jsondata)
            sock.SOCKET_QUEUE.put(json_data_out)

            self.log.info("[TNC] ARQ | TX | TRANSMISSION FAILED OR TIME OUT!",
                overflows=static.BUFFER_OVERFLOW_COUNTER)
            self.stop_transmission()

        # and last but not least doing a state cleanup
        # do cleanup only when not in testmode
        if not TESTMODE:
            self.arq_cleanup()
        else:
            # quit after transmission
            sys.exit(0)

    # signalling frames received
    def burst_ack_received(self, data_in: bytes):
        """

        Args:
          data_in:bytes:

        Returns:

        """
        # increase speed level if we received a burst ack
        # self.speed_level += 1
        # if self.speed_level >= len(self.mode_list)-1:
        #     self.speed_level = len(self.mode_list)-1

        # only process data if we are in ARQ and BUSY state
        if static.ARQ_STATE:
            helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "DATA-CHANNEL", static.SNR,
                                          static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
            self.burst_ack = True  # Force data loops of TNC to stop and continue with next frame
            self.data_channel_last_received = int(time.time())  # we need to update our timeout timestamp
            self.burst_ack_snr = int.from_bytes(bytes(data_in[7:8]), "big")
            self.speed_level = int.from_bytes(bytes(data_in[8:9]), "big")
            static.ARQ_SPEED_LEVEL = self.speed_level
            self.log.debug("[TNC] burst_ack_received:", speed_level=self.speed_level)

            # reset burst nack counter
            self.burst_nack_counter = 0
            # reset n retries per burst counter
            self.n_retries_per_burst = 0

    # signalling frames received
    def burst_nack_received(self, data_in: bytes):
        """

        Args:
          data_in:bytes:

        """
        # increase speed level if we received a burst ack
        # self.speed_level += 1
        # if self.speed_level >= len(self.mode_list)-1:
        #     self.speed_level = len(self.mode_list)-1

        # only process data if we are in ARQ and BUSY state
        if static.ARQ_STATE:
            helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "DATA-CHANNEL", static.SNR,
                                          static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
            self.burst_nack = True  # Force data loops of TNC to stop and continue with next frame
            self.data_channel_last_received = int(time.time())  # we need to update our timeout timestamp
            self.burst_ack_snr = int.from_bytes(bytes(data_in[7:8]), "big")
            self.speed_level = int.from_bytes(bytes(data_in[8:9]), "big")
            static.ARQ_SPEED_LEVEL = self.speed_level
            self.burst_nack_counter += 1
            self.log.debug("[TNC] burst_nack_received:", speed_level=self.speed_level)

    def frame_ack_received(self):
        """ """
        # only process data if we are in ARQ and BUSY state
        if static.ARQ_STATE:
            helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "DATA-CHANNEL", static.SNR,
                                          static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
            # Force data loops of TNC to stop and continue with next frame
            self.data_frame_ack_received = True
            # Update timeout timestamps
            self.data_channel_last_received = int(time.time())
            self.arq_session_last_received = int(time.time())

    def frame_nack_received(self, data_in: bytes):  # pylint: disable=unused-argument
        """

        Args:
          data_in:bytes:

        Returns:

        """
        helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "DATA-CHANNEL",
                                        static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
        static.INFO.append("ARQ;TRANSMITTING;FAILED")
        jsondata = {"arq": "transmission", "status": "failed", "uuid": self.transmission_uuid,
                    "percent": static.ARQ_TRANSMISSION_PERCENT, "bytesperminute": static.ARQ_BYTES_PER_MINUTE}
        json_data_out = json.dumps(jsondata)
        sock.SOCKET_QUEUE.put(json_data_out)
        self.arq_session_last_received = int(time.time())  # we need to update our timeout timestamp

        if not TESTMODE:
            self.arq_cleanup()

    def burst_rpt_received(self, data_in: bytes):
        """

        Args:
          data_in:bytes:

        Returns:

        """
        # only process data if we are in ARQ and BUSY state
        if static.ARQ_STATE and static.TNC_STATE == "BUSY":
            helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "DATA-CHANNEL", static.SNR,
                                          static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)

            self.rpt_request_received = True
            self.data_channel_last_received = int(time.time())  # we need to update our timeout timestamp
            self.rpt_request_buffer = []

            missing_area = bytes(data_in[3:12])  # 1:9

            for i in range(0, 6, 2):
                if not missing_area[i:i + 2].endswith(b"\x00\x00"):
                    missing = missing_area[i:i + 2]
                    self.rpt_request_buffer.insert(0, missing)

    # ############################################################################################################
    # ARQ SESSION HANDLER
    # ############################################################################################################
    def arq_session_handler(self, callsign):
        """

        Args:
          callsign:

        Returns:

        """
        # TODO: we need to check this, maybe placing it to class init
        self.datachannel_timeout = False
        self.log.info(
            "[TNC] SESSION [" + str(self.mycallsign, "utf-8") +
            "]>> <<[" + str(static.DXCALLSIGN, "utf-8") + "]",
            state=static.ARQ_SESSION_STATE)

        self.open_session(callsign)

        # wait until data channel is open
        while not static.ARQ_SESSION and not self.arq_session_timeout:
            time.sleep(0.01)
            static.ARQ_SESSION_STATE = "connecting"

        if static.ARQ_SESSION and static.ARQ_SESSION_STATE == "connected":
            # static.ARQ_SESSION_STATE = "connected"
            return True

        static.ARQ_SESSION_STATE = "failed"
        return False

    def open_session(self, callsign):
        """

        Args:
          callsign:

        Returns:

        """
        self.IS_ARQ_SESSION_MASTER = True
        static.ARQ_SESSION_STATE = "connecting"

        connection_frame = bytearray(14)
        connection_frame[:1] = bytes([221])
        connection_frame[1:4] = static.DXCALLSIGN_CRC
        connection_frame[4:7] = static.MYCALLSIGN_CRC
        connection_frame[7:13] = helpers.callsign_to_bytes(self.mycallsign)

        while not static.ARQ_SESSION:
            time.sleep(0.01)
            for attempt in range(1, self.session_connect_max_retries + 1):
                self.log.info(
                    "[TNC] SESSION [" + str(self.mycallsign, "utf-8") +
                    "]>>?<<[" + str(static.DXCALLSIGN, "utf-8") + "]",
                    a=attempt, state=static.ARQ_SESSION_STATE)

                self.enqueue_frame_for_tx(connection_frame)

                timeout = time.time() + 3
                while time.time() < timeout:
                    time.sleep(0.01)
                    # break if data channel is opened
                    if static.ARQ_SESSION:
                        return True
                # if static.ARQ_SESSION:
                #     break

            # Session connect timeout, send close_session frame to
            # attempt to clean up the far-side, if it received the
            # open_session frame and can still hear us.
            if not static.ARQ_SESSION:
                self.close_session()
                return False

    def received_session_opener(self, data_in: bytes):
        """

        Args:
          data_in:bytes:

        Returns:

        """
        self.IS_ARQ_SESSION_MASTER = False
        static.ARQ_SESSION_STATE = "connecting"

        self.arq_session_last_received = int(time.time())

        static.DXCALLSIGN_CRC = bytes(data_in[4:7])
        static.DXCALLSIGN = helpers.bytes_to_callsign(bytes(data_in[7:13]))

        helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "DATA-CHANNEL",
                                        static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
        self.log.info(
            "[TNC] SESSION [" + str(self.mycallsign, "utf-8") +
            "]>>|<<[" + str(static.DXCALLSIGN, "utf-8") + "]",
            state=static.ARQ_SESSION_STATE)
        static.ARQ_SESSION = True
        static.TNC_STATE = "BUSY"

        self.transmit_session_heartbeat()

    def close_session(self):
        """ Close the ARQ session """
        static.ARQ_SESSION_STATE = "disconnecting"
        helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "DATA-CHANNEL",
                                        static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
        self.log.info(
            "[TNC] SESSION [" + str(self.mycallsign, "utf-8") +
            "]<<X>>[" + str(static.DXCALLSIGN, "utf-8") + "]",
            state=static.ARQ_SESSION_STATE)
        static.INFO.append("ARQ;SESSION;CLOSE")
        self.IS_ARQ_SESSION_MASTER = False
        static.ARQ_SESSION = False
        if not TESTMODE:
            self.arq_cleanup()

        self.send_disconnect_frame()

    def received_session_close(self, data_in: bytes):
        """
        Closes the session when a close session frame is received and
        the DXCALLSIGN_CRC matches the remote station participating in the session.

        Args:
          data_in:bytes:

        Returns:
        """
        # Close the session if the DXCALLSIGN_CRC matches the station in static.
        _valid_crc, _ = helpers.check_callsign(static.DXCALLSIGN, bytes(data_in[4:7]))
        if _valid_crc:
            static.ARQ_SESSION_STATE = "disconnected"
            helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "DATA-CHANNEL", static.SNR,
                                          static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
            self.log.info(
                "[TNC] SESSION [" + str(self.mycallsign, "utf-8") +
                "]<<X>>[" + str(static.DXCALLSIGN, "utf-8") + "]",
                state=static.ARQ_SESSION_STATE)
            static.INFO.append("ARQ;SESSION;CLOSE")

            self.IS_ARQ_SESSION_MASTER = False
            static.ARQ_SESSION = False
            self.arq_cleanup()

    def transmit_session_heartbeat(self):
        """ """
        # static.ARQ_SESSION = True
        # static.TNC_STATE = "BUSY"
        # static.ARQ_SESSION_STATE = "connected"

        connection_frame = bytearray(14)
        connection_frame[:1] = bytes([222])
        connection_frame[1:4] = static.DXCALLSIGN_CRC
        connection_frame[4:7] = static.MYCALLSIGN_CRC

        self.enqueue_frame_for_tx(connection_frame)

    def received_session_heartbeat(self, data_in: bytes):
        """

        Args:
          data_in:bytes:

        Returns:

        """
        # Accept session data if the DXCALLSIGN_CRC matches the station in static.
        _valid_crc, _ = helpers.check_callsign(static.DXCALLSIGN, bytes(data_in[4:7]))
        if _valid_crc:
            self.log.debug("[TNC] Received session heartbeat")
            helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "SESSION-HB", static.SNR,
                                          static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)

            self.arq_session_last_received = int(time.time())  # we need to update our timeout timestamp

            static.ARQ_SESSION = True
            static.ARQ_SESSION_STATE = "connected"
            static.TNC_STATE = "BUSY"
            self.data_channel_last_received = int(time.time())
            if not self.IS_ARQ_SESSION_MASTER and not self.arq_file_transfer:
                self.transmit_session_heartbeat()

    # ############################################################################################################
    # ARQ DATA CHANNEL HANDLER
    # ############################################################################################################
    def open_dc_and_transmit(self, data_out: bytes, mode: int, n_frames_per_burst: int, transmission_uuid: str,
                             mycallsign):
        """

        Args:
          data_out:bytes:
          mode:int:
          n_frames_per_burst:int:

        Returns:

        """
        # overwrite mycallsign in case of different SSID
        self.mycallsign = mycallsign

        static.TNC_STATE = "BUSY"
        self.arq_file_transfer = True

        self.transmission_uuid = transmission_uuid

        # wait a moment for the case, a heartbeat is already on the way back to us
        if static.ARQ_SESSION:
            time.sleep(0.5)

        self.datachannel_timeout = False

        # we need to compress data for gettin a compression factor.
        # so we are compressing twice. This is not that nice and maybe there is another way
        # for calculating transmission statistics
        static.ARQ_COMPRESSION_FACTOR = len(data_out) / len(zlib.compress(data_out))

        self.arq_open_data_channel(mode, n_frames_per_burst, mycallsign)

        # wait until data channel is open
        while not static.ARQ_STATE and not self.datachannel_timeout:
            time.sleep(0.01)

        if static.ARQ_STATE:
            self.arq_transmit(data_out, mode, n_frames_per_burst)
        else:
            return False

    def arq_open_data_channel(self, mode: int, n_frames_per_burst: int, mycallsign):
        """

        Args:
          mode:int:
          n_frames_per_burst:int:

        Returns:

        """
        self.is_IRS = False
        self.data_channel_last_received = int(time.time())

        if static.LOW_BANDWIDTH_MODE and mode == 255:
            frametype = bytes([227])
            self.log.debug("[TNC] Requesting low bandwidth mode")

        else:
            frametype = bytes([225])
            self.log.debug("[TNC] Requesting high bandwidth mode")

        if 230 <= mode <= 240:
            self.log.debug("[TNC] Requesting manual mode --> not yet implemented ")
            frametype = bytes([mode])

        connection_frame = bytearray(14)
        connection_frame[:1] = frametype
        connection_frame[1:4] = static.DXCALLSIGN_CRC
        connection_frame[4:7] = static.MYCALLSIGN_CRC
        connection_frame[7:13] = helpers.callsign_to_bytes(mycallsign)
        connection_frame[13:14] = bytes([n_frames_per_burst])

        while not static.ARQ_STATE:
            time.sleep(0.01)
            for attempt in range(1, self.data_channel_max_retries + 1):
                static.INFO.append("DATACHANNEL;OPENING")
                self.log.info(
                    "[TNC] ARQ | DATA | TX | [" + str(mycallsign, "utf-8") +
                    "]>> <<[" + str(static.DXCALLSIGN, "utf-8") + "]",
                    attempt=f"{str(attempt)}/{str(self.data_channel_max_retries)}")

                self.enqueue_frame_for_tx(connection_frame)

                timeout = time.time() + 3
                while time.time() < timeout:
                    time.sleep(0.01)
                    # break if data channel is opened
                    if static.ARQ_STATE:
                        break

                if static.ARQ_STATE:
                    break

                if attempt == self.data_channel_max_retries:
                    static.INFO.append("DATACHANNEL;FAILED")

                    self.log.debug("[TNC] arq_open_data_channel:",
                        transmission_uuid=self.transmission_uuid)
                    # print(self.transmission_uuid)
                    jsondata = {"arq": "transmission", "status": "failed", "uuid": self.transmission_uuid,
                                "percent": static.ARQ_TRANSMISSION_PERCENT,
                                "bytesperminute": static.ARQ_BYTES_PER_MINUTE}
                    json_data_out = json.dumps(jsondata)
                    sock.SOCKET_QUEUE.put(json_data_out)

                    self.log.warning(
                        "[TNC] ARQ | TX | DATA [" + str(mycallsign, "utf-8") +
                        "]>>X<<[" + str(static.DXCALLSIGN, "utf-8") + "]"
                        )
                    self.datachannel_timeout = True
                    if not TESTMODE:
                        self.arq_cleanup()

                    # attempt to clean up the far-side, if it received the
                    # open_session frame and can still hear us.
                    self.close_session()
                    return False
                    # sys.exit() # close thread and so connection attempts

    def arq_received_data_channel_opener(self, data_in: bytes):
        """

        Args:
          data_in:bytes:

        """
        self.arq_file_transfer = True
        self.is_IRS = True
        static.INFO.append("DATACHANNEL;RECEIVEDOPENER")
        static.DXCALLSIGN_CRC = bytes(data_in[4:7])
        static.DXCALLSIGN = helpers.bytes_to_callsign(bytes(data_in[7:13]))

        n_frames_per_burst = int.from_bytes(bytes(data_in[13:14]), "big")
        frametype = int.from_bytes(bytes(data_in[:1]), "big")
        # check if we received low bandwidth mode
        if frametype == 225:
            self.received_LOW_BANDWIDTH_MODE = False
            self.mode_list = self.mode_list_high_bw
            self.time_list = self.time_list_high_bw
        else:
            self.received_LOW_BANDWIDTH_MODE = True
            self.mode_list = self.mode_list_low_bw
            self.time_list = self.time_list_low_bw
        self.speed_level = len(self.mode_list) - 1

        if 230 <= frametype <= 240:
            self.log.debug("[TNC] arq_received_data_channel_opener: manual mode request")

        # updated modes we are listening to
        self.set_listening_modes(self.mode_list[self.speed_level])

        helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "DATA-CHANNEL",
                                        static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)

        # check if callsign ssid override
        valid, mycallsign = helpers.check_callsign(self.mycallsign, data_in[1:4])
        if not valid:
            # ARQ connect packet not for me.
            if not TESTMODE:
                self.arq_cleanup()
            return

        self.log.info(
            "[TNC] ARQ | DATA | RX | [" + str(mycallsign, "utf-8") +
            "]>> <<[" + str(static.DXCALLSIGN, "utf-8") + "]",
            bandwidth="wide")

        static.ARQ_STATE = True
        static.TNC_STATE = "BUSY"

        self.reset_statistics()

        self.data_channel_last_received = int(time.time())
        # check if we are in low bandwidth mode
        if static.LOW_BANDWIDTH_MODE or self.received_LOW_BANDWIDTH_MODE:
            frametype = bytes([228])
            self.log.debug("[TNC] Responding with low bandwidth mode")
        else:
            frametype = bytes([226])
            self.log.debug("[TNC] Responding with high bandwidth mode")

        connection_frame = bytearray(14)
        connection_frame[:1] = frametype
        connection_frame[1:4] = static.DXCALLSIGN_CRC
        connection_frame[4:7] = static.MYCALLSIGN_CRC
        connection_frame[13:14] = bytes([static.ARQ_PROTOCOL_VERSION])  # crc8 of version for checking protocol version

        self.enqueue_frame_for_tx(connection_frame)

        self.log.info(
            "[TNC] ARQ | DATA | RX | [" + str(mycallsign, "utf-8") +
            "]>>|<<[" + str(static.DXCALLSIGN, "utf-8") + "]",
            bandwidth="wide", snr=static.SNR)

        # set start of transmission for our statistics
        self.rx_start_of_transmission = time.time()

        # reset our data channel watchdog
        self.data_channel_last_received = int(time.time())

    def arq_received_channel_is_open(self, data_in: bytes):
        """
        Called if we received a data channel opener
        Args:
          data_in:bytes:

        Returns:

        """
        protocol_version = int.from_bytes(bytes(data_in[13:14]), "big")
        if protocol_version == static.ARQ_PROTOCOL_VERSION:
            static.INFO.append("DATACHANNEL;OPEN")
            frametype = int.from_bytes(bytes(data_in[:1]), "big")

            if frametype == 228:
                self.received_LOW_BANDWIDTH_MODE = True
                self.mode_list = self.mode_list_low_bw
                self.time_list = self.time_list_low_bw
                self.speed_level = len(self.mode_list) - 1
                self.log.debug("[TNC] low bandwidth mode", modes=self.mode_list)
            else:
                self.received_LOW_BANDWIDTH_MODE = False
                self.mode_list = self.mode_list_high_bw
                self.time_list = self.time_list_high_bw
                self.speed_level = len(self.mode_list) - 1
                self.log.debug("[TNC] high bandwidth mode", modes=self.mode_list)

            helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "DATA-CHANNEL", static.SNR,
                                          static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)

            self.log.info(
                "[TNC] ARQ | DATA | TX | [" + str(self.mycallsign, "utf-8") +
                "]>>|<<[" + str(static.DXCALLSIGN, "utf-8") + "]",
                snr=static.SNR)

            # as soon as we set ARQ_STATE to DATA, transmission starts
            static.ARQ_STATE = True
            self.data_channel_last_received = int(time.time())
        else:
            static.TNC_STATE = "IDLE"
            static.ARQ_STATE = False
            static.INFO.append("PROTOCOL;VERSION_MISMATCH")
            self.log.warning("[TNC] protocol version mismatch:",
                received=protocol_version, own=static.ARQ_PROTOCOL_VERSION)
            self.arq_cleanup()

    # ---------- PING
    def transmit_ping(self, dxcallsign: bytes):
        """
        Funktion for controlling pings
        Args:
          dxcallsign:bytes:

        Returns:

        """
        static.DXCALLSIGN = dxcallsign
        static.DXCALLSIGN_CRC = helpers.get_crc_24(static.DXCALLSIGN)

        static.INFO.append("PING;SENDING")
        self.log.info(
            "[TNC] PING REQ [" + str(self.mycallsign, "utf-8") +
            "] >>> [" + str(static.DXCALLSIGN, "utf-8") + "]")

        ping_frame = bytearray(14)
        ping_frame[:1] = bytes([210])
        ping_frame[1:4] = static.DXCALLSIGN_CRC
        ping_frame[4:7] = static.MYCALLSIGN_CRC
        ping_frame[7:13] = helpers.callsign_to_bytes(self.mycallsign)

        self.log.info("[TNC] ENABLE FSK", state=static.ENABLE_FSK)
        if static.ENABLE_FSK:
            self.enqueue_frame_for_tx(ping_frame, c2_mode=codec2.freedv_get_mode_value_by_name("FSK_LDPC_0"))
        else:
            self.enqueue_frame_for_tx(ping_frame)

    def received_ping(self, data_in: bytes):
        """
        Called if we received a ping

        Args:
          data_in:bytes:

        Returns:

        """
        static.DXCALLSIGN_CRC = bytes(data_in[4:7])
        static.DXCALLSIGN = helpers.bytes_to_callsign(bytes(data_in[7:13]))
        helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "PING", static.SNR,
                                        static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)

        static.INFO.append("PING;RECEIVING")

        # check if callsign ssid override
        valid, mycallsign = helpers.check_callsign(self.mycallsign, data_in[1:4])
        if not valid:
            # PING packet not for me.
            self.log.debug("[TNC] received_ping: ping not for this station.")
            return

        self.log.info(
            "[TNC] PING REQ [" + str(mycallsign, "utf-8") +
            "] <<< [" + str(static.DXCALLSIGN, "utf-8") + "]",
            snr=static.SNR)

        ping_frame = bytearray(14)
        ping_frame[:1] = bytes([211])
        ping_frame[1:4] = static.DXCALLSIGN_CRC
        ping_frame[4:7] = static.MYCALLSIGN_CRC
        ping_frame[7:13] = static.MYGRID

        self.log.info("[TNC] ENABLE FSK", state=static.ENABLE_FSK)
        if static.ENABLE_FSK:
            self.enqueue_frame_for_tx(ping_frame, c2_mode=codec2.freedv_get_mode_value_by_name("FSK_LDPC_0"))
        else:
            self.enqueue_frame_for_tx(ping_frame)

    def received_ping_ack(self, data_in: bytes):
        """
        Called if a PING ack has been received
        Args:
          data_in:bytes:

        Returns:

        """
        static.DXCALLSIGN_CRC = bytes(data_in[4:7])
        static.DXGRID = bytes(data_in[7:13]).rstrip(b"\x00")

        jsondata = {"type": "ping", "status": "ack", "uuid": str(uuid.uuid4()),
                    "timestamp": int(time.time()), "mycallsign": str(self.mycallsign, "utf-8"),
                    "dxcallsign": str(static.DXCALLSIGN, "utf-8"), "dxgrid": str(static.DXGRID, "utf-8"),
                    "snr": str(static.SNR)}
        json_data_out = json.dumps(jsondata)
        sock.SOCKET_QUEUE.put(json_data_out)

        helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, "PING-ACK",
                                        static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)

        static.INFO.append("PING;RECEIVEDACK")

        self.log.info(
            "[TNC] PING ACK [" + str(self.mycallsign, "utf-8") +
            "] >|< [" + str(static.DXCALLSIGN, "utf-8") + "]",
            snr=static.SNR)
        static.TNC_STATE = "IDLE"

    def stop_transmission(self):
        """
        Force a stop of the running transmission
        """
        self.log.warning("[TNC] Stopping transmission!")
        stop_frame = bytearray(14)
        stop_frame[:1] = bytes([249])
        stop_frame[1:4] = static.DXCALLSIGN_CRC
        stop_frame[4:7] = static.MYCALLSIGN_CRC
        stop_frame[7:13] = helpers.callsign_to_bytes(self.mycallsign)

        self.enqueue_frame_for_tx(stop_frame, copies=2, repeat_delay=250)

        static.TNC_STATE = "IDLE"
        static.ARQ_STATE = False
        static.INFO.append("TRANSMISSION;STOPPED")
        self.arq_cleanup()

    def received_stop_transmission(self):
        """
        Received a transmission stop
        """
        self.log.warning("[TNC] Stopping transmission!")
        static.TNC_STATE = "IDLE"
        static.ARQ_STATE = False
        static.INFO.append("TRANSMISSION;STOPPED")
        self.arq_cleanup()

    # ----------- BROADCASTS
    def run_beacon(self):
        """
        Controlling function for running a beacon
        Args:

          self: arq class

        Returns:

        """
        try:
            while True:
                time.sleep(0.5)
                while static.BEACON_STATE:
                    if not static.ARQ_SESSION and not self.arq_file_transfer and not static.BEACON_PAUSE:
                        static.INFO.append("BEACON;SENDING")
                        self.log.info("[TNC] Sending beacon!", interval=self.beacon_interval)

                        beacon_frame = bytearray(14)
                        beacon_frame[:1] = bytes([250])
                        beacon_frame[1:7] = helpers.callsign_to_bytes(self.mycallsign)
                        beacon_frame[9:13] = static.MYGRID[:4]
                        self.log.info("[TNC] ENABLE FSK", state=static.ENABLE_FSK)

                        if static.ENABLE_FSK:
                            self.enqueue_frame_for_tx(beacon_frame, c2_mode=codec2.freedv_get_mode_value_by_name("FSK_LDPC_0"))
                        else:
                            self.enqueue_frame_for_tx(beacon_frame)

                    interval_timer = time.time() + self.beacon_interval
                    while time.time() < interval_timer and static.BEACON_STATE and not static.BEACON_PAUSE:
                        time.sleep(0.01)

        except Exception as err:
            self.log.debug("[TNC] run_beacon: ", exception=err)

    def received_beacon(self, data_in: bytes):
        """
        Called if we received a beacon
        Args:
          data_in:bytes:

        Returns:

        """
        # here we add the received station to the heard stations buffer
        dxcallsign = helpers.bytes_to_callsign(bytes(data_in[1:7]))
        dxgrid = bytes(data_in[9:13]).rstrip(b"\x00")

        jsondata = {"type": "beacon", "status": "received", "uuid": str(uuid.uuid4()),
                    "timestamp": int(time.time()), "mycallsign": str(self.mycallsign, "utf-8"),
                    "dxcallsign": str(dxcallsign, "utf-8"), "dxgrid": str(dxgrid, "utf-8"),
                    "snr": str(static.SNR)}
        json_data_out = json.dumps(jsondata)
        sock.SOCKET_QUEUE.put(json_data_out)

        static.INFO.append("BEACON;RECEIVING")
        self.log.info(
            "[TNC] BEACON RCVD [" + str(dxcallsign, "utf-8") + "][" +
            str(dxgrid, "utf-8") + "] ", snr=static.SNR)
        helpers.add_to_heard_stations(dxcallsign, dxgrid, "BEACON", static.SNR, static.FREQ_OFFSET,
                                      static.HAMLIB_FREQUENCY)

    def transmit_cq(self):
        """
        Transmit a CQ
        Args:
            self

        Returns:
            Nothing
        """
        self.log.info("[TNC] CQ CQ CQ")
        static.INFO.append("CQ;SENDING")

        cq_frame = bytearray(14)
        cq_frame[:1] = bytes([200])
        cq_frame[1:7] = helpers.callsign_to_bytes(self.mycallsign)
        cq_frame[7:11] = helpers.encode_grid(static.MYGRID.decode("utf-8"))

        self.log.info("[TNC] ENABLE FSK", state=static.ENABLE_FSK)
        self.log.debug("[TNC] CQ Frame:", data=[cq_frame])

        if static.ENABLE_FSK:
            self.enqueue_frame_for_tx(cq_frame, c2_mode=codec2.freedv_get_mode_value_by_name("FSK_LDPC_0"))
        else:
            self.enqueue_frame_for_tx(cq_frame)

    def received_cq(self, data_in: bytes):
        """
        Called when we receive a CQ frame
        Args:
          data_in:bytes:

        Returns:
            Nothing
        """
        # here we add the received station to the heard stations buffer
        dxcallsign = helpers.bytes_to_callsign(bytes(data_in[1:7]))
        self.log.debug("[TNC] received_cq:", dxcallsign=dxcallsign)

        dxgrid = bytes(helpers.decode_grid(data_in[7:11]), "utf-8")
        static.INFO.append("CQ;RECEIVING")
        self.log.info(
            "[TNC] CQ RCVD [" + str(dxcallsign, "utf-8") + "][" +
            str(dxgrid, "utf-8") + "] ", snr=static.SNR)
        helpers.add_to_heard_stations(dxcallsign, dxgrid, "CQ CQ CQ", static.SNR, static.FREQ_OFFSET,
                                      static.HAMLIB_FREQUENCY)

        if static.RESPOND_TO_CQ:
            self.transmit_qrv()

    def transmit_qrv(self):
        """
        Called when we send a QRV frame
        Args:
          self

        Returns:
            Nothing
        """
        # Sleep a random amount of time before responding to make it more likely to be
        # heard when many stations respond. Each DATAC0 frame is 0.44 sec (440ms) in
        # duration, plus overhead. Set the wait interval to be random between 0 and 2s
        # in 0.5s increments.
        helpers.wait(randrange(0, 20, 5) / 10.0)
        static.INFO.append("QRV;SENDING")
        self.log.info("[TNC] Sending QRV!")

        qrv_frame = bytearray(14)
        qrv_frame[:1] = bytes([201])
        qrv_frame[1:7] = helpers.callsign_to_bytes(self.mycallsign)
        qrv_frame[7:11] = helpers.encode_grid(static.MYGRID.decode("utf-8"))

        self.log.info("[TNC] ENABLE FSK", state=static.ENABLE_FSK)

        if static.ENABLE_FSK:
            self.enqueue_frame_for_tx(qrv_frame, c2_mode=codec2.freedv_get_mode_value_by_name("FSK_LDPC_0"))
        else:
            self.enqueue_frame_for_tx(qrv_frame)

    def received_qrv(self, data_in: bytes):
        """
        Called when we receive a QRV frame
        Args:
          data_in:bytes:

        Returns:
            Nothing
        """
        # here we add the received station to the heard stations buffer
        dxcallsign = helpers.bytes_to_callsign(bytes(data_in[1:7]))
        dxgrid = bytes(helpers.decode_grid(data_in[7:11]), "utf-8")

        jsondata = {"type": "qrv", "status": "received", "uuid": str(uuid.uuid4()),
                    "timestamp": int(time.time()), "mycallsign": str(self.mycallsign, "utf-8"),
                    "dxcallsign": str(dxcallsign, "utf-8"), "dxgrid": str(dxgrid, "utf-8"),
                    "snr": str(static.SNR)}
        json_data_out = json.dumps(jsondata)
        sock.SOCKET_QUEUE.put(json_data_out)

        static.INFO.append("QRV;RECEIVING")
        self.log.info(
            "[TNC] QRV RCVD [" + str(dxcallsign, "utf-8") + "][" +
            str(dxgrid, "utf-8") + "] ", snr=static.SNR)
        helpers.add_to_heard_stations(dxcallsign, dxgrid, "QRV", static.SNR, static.FREQ_OFFSET,
                                      static.HAMLIB_FREQUENCY)

    # ------------ CALUCLATE TRANSFER RATES
    def calculate_transfer_rate_rx(self, rx_start_of_transmission: float, receivedbytes: int) -> list:
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
            if static.TOTAL_BYTES == 0:
                static.TOTAL_BYTES = 1
            static.ARQ_TRANSMISSION_PERCENT = min(
                int((receivedbytes * static.ARQ_COMPRESSION_FACTOR / (static.TOTAL_BYTES)) * 100), 100)

            transmissiontime = time.time() - self.rx_start_of_transmission

            if receivedbytes > 0:
                static.ARQ_BITS_PER_SECOND = int((receivedbytes * 8) / transmissiontime)
                static.ARQ_BYTES_PER_MINUTE = int((receivedbytes) / (transmissiontime / 60))

            else:
                static.ARQ_BITS_PER_SECOND = 0
                static.ARQ_BYTES_PER_MINUTE = 0
        except Exception as err:
            self.log.error(f"[TNC] calculate_transfer_rate_rx: Exception: {err}")
            static.ARQ_TRANSMISSION_PERCENT = 0.0
            static.ARQ_BITS_PER_SECOND = 0
            static.ARQ_BYTES_PER_MINUTE = 0

        return [static.ARQ_BITS_PER_SECOND,
                static.ARQ_BYTES_PER_MINUTE,
                static.ARQ_TRANSMISSION_PERCENT]

    def reset_statistics(self):
        """
        Reset statistics
        """
        # reset ARQ statistics
        static.ARQ_BYTES_PER_MINUTE_BURST = 0
        static.ARQ_BYTES_PER_MINUTE = 0
        static.ARQ_BITS_PER_SECOND_BURST = 0
        static.ARQ_BITS_PER_SECOND = 0
        static.ARQ_TRANSMISSION_PERCENT = 0
        static.TOTAL_BYTES = 0

    def calculate_transfer_rate_tx(self, tx_start_of_transmission: float, sentbytes: int,
                                   tx_buffer_length: int) -> list:
        """
        Calculate transfer rate for transmission
        Args:
          tx_start_of_transmission:float:
          sentbytes:int:
          tx_buffer_length:int:

        Returns:

        """
        try:
            static.ARQ_TRANSMISSION_PERCENT = min(int((sentbytes / tx_buffer_length) * 100), 100)

            transmissiontime = time.time() - tx_start_of_transmission

            if sentbytes > 0:
                static.ARQ_BITS_PER_SECOND = int((sentbytes * 8) / transmissiontime)  # Bits per Second
                static.ARQ_BYTES_PER_MINUTE = int((sentbytes) / (transmissiontime / 60))  # Bytes per Minute

            else:
                static.ARQ_BITS_PER_SECOND = 0
                static.ARQ_BYTES_PER_MINUTE = 0

        except Exception as err:
            self.log.error(f"[TNC] calculate_transfer_rate_tx: Exception: {err}")
            static.ARQ_TRANSMISSION_PERCENT = 0.0
            static.ARQ_BITS_PER_SECOND = 0
            static.ARQ_BYTES_PER_MINUTE = 0

        return [static.ARQ_BITS_PER_SECOND,
                static.ARQ_BYTES_PER_MINUTE,
                static.ARQ_TRANSMISSION_PERCENT]

    # ----------------------CLEANUP AND RESET FUNCTIONS
    def arq_cleanup(self):
        """
        Cleanup funktion which clears all ARQ states
        """
        self.log.debug("[TNC] arq_cleanup")

        self.received_mycall_crc = b""

        self.rx_frame_bof_received = False
        self.rx_frame_eof_received = False
        self.burst_ack = False
        self.rpt_request_received = False
        self.data_frame_ack_received = False
        static.RX_BURST_BUFFER = []
        static.RX_FRAME_BUFFER = b""
        self.burst_ack_snr = 255

        # reset modem receiving state to reduce cpu load
        modem.RECEIVE_DATAC1 = False
        modem.RECEIVE_DATAC3 = False
        # modem.RECEIVE_FSK_LDPC_0 = False
        modem.RECEIVE_FSK_LDPC_1 = False

        # reset buffer overflow counter
        static.BUFFER_OVERFLOW_COUNTER = [0, 0, 0, 0, 0]

        self.is_IRS = False
        self.burst_nack = False
        self.burst_nack_counter = 0
        self.frame_received_counter = 0
        self.speed_level = len(self.mode_list) - 1
        static.ARQ_SPEED_LEVEL = self.speed_level

        # low bandwidth mode indicator
        self.received_LOW_BANDWIDTH_MODE = False

        # reset retry counter for rx channel / burst
        self.n_retries_per_burst = 0

        if not static.ARQ_SESSION:
            static.TNC_STATE = "IDLE"

        static.ARQ_STATE = False
        self.arq_file_transfer = False

        static.BEACON_PAUSE = False

    def arq_reset_ack(self, state: bool):
        """
        Funktion for resetting acknowledge states
        Args:
          state:bool:

        Returns:

        """
        self.burst_ack = state
        self.rpt_request_received = state
        self.data_frame_ack_received = state

    def set_listening_modes(self, mode):
        """
        Function for setting the data modes we are listening to for saving cpu power

        Args:
          mode:

        Returns:

        """
        # set modes we want to listen to
        mode_name = codec2.freedv_get_mode_name_by_value(mode)

        if mode_name == "datac1":
            modem.RECEIVE_DATAC1 = True
            self.log.debug("[TNC] Changing listening data mode", mode="datac1")
        elif mode_name == "datac3":
            modem.RECEIVE_DATAC3 = True
            self.log.debug("[TNC] Changing listening data mode", mode="datac3")
        elif mode_name == "fsk_ldpc_1":
            modem.RECEIVE_FSK_LDPC_1 = True
            self.log.debug("[TNC] Changing listening data mode", mode="fsk_ldpc_1")
        elif mode_name == "allmodes":
            modem.RECEIVE_DATAC1 = True
            modem.RECEIVE_DATAC3 = True
            modem.RECEIVE_FSK_LDPC_1 = True
            self.log.debug("[TNC] Changing listening data mode", mode="datac1/datac3/fsk_ldpc")

    # ------------------------- WATCHDOG FUNCTIONS FOR TIMER
    def watchdog(self):
        """Author: DJ2LS

        Watchdog master function. From here, call the watchdogs

        Args:

        Returns:

        """
        while True:
            time.sleep(0.1)
            self.data_channel_keep_alive_watchdog()
            self.burst_watchdog()
            self.arq_session_keep_alive_watchdog()

    def burst_watchdog(self):
        """
        watchdog which checks if we are running into a connection timeout
        DATA BURST
        """
        # IRS SIDE
        # TODO: We need to redesign this part for cleaner state handling
        # return only if not ARQ STATE and not ARQ SESSION STATE as they are different use cases
        if not static.ARQ_STATE and static.ARQ_SESSION_STATE != "connected" or not self.is_IRS:
            return
        # we want to reach this state only if connected ( == return above not called )
        if self.data_channel_last_received + self.time_list[self.speed_level] > time.time():
            # print((self.data_channel_last_received + self.time_list[self.speed_level])-time.time())
            pass
        else:
            self.log.warning("[TNC] Frame timeout", attempt=self.n_retries_per_burst,
                max_attempts=self.rx_n_max_retries_per_burst, speed_level=self.speed_level)
            self.frame_received_counter = 0
            self.burst_nack_counter += 1
            if self.burst_nack_counter >= 2:
                self.speed_level -= 1
                # print(self.burst_nack_counter)
                # print(self.speed_level)
                static.ARQ_SPEED_LEVEL = self.speed_level
                self.burst_nack_counter = 0
            if self.speed_level <= 0:
                self.speed_level = 0
                static.ARQ_SPEED_LEVEL = self.speed_level

            # updated modes we are listening to
            self.set_listening_modes(self.mode_list[self.speed_level])

            self.send_burst_nack_frame_watchdog(0)  # Why not pass `snr`?

            self.data_channel_last_received = time.time()
            self.n_retries_per_burst += 1

        if self.n_retries_per_burst >= self.rx_n_max_retries_per_burst:
            self.stop_transmission()
            self.arq_cleanup()

    def data_channel_keep_alive_watchdog(self):
        """
        watchdog which checks if we are running into a connection timeout
        DATA CHANNEL
        """
        # and not static.ARQ_SEND_KEEP_ALIVE:
        if static.ARQ_STATE and static.TNC_STATE == "BUSY":
            time.sleep(0.01)
            if self.data_channel_last_received + self.transmission_timeout > time.time():
                time.sleep(0.01)
                # print(self.data_channel_last_received + self.transmission_timeout - time.time())
                # pass
            else:
                self.data_channel_last_received = 0
                self.log.info(
                    "[TNC] DATA [" + str(self.mycallsign, "utf-8") +
                    "]<<T>>[" + str(static.DXCALLSIGN, "utf-8") + "]")
                static.INFO.append("ARQ;RECEIVING;FAILED")
                if not TESTMODE:
                    self.arq_cleanup()

    def arq_session_keep_alive_watchdog(self):
        """
        watchdog which checks if we are running into a connection timeout
        ARQ SESSION
        """
        if static.ARQ_SESSION and static.TNC_STATE == "BUSY" and not self.arq_file_transfer:
            if self.arq_session_last_received + self.arq_session_timeout > time.time():
                time.sleep(0.01)
            else:
                self.log.info(
                    "[TNC] SESSION [" + str(self.mycallsign, "utf-8") +
                    "]<<T>>[" + str(static.DXCALLSIGN, "utf-8") + "]")
                static.INFO.append("ARQ;SESSION;TIMEOUT")
                self.close_session()

    def heartbeat(self):
        """
        heartbeat thread which auto resumes the heartbeat signal within an arq session
        """
        while True:
            time.sleep(0.01)
            if static.ARQ_SESSION and self.IS_ARQ_SESSION_MASTER and static.ARQ_SESSION_STATE == "connected" and not self.arq_file_transfer:
                time.sleep(1)
                self.transmit_session_heartbeat()
                time.sleep(2)

    def send_test_frame(self):
        modem.MODEM_TRANSMIT_QUEUE.put([12, 1, 0, [bytearray(126)]])
