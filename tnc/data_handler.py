# -*- coding: UTF-8 -*-
"""
Created on Sun Dec 27 20:43:40 2020

@author: DJ2LS
"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init

import base64
import sys
import threading
import time
import uuid
import zlib
from random import randrange# , randbytes

import codec2
import helpers
import modem
import numpy as np
import sock
import static
import structlog
import ujson as json
from codec2 import FREEDV_MODE
from exceptions import NoCallsign
from queues import DATA_QUEUE_RECEIVED, DATA_QUEUE_TRANSMIT, RX_BUFFER
from static import FRAME_TYPE as FR_TYPE

TESTMODE = False


class DATA:
    """Terminal Node Controller for FreeDATA"""

    log = structlog.get_logger("DATA")

    def __init__(self) -> None:
        # Initial call sign. Will be overwritten later
        self.mycallsign = static.MYCALLSIGN
        self.dxcallsign = static.DXCALLSIGN

        self.data_queue_transmit = DATA_QUEUE_TRANSMIT
        self.data_queue_received = DATA_QUEUE_RECEIVED

        # length of signalling frame
        self.length_sig0_frame = 14
        self.length_sig1_frame = 14

        # hold session id
        self.session_id = bytes(1)

        # ------- ARQ SESSION
        self.arq_file_transfer = False
        self.IS_ARQ_SESSION_MASTER = False
        self.arq_session_last_received = 0
        self.arq_session_timeout = 30
        self.session_connect_max_retries = 15

        # actual n retries of burst
        self.tx_n_retry_of_burst = 0

        self.transmission_uuid = ""

        self.data_channel_last_received = 0.0  # time of last "live sign" of a frame
        self.burst_ack_snr = 0  # SNR from received burst ack frames

        # Flag to indicate if we received an acknowledge frame for a burst
        self.burst_ack = False
        # Flag to indicate if we received an acknowledge frame for a data frame
        self.data_frame_ack_received = False
        # Flag to indicate if we received an request for repeater frames
        self.rpt_request_received = False
        self.rpt_request_buffer = []  # requested frames, saved in a list
        self.rx_start_of_transmission = 0  # time of transmission start

        # 3 bytes for the BOF Beginning of File indicator in a data frame
        self.data_frame_bof = b"BOF"
        # 3 bytes for the EOF End of File indicator in a data frame
        self.data_frame_eof = b"EOF"

        self.tx_n_max_retries_per_burst = 50
        self.rx_n_max_retries_per_burst = 50
        self.n_retries_per_burst = 0

        # Flag to indicate if we recevied a low bandwidth mode channel opener
        self.received_LOW_BANDWIDTH_MODE = False

        self.data_channel_max_retries = 15
        self.datachannel_timeout = False

        # -------------- AVAILABLE MODES START-----------
        # IMPORTANT: LISTS MUST BE OF EQUAL LENGTH

        # --------------------- LOW BANDWIDTH

        # List of codec2 modes to use in "low bandwidth" mode.
        self.mode_list_low_bw = [
            FREEDV_MODE.datac3.value,
        ]
        # List for minimum SNR operating level for the corresponding mode in self.mode_list
        self.snr_list_low_bw = [0]
        # List for time to wait for corresponding mode in seconds
        self.time_list_low_bw = [6]

        # --------------------- HIGH BANDWIDTH

        # List of codec2 modes to use in "high bandwidth" mode.
        self.mode_list_high_bw = [
            FREEDV_MODE.datac3.value,
            FREEDV_MODE.datac1.value,
        ]
        # List for minimum SNR operating level for the corresponding mode in self.mode_list
        self.snr_list_high_bw = [0, 3]
        # List for time to wait for corresponding mode in seconds
        self.time_list_high_bw = [6, 7]
        # -------------- AVAILABLE MODES END-----------

        # Mode list for selecting between low bandwidth ( 500Hz ) and modes with higher bandwidth
        # but ability to fall back to low bandwidth modes if needed.
        if static.LOW_BANDWIDTH_MODE:
            # List of codec2 modes to use in "low bandwidth" mode.
            self.mode_list = self.mode_list_low_bw
            # list of times to wait for corresponding mode in seconds
            self.time_list = self.time_list_low_bw

        else:
            # List of codec2 modes to use in "high bandwidth" mode.
            self.mode_list = self.mode_list_high_bw
            # list of times to wait for corresponding mode in seconds
            self.time_list = self.time_list_high_bw

        self.speed_level = len(self.mode_list) - 1  # speed level for selecting mode
        static.ARQ_SPEED_LEVEL = self.speed_level

        self.is_IRS = False
        self.burst_nack = False
        self.burst_nack_counter = 0
        self.frame_received_counter = 0

        self.rx_frame_bof_received = False
        self.rx_frame_eof_received = False

        # TIMEOUTS
        self.burst_ack_timeout_seconds = 3.0  # timeout for burst  acknowledges
        self.data_frame_ack_timeout_seconds = 3.0  # timeout for data frame acknowledges
        self.rpt_ack_timeout_seconds = 3.0  # timeout for rpt frame acknowledges
        self.transmission_timeout = 180  # transmission timeout in seconds

        # Dictionary of functions and log messages used in process_data
        # instead of a long series of if-elif-else statements.
        self.rx_dispatcher = {
            FR_TYPE.ARQ_DC_OPEN_ACK_N.value: (
                self.arq_received_channel_is_open,
                "ARQ OPEN ACK (Narrow)",
            ),
            FR_TYPE.ARQ_DC_OPEN_ACK_W.value: (
                self.arq_received_channel_is_open,
                "ARQ OPEN ACK (Wide)",
            ),
            FR_TYPE.ARQ_DC_OPEN_N.value: (
                self.arq_received_data_channel_opener,
                "ARQ Data Channel Open (Narrow)",
            ),
            FR_TYPE.ARQ_DC_OPEN_W.value: (
                self.arq_received_data_channel_opener,
                "ARQ Data Channel Open (Wide)",
            ),
            FR_TYPE.ARQ_SESSION_CLOSE.value: (
                self.received_session_close,
                "ARQ CLOSE SESSION",
            ),
            FR_TYPE.ARQ_SESSION_HB.value: (
                self.received_session_heartbeat,
                "ARQ HEARTBEAT",
            ),
            FR_TYPE.ARQ_SESSION_OPEN.value: (
                self.received_session_opener,
                "ARQ OPEN SESSION",
            ),
            FR_TYPE.ARQ_STOP.value: (self.received_stop_transmission, "ARQ STOP TX"),
            FR_TYPE.BEACON.value: (self.received_beacon, "BEACON"),
            FR_TYPE.BURST_ACK.value: (self.burst_ack_nack_received, "BURST ACK"),
            FR_TYPE.BURST_NACK.value: (self.burst_ack_nack_received, "BURST NACK"),
            FR_TYPE.CQ.value: (self.received_cq, "CQ"),
            FR_TYPE.FR_ACK.value: (self.frame_ack_received, "FRAME ACK"),
            FR_TYPE.FR_NACK.value: (self.frame_nack_received, "FRAME NACK"),
            FR_TYPE.FR_REPEAT.value: (self.burst_rpt_received, "REPEAT REQUEST"),
            FR_TYPE.PING_ACK.value: (self.received_ping_ack, "PING ACK"),
            FR_TYPE.PING.value: (self.received_ping, "PING"),
            FR_TYPE.QRV.value: (self.received_qrv, "QRV"),
        }
        self.command_dispatcher = {
            #"CONNECT": (self.arq_session_handler, "CONNECT"),
            "CQ": (self.transmit_cq, "CQ"),
            "DISCONNECT": (self.close_session, "DISCONNECT"),
            "SEND_TEST_FRAME": (self.send_test_frame, "TEST"),
            "STOP": (self.stop_transmission, "STOP"),
        }

        # Start worker and watchdog threads
        worker_thread_transmit = threading.Thread(
            target=self.worker_transmit, name="worker thread transmit", daemon=True
        )
        worker_thread_transmit.start()

        worker_thread_receive = threading.Thread(
            target=self.worker_receive, name="worker thread receive", daemon=True
        )
        worker_thread_receive.start()

        # START THE THREAD FOR THE TIMEOUT WATCHDOG
        watchdog_thread = threading.Thread(
            target=self.watchdog, name="watchdog", daemon=True
        )
        watchdog_thread.start()

        arq_session_thread = threading.Thread(
            target=self.heartbeat, name="watchdog", daemon=True
        )
        arq_session_thread.start()

        self.beacon_interval = 0
        self.beacon_thread = threading.Thread(
            target=self.run_beacon, name="watchdog", daemon=True
        )
        self.beacon_thread.start()

    def worker_transmit(self) -> None:
        """Dispatch incoming UI instructions for transmitting operations"""
        while True:
            data = self.data_queue_transmit.get()

            # Dispatch commands known to command_dispatcher
            if data[0] in self.command_dispatcher:
                self.log.debug(f"[TNC] TX {self.command_dispatcher[data[0]][1]}...")
                self.command_dispatcher[data[0]][0]()

            # Dispatch commands that need more arguments.
            elif data[0] == "CONNECT":
                # [1] mycallsign
                # [2] dxcallsign
                # [3] attempts
                self.arq_session_handler(data[1], data[2], data[3])

            elif data[0] == "PING":
                # [1] mycallsign
                # [2] dxcallsign
                self.transmit_ping(data[1], data[2])

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
                # [6] dxcallsign with ssid
                # [7] attempts
                self.open_dc_and_transmit(data[1], data[2], data[3], data[4], data[5], data[6], data[7])

            else:
                self.log.error(
                    "[TNC] worker_transmit: received invalid command:", data=data
                )

    def worker_receive(self) -> None:
        """Queue received data for processing"""
        while True:
            data = self.data_queue_received.get()
            # [0] bytes
            # [1] freedv instance
            # [2] bytes_per_frame
            self.process_data(
                bytes_out=data[0], freedv=data[1], bytes_per_frame=data[2]
            )

    def process_data(self, bytes_out, freedv, bytes_per_frame: int) -> None:
        """
        Process incoming data and decide what to do with the frame.

        Args:
          bytes_out:
          freedv:
          bytes_per_frame:

        Returns:

        """
        self.log.debug(
            "[TNC] process_data:", n_retries_per_burst=self.n_retries_per_burst
        )

        # Process data only if broadcast or we are the receiver
        # bytes_out[1:4] == callsign check for signalling frames,
        # bytes_out[2:5] == transmission
        # we could also create an own function, which returns True.
        frametype = int.from_bytes(bytes(bytes_out[:1]), "big")

        # check for callsign CRC
        _valid1, _ = helpers.check_callsign(self.mycallsign, bytes(bytes_out[1:4]))
        _valid2, _ = helpers.check_callsign(self.mycallsign, bytes(bytes_out[2:5]))

        # check for session ID
        # signalling frames
        _valid3 = helpers.check_session_id(self.session_id, bytes(bytes_out[1:2]))
        # arq data frames
        _valid4 = helpers.check_session_id(self.session_id, bytes(bytes_out[2:3]))
        if (
                _valid1
                or _valid2
                or _valid3
                or _valid4
                or frametype
                in [
                        FR_TYPE.CQ.value,
                        FR_TYPE.QRV.value,
                        FR_TYPE.PING.value,
                        FR_TYPE.BEACON.value,
                ]
        ):

            # CHECK IF FRAMETYPE IS BETWEEN 10 and 50 ------------------------
            # frame = frametype - 10
            # n_frames_per_burst = int.from_bytes(bytes(bytes_out[1:2]), "big")

            # Dispatch activity based on received frametype
            if frametype in self.rx_dispatcher:
                # Process frames "known" by rx_dispatcher
                # self.log.debug(f"[TNC] {self.rx_dispatcher[frametype][1]} RECEIVED....")
                self.rx_dispatcher[frametype][0](bytes_out[:-2])

            # Process frametypes requiring a different set of arguments.
            elif FR_TYPE.BURST_51.value >= frametype >= FR_TYPE.BURST_01.value:
                # get snr of received data
                # FIXME: find a fix for this - after moving to classes, this no longer works
                # snr = self.calculate_snr(freedv)
                snr = static.SNR
                self.log.debug("[TNC] RX SNR", snr=snr)
                # send payload data to arq checker without CRC16
                self.arq_data_received(
                    bytes(bytes_out[:-2]), bytes_per_frame, snr, freedv
                )

                # if we received the last frame of a burst or the last remaining rpt frame, do a modem unsync
                # if static.RX_BURST_BUFFER.count(None) <= 1 or (frame+1) == n_frames_per_burst:
                #    self.log.debug(f"[TNC] LAST FRAME OF BURST --> UNSYNC {frame+1}/{n_frames_per_burst}")
                #    self.c_lib.freedv_set_sync(freedv, 0)

            # TESTFRAMES
            elif frametype == FR_TYPE.TEST_FRAME.value:
                self.log.debug("[TNC] TESTFRAME RECEIVED", frame=bytes_out[:])

            # Unknown frame type
            else:
                self.log.warning(
                    "[TNC] ARQ - other frame type", frametype=FR_TYPE(frametype).name
                )

        else:
            # for debugging purposes to receive all data
            self.log.debug(
                "[TNC] Foreign frame received",
                frame=bytes_out[:-2].hex(),
                frame_type=FR_TYPE(int.from_bytes(bytes_out[:1], byteorder="big")).name,
            )

    def enqueue_frame_for_tx(
            self,
            frame_to_tx,# : list[bytearray], # this causes a crash on python 3.7
            c2_mode=FREEDV_MODE.datac0.value,
            copies=1,
            repeat_delay=0,
    ) -> None:
        """
        Send (transmit) supplied frame to TNC

        :param frame_to_tx: Frame data to send
        :type frame_to_tx: list of bytearrays
        :param c2_mode: Codec2 mode to use, defaults to 14 (datac0)
        :type c2_mode: int, optional
        :param copies: Number of frame copies to send, defaults to 1
        :type copies: int, optional
        :param repeat_delay: Delay time before sending repeat frame, defaults to 0
        :type repeat_delay: int, optional
        """
        self.log.debug("[TNC] enqueue_frame_for_tx", c2_mode=FREEDV_MODE(c2_mode).name)

        # Set the TRANSMITTING flag before adding an object to the transmit queue
        # TODO: This is not that nice, we could improve this somehow
        static.TRANSMITTING = True
        modem.MODEM_TRANSMIT_QUEUE.put([c2_mode, copies, repeat_delay, frame_to_tx])

        # Wait while transmitting
        while static.TRANSMITTING:
            threading.Event().wait(0.01)

    def send_data_to_socket_queue(self, **jsondata):
        """
        Send information to the UI via JSON and the sock.SOCKET_QUEUE.

        Args:
          Dictionary containing the data to be sent, in the format:
          key=value, for each item. E.g.:
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="received",
                status="success",
                uuid=self.transmission_uuid,
                timestamp=timestamp,
                mycallsign=str(self.mycallsign, "UTF-8"),
                dxcallsign=str(static.DXCALLSIGN, "UTF-8"),
                dxgrid=str(static.DXGRID, "UTF-8"),
                data=base64_data,
            )
        """

        # add mycallsign and dxcallsign to network message if they not exist
        # and make sure we are not overwrite them if they exist
        try:
            if not "mycallsign" in jsondata:
                jsondata["mycallsign"] = str(self.mycallsign, "UTF-8")
            if not "dxcallsign" in jsondata:
                jsondata["dxcallsign"] = str(static.DXCALLSIGN, "UTF-8")
        except Exception as e:
            self.log.debug("[TNC] error adding callsigns to network message", e=e)

        # run json dumps
        json_data_out = json.dumps(jsondata)

        self.log.debug("[TNC] send_data_to_socket_queue:", jsondata=json_data_out)
        # finally push data to our network queue
        sock.SOCKET_QUEUE.put(json_data_out)

    def send_ident_frame(self, transmit) -> None:
        """Build and send IDENT frame """
        ident_frame = bytearray(self.length_sig1_frame)
        ident_frame[:1] = bytes([FR_TYPE.IDENT.value])
        ident_frame[1:self.length_sig1_frame] = self.mycallsign

        # Transmit frame
        if transmit:
            self.enqueue_frame_for_tx([ident_frame], c2_mode=FREEDV_MODE.datac0.value)
        else:
            return ident_frame

    def send_burst_ack_frame(self, snr) -> None:
        """Build and send ACK frame for burst DATA frame"""



        ack_frame = bytearray(self.length_sig1_frame)
        ack_frame[:1] = bytes([FR_TYPE.BURST_ACK.value])
        # ack_frame[1:4] = static.DXCALLSIGN_CRC
        # ack_frame[4:7] = static.MYCALLSIGN_CRC
        ack_frame[1:2] = self.session_id
        ack_frame[2:3] = helpers.snr_to_bytes(snr)
        ack_frame[3:4] = bytes([int(self.speed_level)])

        # Transmit frame
        self.enqueue_frame_for_tx([ack_frame], c2_mode=FREEDV_MODE.sig1.value)

    def send_data_ack_frame(self, snr) -> None:
        """Build and send ACK frame for received DATA frame"""

        ack_frame = bytearray(self.length_sig1_frame)
        ack_frame[:1] = bytes([FR_TYPE.FR_ACK.value])
        ack_frame[1:2] = self.session_id
        ack_frame[2:3] = helpers.snr_to_bytes(snr)
        # ack_frame[1:4] = static.DXCALLSIGN_CRC
        # ack_frame[4:7] = static.MYCALLSIGN_CRC
        # ack_frame[7:8] = bytes([int(snr)])
        # ack_frame[8:9] = bytes([int(self.speed_level)])

        # Transmit frame
        # TODO: Do we have to send , self.send_ident_frame(False) ?
        # self.enqueue_frame_for_tx([ack_frame, self.send_ident_frame(False)], c2_mode=FREEDV_MODE.sig1.value, copies=3, repeat_delay=0)
        self.enqueue_frame_for_tx([ack_frame], c2_mode=FREEDV_MODE.sig1.value, copies=6, repeat_delay=0)

    def send_retransmit_request_frame(self, freedv) -> None:
        # check where a None is in our burst buffer and do frame+1, because lists start at 0
        # FIXME: Check to see if there's a `frame - 1` in the receive portion. Remove both if there is.
        missing_frames = [
            frame + 1
            for frame, element in enumerate(static.RX_BURST_BUFFER)
            if element is None
        ]

        # set n frames per burst to modem
        # this is an idea, so it's not getting lost....
        # we need to work on this
        codec2.api.freedv_set_frames_per_burst(freedv, len(missing_frames))

        # TODO: Trim `missing_frames` bytesarray to [7:13] (6) frames, if it's larger.
        # TODO: Instead of using int we could use a binary flag
        # then create a repeat frame
        rpt_frame = bytearray(self.length_sig1_frame)
        rpt_frame[:1] = bytes([FR_TYPE.FR_REPEAT.value])
        rpt_frame[1:2] = self.session_id
        # rpt_frame[1:4] = static.DXCALLSIGN_CRC
        # rpt_frame[4:7] = static.MYCALLSIGN_CRC
        # rpt_frame[7:13] = missing_frames

        self.log.info("[TNC] ARQ | RX | Requesting", frames=missing_frames)
        # Transmit frame
        self.enqueue_frame_for_tx([rpt_frame], c2_mode=FREEDV_MODE.sig1.value, copies=1, repeat_delay=0)

    def send_burst_nack_frame(self, snr: bytes) -> None:
        """Build and send NACK frame for received DATA frame"""

        nack_frame = bytearray(self.length_sig1_frame)
        nack_frame[:1] = bytes([FR_TYPE.FR_NACK.value])
        nack_frame[1:2] = self.session_id
        # nack_frame[1:4] = static.DXCALLSIGN_CRC
        # nack_frame[4:7] = static.MYCALLSIGN_CRC
        nack_frame[2:3] = helpers.snr_to_bytes(snr)
        nack_frame[3:4] = bytes([int(self.speed_level)])

        # TRANSMIT NACK FRAME FOR BURST
        # TODO: Do we have to send ident frame?
        # self.enqueue_frame_for_tx([ack_frame, self.send_ident_frame(False)], c2_mode=FREEDV_MODE.sig1.value, copies=3, repeat_delay=0)
        self.enqueue_frame_for_tx([nack_frame], c2_mode=FREEDV_MODE.sig1.value, copies=6, repeat_delay=0)
    def send_burst_nack_frame_watchdog(self, snr: bytes) -> None:
        """Build and send NACK frame for watchdog timeout"""

        nack_frame = bytearray(self.length_sig1_frame)
        nack_frame[:1] = bytes([FR_TYPE.BURST_NACK.value])
        nack_frame[1:2] = self.session_id
        # nack_frame[1:4] = static.DXCALLSIGN_CRC
        # nack_frame[4:7] = static.MYCALLSIGN_CRC
        nack_frame[2:3] = helpers.snr_to_bytes(snr)
        nack_frame[3:4] = bytes([int(self.speed_level)])

        # TRANSMIT NACK FRAME FOR BURST
        self.enqueue_frame_for_tx([nack_frame], c2_mode=FREEDV_MODE.sig1.value, copies=1, repeat_delay=0)

    def send_disconnect_frame(self) -> None:
        """Build and send a disconnect frame"""
        disconnection_frame = bytearray(self.length_sig1_frame)
        disconnection_frame[:1] = bytes([FR_TYPE.ARQ_SESSION_CLOSE.value])
        disconnection_frame[1:2] = self.session_id
        disconnection_frame[2:5] = static.DXCALLSIGN_CRC
        # TODO: Needed? disconnection_frame[7:13] = helpers.callsign_to_bytes(self.mycallsign)
        # self.enqueue_frame_for_tx([disconnection_frame, self.send_ident_frame(False)], c2_mode=FREEDV_MODE.sig0.value, copies=5, repeat_delay=0)
        # TODO: We need to add the ident frame feature with a seperate PR after publishing latest protocol
        # TODO: We need to wait some time between last arq related signalling frame and ident frame
        # TODO: Maybe about 500ms - 1500ms to avoid confusion and too much PTT toggles
        self.enqueue_frame_for_tx([disconnection_frame], c2_mode=FREEDV_MODE.sig0.value, copies=6, repeat_delay=0)

    def arq_data_received(
            self, data_in: bytes, bytes_per_frame: int, snr: float, freedv
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
        data_in = bytes(data_in)

        # TODO: this seems not to work anymore
        # get received crc for different mycall ssids
        # check if callsign ssid override
        # _, mycallsign = helpers.check_callsign(
        #    self.mycallsign, data_in[2:5]
        # )
        # attempt fixing this
        mycallsign = self.mycallsign

        # only process data if we are in ARQ and BUSY state else return to quit
        if not static.ARQ_STATE and static.TNC_STATE != "BUSY":
            return

        self.arq_file_transfer = True

        static.TNC_STATE = "BUSY"
        static.ARQ_STATE = True

        # Update data_channel timestamp
        self.data_channel_last_received = int(time.time())

        # Extract some important data from the frame
        # Get sequence number of burst frame
        rx_n_frame_of_burst = int.from_bytes(bytes(data_in[:1]), "big") - 10
        # Get number of bursts from received frame
        rx_n_frames_per_burst = int.from_bytes(bytes(data_in[1:2]), "big")

        # The RX burst buffer needs to have a fixed length filled with "None".
        # We need this later for counting the "Nones" to detect missing data.
        # Check if burst buffer has expected length else create it
        if len(static.RX_BURST_BUFFER) != rx_n_frames_per_burst:
            static.RX_BURST_BUFFER = [None] * rx_n_frames_per_burst

        # Append data to rx burst buffer
        # [frame_type][n_frames_per_burst][CRC24][CRC24]
        # static.RX_BURST_BUFFER[rx_n_frame_of_burst] = data_in[8:]  # type: ignore
        static.RX_BURST_BUFFER[rx_n_frame_of_burst] = data_in[3:]  # type: ignore

        self.log.debug("[TNC] static.RX_BURST_BUFFER", buffer=static.RX_BURST_BUFFER)

        helpers.add_to_heard_stations(
            static.DXCALLSIGN,
            static.DXGRID,
            "DATA-CHANNEL",
            snr,
            static.FREQ_OFFSET,
            static.HAMLIB_FREQUENCY,
        )

        # Check if we received all frames in the burst by checking if burst buffer has no more "Nones"
        # This is the ideal case because we received all data
        if None not in static.RX_BURST_BUFFER:
            # then iterate through burst buffer and stick the burst together
            # the temp burst buffer is needed for checking, if we already received data
            temp_burst_buffer = b""
            for value in static.RX_BURST_BUFFER:
                # static.RX_FRAME_BUFFER += static.RX_BURST_BUFFER[i]
                temp_burst_buffer += bytes(value)  # type: ignore

            # if frame buffer ends not with the current frame, we are going to append new data
            # if data already exists, we received the frame correctly,
            # but the ACK frame didn't receive its destination (ISS)
            if static.RX_FRAME_BUFFER.endswith(temp_burst_buffer):
                self.log.info(
                    "[TNC] ARQ | RX | Frame already received - sending ACK again"
                )
                static.RX_BURST_BUFFER = []

            else:
                # Here we are going to search for our data in the last received bytes.
                # This reduces the chance we will lose the entire frame in the case of signalling frame loss

                # static.RX_FRAME_BUFFER --> existing data
                # temp_burst_buffer --> new data
                # search_area --> area where we want to search
                search_area = 510 - 3  # (3 bytes arq frame header)

                search_position = len(static.RX_FRAME_BUFFER) - search_area
                # find position of data. returns -1 if nothing found in area else >= 0
                # we are beginning from the end, so if data exists twice or more,
                # only the last one should be replaced
                get_position = static.RX_FRAME_BUFFER[search_position:].rfind(
                    temp_burst_buffer
                )
                # if we find data, replace it at this position with the new data and strip it
                if get_position >= 0:
                    static.RX_FRAME_BUFFER = static.RX_FRAME_BUFFER[
                                             : search_position + get_position
                                             ]
                    static.RX_FRAME_BUFFER += temp_burst_buffer
                    self.log.warning(
                        "[TNC] ARQ | RX | replacing existing buffer data",
                        area=search_area,
                        pos=get_position,
                    )
                # If we don't find data in this range, we really have new data and going to replace it
                else:
                    static.RX_FRAME_BUFFER += temp_burst_buffer
                    self.log.debug("[TNC] ARQ | RX | appending data to buffer")

            # Check if we didn't receive a BOF and EOF yet to avoid sending
            # ack frames if we already received all data
            if (
                    not self.rx_frame_bof_received
                    and not self.rx_frame_eof_received
                    and data_in.find(self.data_frame_eof) < 0
            ):

                self.frame_received_counter += 1
                # try increasing speed level only if we had two successful decodes
                if self.frame_received_counter >= 2:
                    self.frame_received_counter = 0

                    # make sure new speed level isn't higher than available modes
                    new_speed_level = min(self.speed_level + 1, len(self.mode_list) - 1)
                    # check if actual snr is higher than minimum snr for next mode
                    if static.SNR >= self.snr_list[new_speed_level]:
                        self.speed_level = new_speed_level
                    else:
                        self.log.info("[TNC] ARQ | increasing speed level not possible because of SNR limit",
                                         given_snr=static.SNR,
                                         needed_snr=self.snr_list[new_speed_level]
                                         )
                    static.ARQ_SPEED_LEVEL = self.speed_level

                # Update modes we are listening to
                self.set_listening_modes(False, True, self.mode_list[self.speed_level])

                # Create and send ACK frame
                self.log.info("[TNC] ARQ | RX | SENDING ACK")
                self.send_burst_ack_frame(snr)

                # Reset n retries per burst counter
                self.n_retries_per_burst = 0

                # calculate statistics
                self.calculate_transfer_rate_rx(
                    self.rx_start_of_transmission, len(static.RX_FRAME_BUFFER)
                )

                # send a network message with information
                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    arq="transmission",
                    status="receiving",
                    uuid=self.transmission_uuid,
                    percent=static.ARQ_TRANSMISSION_PERCENT,
                    bytesperminute=static.ARQ_BYTES_PER_MINUTE,
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                )

        elif rx_n_frame_of_burst == rx_n_frames_per_burst - 1:
            # We have "Nones" in our rx buffer,
            # Check if we received last frame of burst - this is an indicator for missed frames.
            # With this way of doing this, we always MUST receive the last
            # frame of a burst otherwise the entire burst is lost
            # TODO: See if a timeout on the send side with re-transmit last burst would help.
            self.log.debug(
                "[TNC] all frames in burst received:",
                frame=rx_n_frame_of_burst,
                frames=rx_n_frames_per_burst,
            )
            self.send_retransmit_request_frame(freedv)
            self.calculate_transfer_rate_rx(
                self.rx_start_of_transmission, len(static.RX_FRAME_BUFFER)
            )

        # Should never reach this point
        else:
            self.log.error(
                "[TNC] data_handler: Should not reach this point...",
                frame=rx_n_frame_of_burst,
                frames=rx_n_frames_per_burst,
            )

        # We have a BOF and EOF flag in our data. If we received both we received our frame.
        # In case of loosing data, but we received already a BOF and EOF we need to make sure, we
        # received the complete last burst by checking it for Nones
        bof_position = static.RX_FRAME_BUFFER.find(self.data_frame_bof)
        eof_position = static.RX_FRAME_BUFFER.find(self.data_frame_eof)

        # get total bytes per transmission information as soon we received a frame with a BOF

        if bof_position >= 0:
            payload = static.RX_FRAME_BUFFER[
                      bof_position + len(self.data_frame_bof): eof_position
                      ]
            frame_length = int.from_bytes(payload[4:8], "big")  # 4:8 4bytes
            static.TOTAL_BYTES = frame_length
            compression_factor = int.from_bytes(payload[8:9], "big")  # 4:8 4bytes
            # limit to max value of 255
            compression_factor = np.clip(compression_factor, 0, 255)
            static.ARQ_COMPRESSION_FACTOR = compression_factor / 10
            self.calculate_transfer_rate_rx(
                self.rx_start_of_transmission, len(static.RX_FRAME_BUFFER)
            )

        if (
                bof_position >= 0
                and eof_position > 0
                and None not in static.RX_BURST_BUFFER
        ):
            self.log.debug(
                "[TNC] arq_data_received:",
                bof_position=bof_position,
                eof_position=eof_position,
            )
            self.rx_frame_bof_received = True
            self.rx_frame_eof_received = True

            # Extract raw data from buffer
            payload = static.RX_FRAME_BUFFER[
                      bof_position + len(self.data_frame_bof): eof_position
                      ]
            # Get the data frame crc
            data_frame_crc = payload[:4]  # 0:4 = 4 bytes
            # Get the data frame length
            frame_length = int.from_bytes(payload[4:8], "big")  # 4:8 = 4 bytes
            static.TOTAL_BYTES = frame_length
            # 8:9 = compression factor

            data_frame = payload[9:]
            data_frame_crc_received = helpers.get_crc_32(data_frame)

            # Check if data_frame_crc is equal with received crc
            if data_frame_crc == data_frame_crc_received:
                self.log.info("[TNC] ARQ | RX | DATA FRAME SUCCESSFULLY RECEIVED")

                # Decompress the data frame
                data_frame_decompressed = zlib.decompress(data_frame)
                static.ARQ_COMPRESSION_FACTOR = len(data_frame_decompressed) / len(
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
                    RX_BUFFER.maxsize = int(static.RX_BUFFER_SIZE)
                else:
                    # if full, free space by getting an item
                    self.log.info(
                        "[TNC] ARQ | RX | RX_BUFFER FULL - dropping old data",
                        buffer_size=RX_BUFFER.qsize(),
                        maxsize=int(static.RX_BUFFER_SIZE)
                    )
                    RX_BUFFER.get()

                # add item to RX_BUFFER
                self.log.info(
                    "[TNC] ARQ | RX | saving data to rx buffer",
                    buffer_size=RX_BUFFER.qsize() + 1,
                    maxsize=RX_BUFFER.maxsize
                )
                try:
                    RX_BUFFER.put(
                        [
                            self.transmission_uuid,
                            timestamp,
                            static.DXCALLSIGN,
                            static.DXGRID,
                            base64_data,
                        ]
                    )
                except Exception as e:
                    # File "/usr/lib/python3.7/queue.py", line 133, in put
                    #    if self.maxsize > 0
                    # TypeError: '>' not supported between instances of 'str' and 'int'
                    #
                    # Occurs on Raspberry Pi and Python 3.7
                    self.log.error(
                        "[TNC] ARQ | RX | error occurred when saving data!",
                        e=e,
                        uuid = self.transmission_uuid,
                        timestamp = timestamp,
                        dxcall = static.DXCALLSIGN,
                        dxgrid = static.DXGRID,
                        data = base64_data
                    )

                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    arq="transmission",
                    status="received",
                    uuid=self.transmission_uuid,
                    timestamp=timestamp,
                    mycallsign=str(mycallsign, "UTF-8"),
                    dxcallsign=str(static.DXCALLSIGN, "UTF-8"),
                    dxgrid=str(static.DXGRID, "UTF-8"),
                    data=base64_data,
                )

                self.log.info(
                    "[TNC] ARQ | RX | SENDING DATA FRAME ACK",
                    snr=snr,
                    crc=data_frame_crc.hex(),
                )

                self.send_data_ack_frame(snr)
                # Update statistics AFTER the frame ACK is sent
                self.calculate_transfer_rate_rx(
                    self.rx_start_of_transmission, len(static.RX_FRAME_BUFFER)
                )

                self.log.info(
                    "[TNC] | RX | DATACHANNEL ["
                    + str(self.mycallsign, "UTF-8")
                    + "]<< >>["
                    + str(static.DXCALLSIGN, "UTF-8")
                    + "]",
                    snr=snr,
                )

            else:
                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    arq="transmission",
                    status="failed",
                    uuid=self.transmission_uuid,
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                )

                self.log.warning(
                    "[TNC] ARQ | RX | DATA FRAME NOT SUCCESSFULLY RECEIVED!",
                    e="wrong crc",
                    expected=data_frame_crc.hex(),
                    received=data_frame_crc_received.hex(),
                    overflows=static.BUFFER_OVERFLOW_COUNTER,
                )

                self.log.info("[TNC] ARQ | RX | Sending NACK")
                self.send_burst_nack_frame(snr)

            # Update arq_session timestamp
            self.arq_session_last_received = int(time.time())

            # Finally cleanup our buffers and states,
            self.arq_cleanup()

    def arq_transmit(self, data_out: bytes, mode: int, n_frames_per_burst: int):
        """
        Transmit ARQ frame

        Args:
          data_out:bytes:
          mode:int:
          n_frames_per_burst:int:

        """
        self.arq_file_transfer = True

        # set signalling modes we want to listen to
        # we are in an ongoing arq transmission, so we don't need sig0 actually
        modem.RECEIVE_SIG0 = False
        modem.RECEIVE_SIG1 = True

        self.tx_n_retry_of_burst = 0  # retries we already sent data
        # Maximum number of retries to send before declaring a frame is lost

        # save len of data_out to TOTAL_BYTES for our statistics --> kBytes
        # static.TOTAL_BYTES = round(len(data_out) / 1024, 2)
        static.TOTAL_BYTES = len(data_out)
        frame_total_size = len(data_out).to_bytes(4, byteorder="big")

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            status="transmitting",
            uuid=self.transmission_uuid,
            percent=static.ARQ_TRANSMISSION_PERCENT,
            bytesperminute=static.ARQ_BYTES_PER_MINUTE,
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )

        self.log.info(
            "[TNC] | TX | DATACHANNEL",
            Bytes=static.TOTAL_BYTES,
        )

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
        self.log.debug("[TNC] frame payload CRC:", crc=frame_payload_crc.hex())

        # Assemble the data frame
        data_out = (
                self.data_frame_bof
                + frame_payload_crc
                + frame_total_size
                + compression_factor
                + data_out
                + self.data_frame_eof
        )

        # Initial bufferposition is 0
        bufferposition = bufferposition_end = 0

        # Iterate through data_out buffer
        while not self.data_frame_ack_received and static.ARQ_STATE:
            # we have self.tx_n_max_retries_per_burst attempts for sending a burst
            for self.tx_n_retry_of_burst in range(self.tx_n_max_retries_per_burst):
                # data_mode = mode
                # self.log.debug("[TNC] FIXED MODE:", mode=FREEDV_MODE(data_mode).name)

                # we are doing a modulo check of transmission retries of the actual burst
                # every 2nd retry which fails, decreases speedlevel by 1.
                # as soon as we received an ACK for the current burst, speed_level will increase
                # by 1.
                # The intent is to optimize speed by adapting to the current RF conditions.
                # if not self.tx_n_retry_of_burst % 2 and self.tx_n_retry_of_burst > 0:
                #    self.speed_level = max(self.speed_level - 1, 0)

                # if self.tx_n_retry_of_burst <= 1:
                #    self.speed_level += 1
                # self.speed_level = max(self.speed_level + 1, len(self.mode_list) - 1)

                # Bound speed level to:
                # - minimum of either the speed or the length of mode list - 1
                # - maximum of either the speed or zero
                self.speed_level = min(self.speed_level, len(self.mode_list) - 1)
                self.speed_level = max(self.speed_level, 0)

                static.ARQ_SPEED_LEVEL = self.speed_level
                data_mode = self.mode_list[self.speed_level]

                self.log.debug(
                    "[TNC] Speed-level:",
                    level=self.speed_level,
                    retry=self.tx_n_retry_of_burst,
                    mode=FREEDV_MODE(data_mode).name,
                )

                # Payload information
                payload_per_frame = modem.get_bytes_per_frame(data_mode) - 2

                # Tempbuffer list for storing our data frames
                tempbuffer = []

                # Append data frames with n_frames_per_burst to tempbuffer
                # TODO: this part needs a complete rewrite!
                # n_frames_per_burst = 1 is working

                arqheader = bytearray()
                # arqheader[:1] = bytes([FR_TYPE.BURST_01.value + i])
                arqheader[:1] = bytes([FR_TYPE.BURST_01.value])
                arqheader[1:2] = bytes([n_frames_per_burst])
                arqheader[2:3] = self.session_id
                # arqheader[2:5] = static.DXCALLSIGN_CRC
                # arqheader[5:8] = static.MYCALLSIGN_CRC

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

                # Append frame to tempbuffer for transmission
                tempbuffer.append(frame)

                self.log.debug("[TNC] tempbuffer:", tempbuffer=tempbuffer)
                self.log.info(
                    "[TNC] ARQ | TX | FRAMES",
                    mode=FREEDV_MODE(data_mode).name,
                    fpb=n_frames_per_burst,
                    retry=self.tx_n_retry_of_burst,
                )

                for t_buf_item in tempbuffer:
                    self.enqueue_frame_for_tx([t_buf_item], c2_mode=data_mode)

                # After transmission finished, wait for an ACK or RPT frame
                # burstacktimeout = time.time() + self.burst_ack_timeout_seconds + 100
                # while (not self.burst_ack and not self.burst_nack and
                #         not self.rpt_request_received and not self.data_frame_ack_received and
                #         time.time() < burstacktimeout and static.ARQ_STATE):
                #     threading.Event().wait(0.01)

                # burstacktimeout = time.time() + self.burst_ack_timeout_seconds + 100
                while static.ARQ_STATE and not (
                        self.burst_ack
                        or self.burst_nack
                        or self.rpt_request_received
                        or self.data_frame_ack_received
                ):
                    threading.Event().wait(0.01)

                # Once we receive a burst ack, reset its state and break the RETRIES loop
                if self.burst_ack:
                    self.burst_ack = False  # reset ack state
                    self.tx_n_retry_of_burst = 0  # reset retries
                    self.log.debug(
                        "[TNC] arq_transmit: Received BURST ACK. Sending next chunk."
                    , irs_snr=self.burst_ack_snr)
                    break  # break retry loop

                if self.burst_nack:
                    self.burst_nack = False  # reset nack state

                # not yet implemented
                if self.rpt_request_received:
                    pass

                if self.data_frame_ack_received:
                    self.log.debug(
                        "[TNC] arq_transmit: Received FRAME ACK. Sending next chunk."
                    )
                    break  # break retry loop

                # We need this part for leaving the repeat loop
                # static.ARQ_STATE == "DATA" --> when stopping transmission manually
                if not static.ARQ_STATE:
                    # print("not ready for data...leaving loop....")
                    self.log.debug(
                        "[TNC] arq_transmit: ARQ State changed to FALSE. Breaking retry loop."
                    )
                    break

                self.calculate_transfer_rate_tx(
                    tx_start_of_transmission, bufferposition_end, len(data_out)
                )
                # NEXT ATTEMPT
                self.log.debug(
                    "[TNC] ATTEMPT:",
                    retry=self.tx_n_retry_of_burst,
                    maxretries=self.tx_n_max_retries_per_burst,
                    overflows=static.BUFFER_OVERFLOW_COUNTER,
                )
                # End of FOR loop

            # update buffer position
            bufferposition = bufferposition_end

            # update stats
            self.calculate_transfer_rate_tx(
                tx_start_of_transmission, bufferposition_end, len(data_out)
            )

            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="transmission",
                status="transmitting",
                uuid=self.transmission_uuid,
                percent=static.ARQ_TRANSMISSION_PERCENT,
                bytesperminute=static.ARQ_BYTES_PER_MINUTE,
                irs_snr=self.burst_ack_snr,
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )

            # Stay in the while loop until we receive a data_frame_ack. Otherwise,
            # the loop exits after sending the last frame only once and doesn't
            # wait for an acknowledgement.
            if self.data_frame_ack_received and bufferposition > len(data_out):
                self.log.debug("[TNC] arq_tx: Last fragment sent and acknowledged.")
                break
            # GOING TO NEXT ITERATION

        if self.data_frame_ack_received:
            # we need to wait until sending "transmitted" state
            # gui database is too slow for handling this within 0.001 seconds
            # so let's sleep a little
            threading.Event().wait(0.2)
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="transmission",
                status="transmitted",
                uuid=self.transmission_uuid,
                percent=static.ARQ_TRANSMISSION_PERCENT,
                bytesperminute=static.ARQ_BYTES_PER_MINUTE,
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )

            self.log.info(
                "[TNC] ARQ | TX | DATA TRANSMITTED!",
                BytesPerMinute=static.ARQ_BYTES_PER_MINUTE,
                BitsPerSecond=static.ARQ_BITS_PER_SECOND,
                overflows=static.BUFFER_OVERFLOW_COUNTER,
            )

        else:
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="transmission",
                status="failed",
                uuid=self.transmission_uuid,
                percent=static.ARQ_TRANSMISSION_PERCENT,
                bytesperminute=static.ARQ_BYTES_PER_MINUTE,
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )

            self.log.info(
                "[TNC] ARQ | TX | TRANSMISSION FAILED OR TIME OUT!",
                overflows=static.BUFFER_OVERFLOW_COUNTER,
            )
            self.stop_transmission()

        # Last but not least do a state cleanup
        self.arq_cleanup()
        if TESTMODE:
            # Quit after transmission
            self.log.debug("[TNC] TESTMODE: arq_transmit exiting.")
            sys.exit(0)

    def burst_ack_nack_received(self, data_in: bytes) -> None:
        """
        Received an ACK/NACK for a transmitted frame, keep track and
        make adjustments to speed level if needed.

        Args:
          data_in:bytes:

        Returns:

        """
        # Process data only if we are in ARQ and BUSY state
        if static.ARQ_STATE:
            helpers.add_to_heard_stations(
                static.DXCALLSIGN,
                static.DXGRID,
                "DATA-CHANNEL",
                static.SNR,
                static.FREQ_OFFSET,
                static.HAMLIB_FREQUENCY,
            )

            frametype = int.from_bytes(bytes(data_in[:1]), "big")
            desc = "ack"
            if frametype == FR_TYPE.BURST_ACK.value:
                # Increase speed level if we received a burst ack
                # self.speed_level = min(self.speed_level + 1, len(self.mode_list) - 1)
                # Force data retry loops of TX TNC to stop and continue with next frame
                self.burst_ack = True
                # Reset burst nack counter
                self.burst_nack_counter = 0
                # Reset n retries per burst counter
                self.n_retries_per_burst = 0
            else:
                # Decrease speed level if we received a burst nack
                # self.speed_level = max(self.speed_level - 1, 0)
                # Set flag to retry frame again.
                self.burst_nack = True
                # Increment burst nack counter
                self.burst_nack_counter += 1
                desc = "nack"

            # Update data_channel timestamp
            self.data_channel_last_received = int(time.time())
            # self.burst_ack_snr = int.from_bytes(bytes(data_in[2:3]), "big")
            self.burst_ack_snr = helpers.snr_from_bytes(data_in[2:3])
            # self.log.info("SNR ON IRS", snr=self.burst_ack_snr)

            self.speed_level = int.from_bytes(bytes(data_in[3:4]), "big")
            static.ARQ_SPEED_LEVEL = self.speed_level

            #self.log.debug(
            #    f"[TNC] burst_{desc}_received:",
            #    speed_level=self.speed_level,
            #    c2_mode=FREEDV_MODE(self.mode_list[self.speed_level]).name,
            #)

    def frame_ack_received(
            self, data_in: bytes  # pylint: disable=unused-argument
    ) -> None:
        """Received an ACK for a transmitted frame"""
        # Process data only if we are in ARQ and BUSY state
        if static.ARQ_STATE:
            helpers.add_to_heard_stations(
                static.DXCALLSIGN,
                static.DXGRID,
                "DATA-CHANNEL",
                static.SNR,
                static.FREQ_OFFSET,
                static.HAMLIB_FREQUENCY,
            )
            # Force data loops of TNC to stop and continue with next frame
            self.data_frame_ack_received = True
            # Update arq_session and data_channel timestamp
            self.data_channel_last_received = int(time.time())
            self.arq_session_last_received = int(time.time())

    def frame_nack_received(
            self, data_in: bytes  # pylint: disable=unused-argument
    ) -> None:
        """
        Received a NACK for a transmitted frame

        Args:
          data_in:bytes:

        """
        self.log.warning("[TNC] ARQ FRAME NACK RECEIVED - cleanup!",
                         arq="transmission",
                         status="failed",
                         uuid=self.transmission_uuid,
                         percent=static.ARQ_TRANSMISSION_PERCENT,
                         bytesperminute=static.ARQ_BYTES_PER_MINUTE,
                         mycallsign=str(self.mycallsign, 'UTF-8'),
                         dxcallsign=str(self.dxcallsign, 'UTF-8'),
                         )

        helpers.add_to_heard_stations(
            static.DXCALLSIGN,
            static.DXGRID,
            "DATA-CHANNEL",
            static.SNR,
            static.FREQ_OFFSET,
            static.HAMLIB_FREQUENCY,
        )
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            status="failed",
            uuid=self.transmission_uuid,
            percent=static.ARQ_TRANSMISSION_PERCENT,
            bytesperminute=static.ARQ_BYTES_PER_MINUTE,
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )
        # Update data_channel timestamp
        self.arq_session_last_received = int(time.time())

        self.arq_cleanup()

    def burst_rpt_received(self, data_in: bytes):
        """
        Repeat request frame received for transmitted frame

        Args:
          data_in:bytes:

        """
        # Only process data if we are in ARQ and BUSY state
        if static.ARQ_STATE and static.TNC_STATE == "BUSY":
            helpers.add_to_heard_stations(
                static.DXCALLSIGN,
                static.DXGRID,
                "DATA-CHANNEL",
                static.SNR,
                static.FREQ_OFFSET,
                static.HAMLIB_FREQUENCY,
            )

            self.rpt_request_received = True
            # Update data_channel timestamp
            self.data_channel_last_received = int(time.time())
            self.rpt_request_buffer = []

            missing_area = bytes(data_in[3:12])  # 1:9

            for i in range(0, 6, 2):
                if not missing_area[i: i + 2].endswith(b"\x00\x00"):
                    missing = missing_area[i: i + 2]
                    self.rpt_request_buffer.insert(0, missing)

    ############################################################################################################
    # ARQ SESSION HANDLER
    ############################################################################################################
    def arq_session_handler(self, mycallsign, dxcallsign, attempts) -> bool:
        """
        Create a session with `static.DXCALLSIGN` and wait until the session is open.

        Returns:
            True if the session was opened successfully
            False if the session open request failed
        """
        # override connection attempts
        self.session_connect_max_retries = attempts

        self.mycallsign = mycallsign
        self.dxcallsign = dxcallsign

        static.DXCALLSIGN = self.dxcallsign
        static.DXCALLSIGN_CRC = helpers.get_crc_24(self.dxcallsign)

        # TODO: we need to check this, maybe placing it to class init
        self.datachannel_timeout = False
        self.log.info(
            "[TNC] SESSION ["
            + str(self.mycallsign, "UTF-8")
            + "]>> <<["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            state=static.ARQ_SESSION_STATE,
        )

        # Let's check if we have a busy channel
        if static.CHANNEL_BUSY:
            self.log.warning("[TNC] Channel busy, waiting until free...")
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="session",
                status="waiting",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )

            # wait while timeout not reached and our busy state is busy
            channel_busy_timeout = time.time() + 30
            while static.CHANNEL_BUSY and time.time() < channel_busy_timeout:
                threading.Event().wait(0.01)

            # if channel busy timeout reached stop connecting
            if time.time() > channel_busy_timeout:
                self.log.warning("[TNC] Channel busy, try again later...")
                static.ARQ_SESSION_STATE = "failed"
                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    arq="session",
                    status="failed",
                    reason="busy",
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                )
                return False

        self.open_session()

        # wait until data channel is open
        while not static.ARQ_SESSION and not self.arq_session_timeout:
            threading.Event().wait(0.01)
            static.ARQ_SESSION_STATE = "connecting"
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="session",
                status="connecting",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )
        if static.ARQ_SESSION and static.ARQ_SESSION_STATE == "connected":
            # static.ARQ_SESSION_STATE = "connected"
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="session",
                status="connected",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )
            return True

        self.log.warning(
            "[TNC] SESSION FAILED ["
            + str(self.mycallsign, "UTF-8")
            + "]>>X<<["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            attempts=self.session_connect_max_retries,  # Adjust for 0-based for user display
            reason="maximum connection attempts reached",
            state=static.ARQ_SESSION_STATE,
        )
        static.ARQ_SESSION_STATE = "failed"
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="session",
            status="failed",
            reason="timeout",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
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
        static.ARQ_SESSION_STATE = "connecting"

        # create a random session id
        # self.session_id = randbytes(1)
        self.session_id = np.random.bytes(1)

        connection_frame = bytearray(self.length_sig0_frame)
        connection_frame[:1] = bytes([FR_TYPE.ARQ_SESSION_OPEN.value])
        connection_frame[1:2] = self.session_id
        connection_frame[2:5] = static.DXCALLSIGN_CRC
        connection_frame[5:8] = static.MYCALLSIGN_CRC
        connection_frame[8:14] = helpers.callsign_to_bytes(self.mycallsign)

        while not static.ARQ_SESSION:
            threading.Event().wait(0.01)
            for attempt in range(self.session_connect_max_retries):
                self.log.info(
                    "[TNC] SESSION ["
                    + str(self.mycallsign, "UTF-8")
                    + "]>>?<<["
                    + str(self.dxcallsign, "UTF-8")
                    + "]",
                    a=str(attempt + 1) + "/" + str(self.session_connect_max_retries),  # Adjust for 0-based for user display
                    state=static.ARQ_SESSION_STATE,
                )

                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    arq="session",
                    status="connecting",
                    attempt=attempt + 1,
                    maxattempts=self.session_connect_max_retries,
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                )

                self.enqueue_frame_for_tx([connection_frame], c2_mode=FREEDV_MODE.datac0.value, copies=1, repeat_delay=0)

                # Wait for a time, looking to see if `static.ARQ_SESSION`
                # indicates we've received a positive response from the far station.
                timeout = time.time() + 3
                while time.time() < timeout:
                    threading.Event().wait(0.01)
                    # Stop waiting if data channel is opened
                    if static.ARQ_SESSION:
                        return True

                    # Stop waiting and interrupt if data channel is getting closed while opening
                    if static.ARQ_SESSION_STATE == "disconnecting":
                        # disabled this session close as its called twice
                        # self.close_session()
                        return False

            # Session connect timeout, send close_session frame to
            # attempt to clean up the far-side, if it received the
            # open_session frame and can still hear us.
            if not static.ARQ_SESSION:
                self.close_session()
                return False

        # Given the while condition, it will only exit when `static.ARQ_SESSION` is True
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="session",
            status="connected",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )
        return True

    def received_session_opener(self, data_in: bytes) -> None:
        """
        Received a session open request packet.

        Args:
          data_in:bytes:
        """
        # if we don't want to respond to calls, return False
        if not static.RESPOND_TO_CALL:
            return False

        self.IS_ARQ_SESSION_MASTER = False
        static.ARQ_SESSION_STATE = "connecting"

        # Update arq_session timestamp
        self.arq_session_last_received = int(time.time())

        self.session_id = bytes(data_in[1:2])
        static.DXCALLSIGN_CRC = bytes(data_in[5:8])
        self.dxcallsign = helpers.bytes_to_callsign(bytes(data_in[8:14]))
        static.DXCALLSIGN = self.dxcallsign

        # check if callsign ssid override
        valid, mycallsign = helpers.check_callsign(self.mycallsign, data_in[2:5])
        self.mycallsign = mycallsign

        helpers.add_to_heard_stations(
            static.DXCALLSIGN,
            static.DXGRID,
            "DATA-CHANNEL",
            static.SNR,
            static.FREQ_OFFSET,
            static.HAMLIB_FREQUENCY,
        )
        self.log.info(
            "[TNC] SESSION ["
            + str(self.mycallsign, "UTF-8")
            + "]>>|<<["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            state=static.ARQ_SESSION_STATE,
        )
        static.ARQ_SESSION = True
        static.TNC_STATE = "BUSY"

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="session",
            status="connected",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )
        self.transmit_session_heartbeat()

    def close_session(self) -> None:
        """Close the ARQ session"""
        static.ARQ_SESSION_STATE = "disconnecting"

        self.log.info(
            "[TNC] SESSION ["
            + str(self.mycallsign, "UTF-8")
            + "]<<X>>["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            state=static.ARQ_SESSION_STATE,
        )

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="session",
            status="close",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )

        self.IS_ARQ_SESSION_MASTER = False
        static.ARQ_SESSION = False

        # we need to send disconnect frame before doing arq cleanup
        # we would lose our session id then
        self.send_disconnect_frame()
        self.arq_cleanup()

        static.ARQ_SESSION_STATE = "disconnected"

    def received_session_close(self, data_in: bytes):
        """
        Closes the session when a close session frame is received and
        the DXCALLSIGN_CRC matches the remote station participating in the session.

        Args:
          data_in:bytes:

        """
        # We've arrived here from process_data which already checked that the frame
        # is intended for this station.
        # Close the session if the CRC matches the remote station in static.
        _valid_crc, mycallsign = helpers.check_callsign(self.mycallsign, bytes(data_in[2:5]))
        _valid_session = helpers.check_session_id(self.session_id, bytes(data_in[1:2]))
        if _valid_crc or _valid_session and static.ARQ_SESSION_STATE != "disconnected":
            static.ARQ_SESSION_STATE = "disconnected"
            helpers.add_to_heard_stations(
                static.DXCALLSIGN,
                static.DXGRID,
                "DATA-CHANNEL",
                static.SNR,
                static.FREQ_OFFSET,
                static.HAMLIB_FREQUENCY,
            )
            self.log.info(
                "[TNC] SESSION ["
                + str(mycallsign, "UTF-8")
                + "]<<X>>["
                + str(self.dxcallsign, "UTF-8")
                + "]",
                state=static.ARQ_SESSION_STATE,
            )

            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="session",
                status="close",
                mycallsign=str(mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )

            self.IS_ARQ_SESSION_MASTER = False
            static.ARQ_SESSION = False
            self.arq_cleanup()

    def transmit_session_heartbeat(self) -> None:
        """Send ARQ sesion heartbeat while connected"""
        # static.ARQ_SESSION = True
        # static.TNC_STATE = "BUSY"
        # static.ARQ_SESSION_STATE = "connected"

        connection_frame = bytearray(self.length_sig0_frame)
        connection_frame[:1] = bytes([FR_TYPE.ARQ_SESSION_HB.value])
        connection_frame[1:2] = self.session_id
        # connection_frame[1:4] = static.DXCALLSIGN_CRC
        # connection_frame[4:7] = static.MYCALLSIGN_CRC

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="session",
            status="connected",
            heartbeat="transmitting",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )

        self.enqueue_frame_for_tx([connection_frame], c2_mode=FREEDV_MODE.datac0.value, copies=1, repeat_delay=0)

    def received_session_heartbeat(self, data_in: bytes) -> None:
        """
        Received an ARQ session heartbeat, record and update state accordingly.
        Args:
          data_in:bytes:

        """
        # Accept session data if the DXCALLSIGN_CRC matches the station in static or session id.
        _valid_crc, _ = helpers.check_callsign(self.dxcallsign, bytes(data_in[4:7]))
        _valid_session = helpers.check_session_id(self.session_id, bytes(data_in[1:2]))
        if _valid_crc or _valid_session:
            self.log.debug("[TNC] Received session heartbeat")
            helpers.add_to_heard_stations(
                self.dxcallsign,
                static.DXGRID,
                "SESSION-HB",
                static.SNR,
                static.FREQ_OFFSET,
                static.HAMLIB_FREQUENCY,
            )

            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="session",
                status="connected",
                heartbeat="received",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )

            static.ARQ_SESSION = True
            static.ARQ_SESSION_STATE = "connected"
            static.TNC_STATE = "BUSY"

            # Update the timeout timestamps
            self.arq_session_last_received = int(time.time())
            self.data_channel_last_received = int(time.time())
            # transmit session heartbeat only
            # -> if not session master
            # --> this will be triggered by heartbeat watchdog
            # -> if not during a file transfer
            # -> if ARQ_SESSION_STATE != disconnecting, disconnected, failed
            # --> to avoid heartbeat toggle loops while disconnecting
            if (
                    not self.IS_ARQ_SESSION_MASTER
                    and not self.arq_file_transfer
                    and static.ARQ_SESSION_STATE != 'disconnecting'
                    and static.ARQ_SESSION_STATE != 'disconnected'
                    and static.ARQ_SESSION_STATE != 'failed'
            ):
                self.transmit_session_heartbeat()

    ##########################################################################################################
    # ARQ DATA CHANNEL HANDLER
    ##########################################################################################################
    def open_dc_and_transmit(
            self,
            data_out: bytes,
            mode: int,
            n_frames_per_burst: int,
            transmission_uuid: str,
            mycallsign,
            dxcallsign,
            attempts: int,
    ) -> bool:
        """
        Open data channel and transmit data

        Args:
          data_out:bytes:
          mode:int:
          n_frames_per_burst:int:
          transmission_uuid:str:
          mycallsign:bytes:
          attempts:int: Overriding number of attempts initiating a connection

        Returns:
            True if the data session was opened and the data was sent
            False if the data session was not opened
        """
        # overwrite mycallsign in case of different SSID
        self.mycallsign = mycallsign
        self.dxcallsign = dxcallsign

        # override session connection attempts
        self.data_channel_max_retries = attempts

        static.TNC_STATE = "BUSY"
        self.arq_file_transfer = True

        self.transmission_uuid = transmission_uuid

        # wait a moment for the case, a heartbeat is already on the way back to us
        # this makes channel establishment more clean
        if static.ARQ_SESSION:
            threading.Event().wait(2)

        self.datachannel_timeout = False

        # we need to compress data for getting a compression factor.
        # so we are compressing twice. This is not that nice and maybe there is another way
        # for calculating transmission statistics
        # static.ARQ_COMPRESSION_FACTOR = len(data_out) / len(zlib.compress(data_out))

        # Let's check if we have a busy channel and if we are not in a running arq session.
        if static.CHANNEL_BUSY and not static.ARQ_SESSION:
            self.log.warning("[TNC] Channel busy, waiting until free...")
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="transmission",
                status="waiting",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )

            # wait while timeout not reached and our busy state is busy
            channel_busy_timeout = time.time() + 30
            while static.CHANNEL_BUSY and time.time() < channel_busy_timeout:
                threading.Event().wait(0.01)

            # if channel busy timeout reached, stop connecting
            if time.time() > channel_busy_timeout:
                self.log.warning("[TNC] Channel busy, try again later...")
                static.ARQ_SESSION_STATE = "failed"
                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    arq="transmission",
                    status="failed",
                    reason="busy",
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                )
                static.ARQ_SESSION_STATE = "disconnected"
                return False

        self.arq_open_data_channel(mode, n_frames_per_burst, mycallsign)

        # wait until data channel is open
        while not static.ARQ_STATE and not self.datachannel_timeout:
            threading.Event().wait(0.01)

        if static.ARQ_STATE:
            self.arq_transmit(data_out, mode, n_frames_per_burst)
            return True

        return False

    def arq_open_data_channel(
            self, mode: int, n_frames_per_burst: int, mycallsign
    ) -> bool:
        """
        Open an ARQ data channel.

        Args:
          mode:int:
          n_frames_per_burst:int:
          mycallsign:bytes:

        Returns:
            True if the data channel was opened successfully
            False if the data channel failed to open
        """
        self.is_IRS = False

        # init a new random session id if we are not in an arq session
        if not static.ARQ_SESSION:
            # self.session_id = randbytes(1)
            self.session_id = np.random.bytes(1)

        # Update data_channel timestamp
        self.data_channel_last_received = int(time.time())

        if static.LOW_BANDWIDTH_MODE:
            frametype = bytes([FR_TYPE.ARQ_DC_OPEN_N.value])
            self.log.debug("[TNC] Requesting low bandwidth mode")

        else:
            frametype = bytes([FR_TYPE.ARQ_DC_OPEN_W.value])
            self.log.debug("[TNC] Requesting high bandwidth mode")

        connection_frame = bytearray(self.length_sig0_frame)
        connection_frame[:1] = frametype
        connection_frame[1:4] = static.DXCALLSIGN_CRC
        connection_frame[4:7] = static.MYCALLSIGN_CRC
        connection_frame[7:13] = helpers.callsign_to_bytes(mycallsign)
        # connection_frame[13:14] = bytes([n_frames_per_burst])
        connection_frame[13:14] = self.session_id

        while not static.ARQ_STATE:
            threading.Event().wait(0.01)
            for attempt in range(self.data_channel_max_retries):

                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    arq="transmission",
                    status="opening",
                    mycallsign=str(mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign,'UTF-8'),
                )

                self.log.info(
                    "[TNC] ARQ | DATA | TX | ["
                    + str(mycallsign, "UTF-8")
                    + "]>> <<["
                    + str(self.dxcallsign, "UTF-8")
                    + "]",
                    attempt=f"{str(attempt + 1)}/{str(self.data_channel_max_retries)}",
                )

                self.enqueue_frame_for_tx([connection_frame], c2_mode=FREEDV_MODE.datac0.value, copies=1, repeat_delay=0)

                timeout = time.time() + 3
                while time.time() < timeout:
                    threading.Event().wait(0.01)
                    # Stop waiting if data channel is opened
                    if static.ARQ_STATE:
                        return True

            # `data_channel_max_retries` attempts have been sent. Aborting attempt & cleaning up

            self.log.debug(
                "[TNC] arq_open_data_channel:", transmission_uuid=self.transmission_uuid
            )

            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="transmission",
                status="failed",
                reason="unknown",
                uuid=self.transmission_uuid,
                percent=static.ARQ_TRANSMISSION_PERCENT,
                bytesperminute=static.ARQ_BYTES_PER_MINUTE,
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )

            self.log.warning(
                "[TNC] ARQ | TX | DATA ["
                + str(mycallsign, "UTF-8")
                + "]>>X<<["
                + str(self.dxcallsign, "UTF-8")
                + "]"
            )
            self.datachannel_timeout = True

            # Attempt to clean up the far-side, if it received the
            # open_session frame and can still hear us.
            self.close_session()

            self.arq_cleanup()
            return False

        # Shouldn't get here...
        return True

    def arq_received_data_channel_opener(self, data_in: bytes):
        """
        Received request to open data channel frame

        Args:
          data_in:bytes:

        """
        # We've arrived here from process_data which already checked that the frame
        # is intended for this station.

        # stop processing if we don't want to respond to a call when not in a arq session
        if not static.RESPOND_TO_CALL and not static.ARQ_SESSION:
            return False

        self.arq_file_transfer = True
        self.is_IRS = True

        static.DXCALLSIGN_CRC = bytes(data_in[4:7])
        self.dxcallsign = helpers.bytes_to_callsign(bytes(data_in[7:13]))
        static.DXCALLSIGN = self.dxcallsign

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            status="opening",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )



        # n_frames_per_burst is currently unused
        # n_frames_per_burst = int.from_bytes(bytes(data_in[13:14]), "big")

        frametype = int.from_bytes(bytes(data_in[:1]), "big")
        # check if we received low bandwidth mode
        # possible channel constellations
        # ISS(w) <-> IRS(w)
        # ISS(w) <-> IRS(n)
        # ISS(n) <-> IRS(w)
        # ISS(n) <-> IRS(n)

        if frametype == FR_TYPE.ARQ_DC_OPEN_W.value and not static.LOW_BANDWIDTH_MODE:
            # ISS(w) <-> IRS(w)
            constellation = "ISS(w) <-> IRS(w)"
            self.received_LOW_BANDWIDTH_MODE = False
            self.mode_list = self.mode_list_high_bw
            self.time_list = self.time_list_high_bw
            self.snr_list = self.snr_list_high_bw
        elif frametype == FR_TYPE.ARQ_DC_OPEN_W.value and static.LOW_BANDWIDTH_MODE:
            # ISS(w) <-> IRS(n)
            constellation = "ISS(w) <-> IRS(n)"
            self.received_LOW_BANDWIDTH_MODE = False
            self.mode_list = self.mode_list_low_bw
            self.time_list = self.time_list_low_bw
            self.snr_list = self.snr_list_low_bw
        elif frametype == FR_TYPE.ARQ_DC_OPEN_N.value and not static.LOW_BANDWIDTH_MODE:
            # ISS(n) <-> IRS(w)
            constellation = "ISS(n) <-> IRS(w)"
            self.received_LOW_BANDWIDTH_MODE = True
            self.mode_list = self.mode_list_low_bw
            self.time_list = self.time_list_low_bw
            self.snr_list = self.snr_list_low_bw
        elif frametype == FR_TYPE.ARQ_DC_OPEN_N.value and static.LOW_BANDWIDTH_MODE:
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
        # initially set speed_level 0 in case of really bad SNR and no matching mode
        self.speed_level = 0
        for i in range(len(self.mode_list)):
            if static.SNR >= self.snr_list[i]:
                self.speed_level = i

        self.log.debug(
            "[TNC] calculated speed level",
            speed_level=self.speed_level,
            given_snr=static.SNR,
            min_snr=self.snr_list[self.speed_level],
        )

        # Update modes we are listening to
        self.set_listening_modes(True, True, self.mode_list[self.speed_level])

        helpers.add_to_heard_stations(
            static.DXCALLSIGN,
            static.DXGRID,
            "DATA-CHANNEL",
            static.SNR,
            static.FREQ_OFFSET,
            static.HAMLIB_FREQUENCY,
        )

        self.session_id = data_in[13:14]
        print(self.session_id)

        # check if callsign ssid override
        _, mycallsign = helpers.check_callsign(self.mycallsign, data_in[1:4])

        self.log.info(
            "[TNC] ARQ | DATA | RX | ["
            + str(mycallsign, "UTF-8")
            + "]>> <<["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            channel_constellation=constellation,
        )

        static.ARQ_STATE = True
        static.TNC_STATE = "BUSY"

        self.reset_statistics()

        # Update data_channel timestamp
        self.data_channel_last_received = int(time.time())

        # Select the frame type based on the current TNC mode
        if static.LOW_BANDWIDTH_MODE or self.received_LOW_BANDWIDTH_MODE:
            frametype = bytes([FR_TYPE.ARQ_DC_OPEN_ACK_N.value])
            self.log.debug("[TNC] Responding with low bandwidth mode")
        else:
            frametype = bytes([FR_TYPE.ARQ_DC_OPEN_ACK_W.value])
            self.log.debug("[TNC] Responding with high bandwidth mode")

        connection_frame = bytearray(self.length_sig0_frame)
        connection_frame[:1] = frametype
        connection_frame[1:2] = self.session_id
        # connection_frame[1:4] = static.DXCALLSIGN_CRC
        # connection_frame[4:7] = static.MYCALLSIGN_CRC
        connection_frame[8:9] = bytes([self.speed_level])

        # For checking protocol version on the receiving side
        connection_frame[13:14] = bytes([static.ARQ_PROTOCOL_VERSION])

        self.enqueue_frame_for_tx([connection_frame], c2_mode=FREEDV_MODE.datac0.value, copies=1, repeat_delay=0)

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            status="opened",
            mycallsign=str(mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )

        self.log.info(
            "[TNC] ARQ | DATA | RX | ["
            + str(mycallsign, "UTF-8")
            + "]>>|<<["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            bandwidth="wide",
            snr=static.SNR,
        )

        # set start of transmission for our statistics
        self.rx_start_of_transmission = time.time()

        # Update data_channel timestamp
        self.data_channel_last_received = int(time.time())

    def arq_received_channel_is_open(self, data_in: bytes) -> None:
        """
        Called if we received a data channel opener
        Args:
          data_in:bytes:

        """
        protocol_version = int.from_bytes(bytes(data_in[13:14]), "big")
        if protocol_version == static.ARQ_PROTOCOL_VERSION:
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="transmission",
                status="opened",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )
            frametype = int.from_bytes(bytes(data_in[:1]), "big")

            if frametype == FR_TYPE.ARQ_DC_OPEN_ACK_N.value:
                self.received_LOW_BANDWIDTH_MODE = True
                self.mode_list = self.mode_list_low_bw
                self.time_list = self.time_list_low_bw
                self.log.debug("[TNC] low bandwidth mode", modes=self.mode_list)
            else:
                self.received_LOW_BANDWIDTH_MODE = False
                self.mode_list = self.mode_list_high_bw
                self.time_list = self.time_list_high_bw
                self.log.debug("[TNC] high bandwidth mode", modes=self.mode_list)

            # set speed level from session opener frame which is selected by SNR measurement
            self.speed_level = int.from_bytes(bytes(data_in[8:9]), "big")
            self.log.debug("[TNC] speed level selected for given SNR", speed_level=self.speed_level)
            # self.speed_level = len(self.mode_list) - 1

            helpers.add_to_heard_stations(
                static.DXCALLSIGN,
                static.DXGRID,
                "DATA-CHANNEL",
                static.SNR,
                static.FREQ_OFFSET,
                static.HAMLIB_FREQUENCY,
            )

            self.log.info(
                "[TNC] ARQ | DATA | TX | ["
                + str(self.mycallsign, "UTF-8")
                + "]>>|<<["
                + str(self.dxcallsign, "UTF-8")
                + "]",
                snr=static.SNR,
            )

            # as soon as we set ARQ_STATE to DATA, transmission starts
            static.ARQ_STATE = True
            # Update data_channel timestamp
            self.data_channel_last_received = int(time.time())
        else:
            static.TNC_STATE = "IDLE"
            static.ARQ_STATE = False
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="transmission",
                status="failed",
                reason="protocol version missmatch",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )
            # TODO: We should display a message to this effect on the UI.
            self.log.warning(
                "[TNC] protocol version mismatch:",
                received=protocol_version,
                own=static.ARQ_PROTOCOL_VERSION,
            )
            self.arq_cleanup()

    # ---------- PING
    def transmit_ping(self, mycallsign: bytes, dxcallsign: bytes) -> None:
        """
        Funktion for controlling pings
        Args:
          mycallsign:bytes:
          dxcallsign:bytes:

        """
        if not str(dxcallsign).strip():
            # TODO: We should display a message to this effect on the UI.
            self.log.warning("[TNC] Missing required callsign", dxcallsign=dxcallsign)
            return
        static.DXCALLSIGN = dxcallsign
        static.DXCALLSIGN_CRC = helpers.get_crc_24(static.DXCALLSIGN)

        self.send_data_to_socket_queue(freedata="tnc-message", ping="transmitting")
        self.log.info(
            "[TNC] PING REQ ["
            + str(mycallsign, "UTF-8")
            + "] >>> ["
            + str(dxcallsign, "UTF-8")
            + "]"
        )

        ping_frame = bytearray(self.length_sig0_frame)
        ping_frame[:1] = bytes([FR_TYPE.PING.value])
        ping_frame[1:4] = static.DXCALLSIGN_CRC
        ping_frame[4:7] = static.MYCALLSIGN_CRC
        ping_frame[7:13] = helpers.callsign_to_bytes(mycallsign)

        self.log.info("[TNC] ENABLE FSK", state=static.ENABLE_FSK)
        if static.ENABLE_FSK:
            self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.fsk_ldpc_0.value)
        else:
            self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.datac0.value)

    def received_ping(self, data_in: bytes) -> None:
        """
        Called if we received a ping

        Args:
          data_in:bytes:

        """
        dxcallsign_crc = bytes(data_in[4:7])
        dxcallsign = helpers.bytes_to_callsign(bytes(data_in[7:13]))

        # check if callsign ssid override
        valid, mycallsign = helpers.check_callsign(self.mycallsign, data_in[1:4])
        if not valid:
            # PING packet not for me.
            self.log.debug("[TNC] received_ping: ping not for this station.")
            return

        static.DXCALLSIGN_CRC = dxcallsign_crc
        static.DXCALLSIGN = dxcallsign
        self.log.info(
            "[TNC] PING REQ ["
            + str(mycallsign, "UTF-8")
            + "] <<< ["
            + str(dxcallsign, "UTF-8")
            + "]",
            snr=static.SNR,
        )

        helpers.add_to_heard_stations(
            dxcallsign,
            static.DXGRID,
            "PING",
            static.SNR,
            static.FREQ_OFFSET,
            static.HAMLIB_FREQUENCY,
        )

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            ping="received",
            uuid=str(uuid.uuid4()),
            timestamp=int(time.time()),
            dxgrid=str(static.DXGRID, "UTF-8"),
            dxcallsign = str(dxcallsign, "UTF-8"),
            mycallsign=str(mycallsign, "UTF-8"),
            snr=str(static.SNR),
        )
        if static.RESPOND_TO_CALL:
            ping_frame = bytearray(self.length_sig0_frame)
            ping_frame[:1] = bytes([FR_TYPE.PING_ACK.value])
            ping_frame[1:4] = static.DXCALLSIGN_CRC
            ping_frame[4:7] = static.MYCALLSIGN_CRC
            ping_frame[7:13] = static.MYGRID
            ping_frame[13:14] = helpers.snr_to_bytes(static.SNR)

            if static.ENABLE_FSK:
                self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.fsk_ldpc_0.value)
            else:
                self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.datac0.value)

    def received_ping_ack(self, data_in: bytes) -> None:
        """
        Called if a PING ack has been received
        Args:
          data_in:bytes:

        """

        # check if we received correct ping

        if static.DXCALLSIGN_CRC == bytes(data_in[4:7]):

            # static.DXCALLSIGN_CRC = bytes(data_in[4:7])
            static.DXGRID = bytes(data_in[7:13]).rstrip(b"\x00")
            dxsnr = helpers.snr_from_bytes(data_in[13:14])
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                ping="acknowledge",
                uuid=str(uuid.uuid4()),
                timestamp=int(time.time()),
                dxgrid=str(static.DXGRID, "UTF-8"),
                snr=str(static.SNR),
                dxsnr=str(dxsnr)
            )
            # combined_snr = own rx snr / snr on dx side
            combined_snr = f"{static.SNR}/{dxsnr}"
            helpers.add_to_heard_stations(
                static.DXCALLSIGN,
                static.DXGRID,
                "PING-ACK",
                combined_snr,
                static.FREQ_OFFSET,
                static.HAMLIB_FREQUENCY,
            )

            self.log.info(
                "[TNC] PING ACK ["
                + str(self.mycallsign, "UTF-8")
                + "] >|< ["
                + str(static.DXCALLSIGN, "UTF-8")
                + "]",
                snr=static.SNR,
                dxsnr=dxsnr,
            )
            static.TNC_STATE = "IDLE"
        else:
            self.log.info(
                "[TNC] FOREIGN PING ACK ["
                + str(self.mycallsign, "UTF-8")
                + "] ??? ["
                + str(bytes(data_in[4:7]), "UTF-8")
                + "]",
                snr=static.SNR,
            )

    def stop_transmission(self) -> None:
        """
        Force a stop of the running transmission
        """
        self.log.warning("[TNC] Stopping transmission!")
        stop_frame = bytearray(self.length_sig0_frame)
        stop_frame[:1] = bytes([FR_TYPE.ARQ_STOP.value])
        stop_frame[1:4] = static.DXCALLSIGN_CRC
        stop_frame[4:7] = static.MYCALLSIGN_CRC
        # TODO: Not sure if we really need the session id when disconnecting
        # stop_frame[1:2] = self.session_id
        stop_frame[7:13] = helpers.callsign_to_bytes(self.mycallsign)
        self.enqueue_frame_for_tx([stop_frame], c2_mode=FREEDV_MODE.sig1.value, copies=6, repeat_delay=0)

        static.TNC_STATE = "IDLE"
        static.ARQ_STATE = False
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            status="stopped",
        )
        self.arq_cleanup()

    def received_stop_transmission(
            self, data_in: bytes
    ) -> None:  # pylint: disable=unused-argument
        """
        Received a transmission stop
        """
        self.log.warning("[TNC] Stopping transmission!")
        static.TNC_STATE = "IDLE"
        static.ARQ_STATE = False
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            status="stopped",
            uuid=self.transmission_uuid,
        )
        self.arq_cleanup()

    # ----------- BROADCASTS
    def run_beacon(self) -> None:
        """
        Controlling function for running a beacon
        Args:

          self: arq class

        Returns:

        """
        try:
            while True:
                threading.Event().wait(0.5)
                while static.BEACON_STATE:
                    if (
                            not static.ARQ_SESSION
                            and not self.arq_file_transfer
                            and not static.BEACON_PAUSE
                    ):
                        self.send_data_to_socket_queue(
                            freedata="tnc-message",
                            beacon="transmitting",
                            dxcallsign="None",
                            interval=self.beacon_interval,
                        )
                        self.log.info(
                            "[TNC] Sending beacon!", interval=self.beacon_interval
                        )

                        beacon_frame = bytearray(self.length_sig0_frame)
                        beacon_frame[:1] = bytes([FR_TYPE.BEACON.value])
                        beacon_frame[1:7] = helpers.callsign_to_bytes(self.mycallsign)
                        beacon_frame[9:13] = static.MYGRID[:4]
                        self.log.info("[TNC] ENABLE FSK", state=static.ENABLE_FSK)

                        if static.ENABLE_FSK:
                            self.enqueue_frame_for_tx(
                                [beacon_frame],
                                c2_mode=FREEDV_MODE.fsk_ldpc_0.value,
                            )
                        else:
                            self.enqueue_frame_for_tx([beacon_frame], c2_mode=FREEDV_MODE.datac0.value, copies=1,
                                                      repeat_delay=0)

                    interval_timer = time.time() + self.beacon_interval
                    while (
                            time.time() < interval_timer
                            and static.BEACON_STATE
                            and not static.BEACON_PAUSE
                    ):
                        threading.Event().wait(0.01)

        except Exception as err:
            self.log.debug("[TNC] run_beacon: ", exception=err)

    def received_beacon(self, data_in: bytes) -> None:
        """
        Called if we received a beacon
        Args:
          data_in:bytes:

        """
        # here we add the received station to the heard stations buffer
        beacon_callsign = helpers.bytes_to_callsign(bytes(data_in[1:7]))
        dxgrid = bytes(data_in[9:13]).rstrip(b"\x00")

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            beacon="received",
            uuid=str(uuid.uuid4()),
            timestamp=int(time.time()),
            dxcallsign=str(beacon_callsign, "UTF-8"),
            dxgrid=str(dxgrid, "UTF-8"),
            snr=str(static.SNR),
        )

        self.log.info(
            "[TNC] BEACON RCVD ["
            + str(beacon_callsign, "UTF-8")
            + "]["
            + str(dxgrid, "UTF-8")
            + "] ",
            snr=static.SNR,
        )
        helpers.add_to_heard_stations(
            beacon_callsign,
            dxgrid,
            "BEACON",
            static.SNR,
            static.FREQ_OFFSET,
            static.HAMLIB_FREQUENCY,
        )

    def transmit_cq(self) -> None:
        """
        Transmit a CQ
        Args:
            self

        Returns:
            Nothing
        """
        self.log.info("[TNC] CQ CQ CQ")
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            cq="transmitting",
            mycallsign=str(self.mycallsign, "UTF-8"),
            dxcallsign="None",
        )
        cq_frame = bytearray(self.length_sig0_frame)
        cq_frame[:1] = bytes([FR_TYPE.CQ.value])
        cq_frame[1:7] = helpers.callsign_to_bytes(self.mycallsign)
        cq_frame[7:11] = helpers.encode_grid(static.MYGRID.decode("UTF-8"))

        self.log.info("[TNC] ENABLE FSK", state=static.ENABLE_FSK)
        self.log.debug("[TNC] CQ Frame:", data=[cq_frame])

        if static.ENABLE_FSK:
            self.enqueue_frame_for_tx([cq_frame], c2_mode=FREEDV_MODE.fsk_ldpc_0.value)
        else:
            self.enqueue_frame_for_tx([cq_frame], c2_mode=FREEDV_MODE.datac0.value, copies=1, repeat_delay=0)

    def received_cq(self, data_in: bytes) -> None:
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
        dxgrid = bytes(helpers.decode_grid(data_in[7:11]), "UTF-8")
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            cq="received",
            mycallsign=str(self.mycallsign, "UTF-8"),
            dxcallsign=str(dxcallsign, "UTF-8"),
            dxgrid=str(static.DXGRID, "UTF-8"),
        )
        self.log.info(
            "[TNC] CQ RCVD ["
            + str(dxcallsign, "UTF-8")
            + "]["
            + str(dxgrid, "UTF-8")
            + "] ",
            snr=static.SNR,
        )
        helpers.add_to_heard_stations(
            dxcallsign,
            dxgrid,
            "CQ CQ CQ",
            static.SNR,
            static.FREQ_OFFSET,
            static.HAMLIB_FREQUENCY,
        )

        if static.RESPOND_TO_CQ and static.RESPOND_TO_CALL:
            self.transmit_qrv(dxcallsign)

    def transmit_qrv(self, dxcallsign: bytes) -> None:
        """
        Called when we send a QRV frame
        Args:
          self,
          dxcallsign

        """
        # Sleep a random amount of time before responding to make it more likely to be
        # heard when many stations respond. Each DATAC0 frame is 0.44 sec (440ms) in
        # duration, plus overhead. Set the wait interval to be random between 0 and 2s
        # in 0.5s increments.
        helpers.wait(randrange(0, 20, 5) / 10.0)
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            qrv="transmitting",
            dxcallsign=str(dxcallsign, "UTF-8"),
        )
        self.log.info("[TNC] Sending QRV!")

        qrv_frame = bytearray(self.length_sig0_frame)
        qrv_frame[:1] = bytes([FR_TYPE.QRV.value])
        qrv_frame[1:7] = helpers.callsign_to_bytes(self.mycallsign)
        qrv_frame[7:11] = helpers.encode_grid(static.MYGRID.decode("UTF-8"))

        self.log.info("[TNC] ENABLE FSK", state=static.ENABLE_FSK)

        if static.ENABLE_FSK:
            self.enqueue_frame_for_tx([qrv_frame], c2_mode=FREEDV_MODE.fsk_ldpc_0.value)
        else:
            self.enqueue_frame_for_tx([qrv_frame], c2_mode=FREEDV_MODE.datac0.value, copies=1, repeat_delay=0)

    def received_qrv(self, data_in: bytes) -> None:
        """
        Called when we receive a QRV frame
        Args:
          data_in:bytes:

        """
        # here we add the received station to the heard stations buffer
        dxcallsign = helpers.bytes_to_callsign(bytes(data_in[1:7]))
        dxgrid = bytes(helpers.decode_grid(data_in[7:11]), "UTF-8")

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            qrv="received",
            dxcallsign=str(dxcallsign, "UTF-8"),
            dxgrid=str(dxgrid, "UTF-8")
        )

        self.log.info(
            "[TNC] QRV RCVD ["
            + str(dxcallsign, "UTF-8")
            + "]["
            + str(dxgrid, "UTF-8")
            + "] ",
            snr=static.SNR,
        )
        helpers.add_to_heard_stations(
            dxcallsign,
            dxgrid,
            "QRV",
            static.SNR,
            static.FREQ_OFFSET,
            static.HAMLIB_FREQUENCY,
        )

    # ------------ CALCULATE TRANSFER RATES
    def calculate_transfer_rate_rx(
            self, rx_start_of_transmission: float, receivedbytes: int
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
            if static.TOTAL_BYTES == 0:
                static.TOTAL_BYTES = 1
            static.ARQ_TRANSMISSION_PERCENT = min(
                int(
                    (
                            receivedbytes
                            * static.ARQ_COMPRESSION_FACTOR
                            / static.TOTAL_BYTES
                    )
                    * 100
                ),
                100,
            )

            transmissiontime = time.time() - self.rx_start_of_transmission

            if receivedbytes > 0:
                static.ARQ_BITS_PER_SECOND = int((receivedbytes * 8) / transmissiontime)
                static.ARQ_BYTES_PER_MINUTE = int(
                    receivedbytes / (transmissiontime / 60)
                )

            else:
                static.ARQ_BITS_PER_SECOND = 0
                static.ARQ_BYTES_PER_MINUTE = 0
        except Exception as err:
            self.log.error(f"[TNC] calculate_transfer_rate_rx: Exception: {err}")
            static.ARQ_TRANSMISSION_PERCENT = 0.0
            static.ARQ_BITS_PER_SECOND = 0
            static.ARQ_BYTES_PER_MINUTE = 0

        return [
            static.ARQ_BITS_PER_SECOND,
            static.ARQ_BYTES_PER_MINUTE,
            static.ARQ_TRANSMISSION_PERCENT,
        ]

    def reset_statistics(self) -> None:
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
            static.ARQ_TRANSMISSION_PERCENT = min(
                int((sentbytes / tx_buffer_length) * 100), 100
            )

            transmissiontime = time.time() - tx_start_of_transmission

            if sentbytes > 0:
                static.ARQ_BITS_PER_SECOND = int((sentbytes * 8) / transmissiontime)
                static.ARQ_BYTES_PER_MINUTE = int(sentbytes / (transmissiontime / 60))

            else:
                static.ARQ_BITS_PER_SECOND = 0
                static.ARQ_BYTES_PER_MINUTE = 0

        except Exception as err:
            self.log.error(f"[TNC] calculate_transfer_rate_tx: Exception: {err}")
            static.ARQ_TRANSMISSION_PERCENT = 0.0
            static.ARQ_BITS_PER_SECOND = 0
            static.ARQ_BYTES_PER_MINUTE = 0

        return [
            static.ARQ_BITS_PER_SECOND,
            static.ARQ_BYTES_PER_MINUTE,
            static.ARQ_TRANSMISSION_PERCENT,
        ]

    # ----------------------CLEANUP AND RESET FUNCTIONS
    def arq_cleanup(self) -> None:
        """
        Cleanup function which clears all ARQ states
        """
        if TESTMODE:
            self.log.debug("[TNC] TESTMODE: arq_cleanup: Not performing cleanup.")
            return

        self.log.debug("[TNC] arq_cleanup")

        self.session_id = bytes(1)
        self.rx_frame_bof_received = False
        self.rx_frame_eof_received = False
        self.burst_ack = False
        self.rpt_request_received = False
        self.data_frame_ack_received = False
        static.RX_BURST_BUFFER = []
        static.RX_FRAME_BUFFER = b""
        self.burst_ack_snr = 255

        # reset modem receiving state to reduce cpu load
        modem.RECEIVE_SIG0 = True
        modem.RECEIVE_SIG1 = False
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

        # reset max retries possibly overriden by api
        self.session_connect_max_retries = 15
        self.data_channel_max_retries = 15

        if not static.ARQ_SESSION:
            static.TNC_STATE = "IDLE"
            self.dxcallsign = b"AA0AA-0"
            self.mycallsign = static.MYCALLSIGN

        static.ARQ_STATE = False
        self.arq_file_transfer = False

        static.BEACON_PAUSE = False

    def arq_reset_ack(self, state: bool) -> None:
        """
        Funktion for resetting acknowledge states
        Args:
          state:bool:

        """
        self.burst_ack = state
        self.rpt_request_received = state
        self.data_frame_ack_received = state

    def set_listening_modes(self, enable_sig0: bool, enable_sig1: bool, mode: int) -> None:
        """
        Function for setting the data modes we are listening to for saving cpu power

        Args:
          enable_sig0:int: Enable/Disable signalling mode 0
          enable_sig1:int: Enable/Disable signalling mode 1
          mode:int: Codec2 mode to listen for

        """
        # set modes we want to listen to
        modem.RECEIVE_SIG0 = enable_sig0
        modem.RECEIVE_SIG1 = enable_sig1

        if mode == FREEDV_MODE.datac1.value:
            modem.RECEIVE_DATAC1 = True
            modem.RECEIVE_DATAC3 = False
            modem.RECEIVE_FSK_LDPC_1 = False
            self.log.debug("[TNC] Changing listening data mode", mode="datac1")
        elif mode == FREEDV_MODE.datac3.value:
            modem.RECEIVE_DATAC1 = False
            modem.RECEIVE_DATAC3 = True
            modem.RECEIVE_FSK_LDPC_1 = False
            self.log.debug("[TNC] Changing listening data mode", mode="datac3")
        elif mode == FREEDV_MODE.fsk_ldpc_1.value:
            modem.RECEIVE_DATAC1 = False
            modem.RECEIVE_DATAC3 = False
            modem.RECEIVE_FSK_LDPC_1 = True
            self.log.debug("[TNC] Changing listening data mode", mode="fsk_ldpc_1")
        else:
            modem.RECEIVE_DATAC1 = True
            modem.RECEIVE_DATAC3 = True
            modem.RECEIVE_FSK_LDPC_1 = True
            self.log.debug(
                "[TNC] Changing listening data mode", mode="datac1/datac3/fsk_ldpc"
            )

    # ------------------------- WATCHDOG FUNCTIONS FOR TIMER
    def watchdog(self) -> None:
        """Author: DJ2LS

        Watchdog master function. From here, "pet" the watchdogs

        """
        while True:
            threading.Event().wait(0.1)
            self.data_channel_keep_alive_watchdog()
            self.burst_watchdog()
            self.arq_session_keep_alive_watchdog()

    def burst_watchdog(self) -> None:
        """
        Watchdog which checks if we are running into a connection timeout
        DATA BURST
        """
        # IRS SIDE
        # TODO: We need to redesign this part for cleaner state handling
        # Return if not ARQ STATE and not ARQ SESSION STATE as they are different use cases
        if (
                not static.ARQ_STATE
                and static.ARQ_SESSION_STATE != "connected"
                or not self.is_IRS
        ):
            return

        # get modem error state
        modem_error_state = modem.get_modem_error_state()

        # We want to reach this state only if connected ( == return above not called )
        if (
                self.data_channel_last_received + self.time_list[self.speed_level]
                <= time.time() or modem_error_state
        ):
            if modem_error_state:
                self.log.warning(
                    "[TNC] Decoding Error",
                    attempt=self.n_retries_per_burst,
                    max_attempts=self.rx_n_max_retries_per_burst,
                    speed_level=self.speed_level,
                )
            else:
                self.log.warning(
                    "[TNC] Frame timeout",
                    attempt=self.n_retries_per_burst,
                    max_attempts=self.rx_n_max_retries_per_burst,
                    speed_level=self.speed_level,
                )
            # reduce speed level if nack counter increased
            self.frame_received_counter = 0
            self.burst_nack_counter += 1
            if self.burst_nack_counter >= 2:
                self.burst_nack_counter = 0
                self.speed_level = max(self.speed_level - 1, 0)
                static.ARQ_SPEED_LEVEL = self.speed_level

            # Update modes we are listening to
            self.set_listening_modes(True, True, self.mode_list[self.speed_level])

            # Why not pass `snr` or `static.SNR`?
            self.send_burst_nack_frame_watchdog(0)

            # Update data_channel timestamp
            self.data_channel_last_received = time.time()
            self.n_retries_per_burst += 1
        else:
            # print((self.data_channel_last_received + self.time_list[self.speed_level])-time.time())
            pass

        if self.n_retries_per_burst >= self.rx_n_max_retries_per_burst:
            self.stop_transmission()
            self.arq_cleanup()

    def data_channel_keep_alive_watchdog(self) -> None:
        """
        watchdog which checks if we are running into a connection timeout
        DATA CHANNEL
        """
        # and not static.ARQ_SEND_KEEP_ALIVE:
        if static.ARQ_STATE and static.TNC_STATE == "BUSY":
            threading.Event().wait(0.01)
            if (
                    self.data_channel_last_received + self.transmission_timeout
                    > time.time()
            ):

                timeleft = (self.data_channel_last_received + self.transmission_timeout) - time.time()
                self.log.debug("Time left until timeout", seconds=timeleft)
                threading.Event().wait(5)
                # print(self.data_channel_last_received + self.transmission_timeout - time.time())
                # pass
            else:
                # Clear the timeout timestamp
                self.data_channel_last_received = 0
                self.log.info(
                    "[TNC] DATA ["
                    + str(self.mycallsign, "UTF-8")
                    + "]<<T>>["
                    + str(static.DXCALLSIGN, "UTF-8")
                    + "]"
                )
                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    arq="transmission",
                    status="failed",
                    uuid=self.transmission_uuid,
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                )
                self.arq_cleanup()

    def arq_session_keep_alive_watchdog(self) -> None:
        """
        watchdog which checks if we are running into a connection timeout
        ARQ SESSION
        """
        if (
                static.ARQ_SESSION
                and static.TNC_STATE == "BUSY"
                and not self.arq_file_transfer
        ):
            if self.arq_session_last_received + self.arq_session_timeout > time.time():
                threading.Event().wait(0.01)
            else:
                self.log.info(
                    "[TNC] SESSION ["
                    + str(self.mycallsign, "UTF-8")
                    + "]<<T>>["
                    + str(self.dxcallsign, "UTF-8")
                    + "]"
                )
                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    arq="session",
                    status="failed",
                    reason="timeout",
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                )
                self.close_session()

    def heartbeat(self) -> None:
        """
        Heartbeat thread which auto pauses and resumes the heartbeat signal when in an arq session
        """
        while True:
            threading.Event().wait(0.01)
            # additional check for smoother stopping if heartbeat transmission
            while not self.arq_file_transfer:
                threading.Event().wait(0.01)
                if (
                        static.ARQ_SESSION
                        and self.IS_ARQ_SESSION_MASTER
                        and static.ARQ_SESSION_STATE == "connected"
                        # and not self.arq_file_transfer
                ):
                    threading.Event().wait(1)
                    self.transmit_session_heartbeat()
                    threading.Event().wait(2)

    def send_test_frame(self) -> None:
        """Send an empty test frame"""
        self.enqueue_frame_for_tx(
            frame_to_tx=[bytearray(126)], c2_mode=FREEDV_MODE.datac3.value
        )
