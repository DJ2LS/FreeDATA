# -*- coding: UTF-8 -*-
"""
Created on Sun Dec 27 20:43:40 2020

@author: DJ2LS
"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init

import os
import base64
import sys
import threading
import time
import uuid
import lzma
from random import randrange

import codec2
import helpers
import modem
import numpy as np
import sock
from static import ARQ, AudioParam, Beacon, Channel, Daemon, HamlibParam, ModemParam, Station, Statistics, TCIParam, TNC
import structlog
import stats
import ujson as json
from codec2 import FREEDV_MODE, FREEDV_MODE_USED_SLOTS
from queues import DATA_QUEUE_RECEIVED, DATA_QUEUE_TRANSMIT, RX_BUFFER
from static import FRAME_TYPE as FR_TYPE
import broadcast

TESTMODE = False


class DATA:
    """Terminal Node Controller for FreeDATA"""

    log = structlog.get_logger("DATA")

    def __init__(self) -> None:

        self.stats = stats.stats()

        # Initial call sign. Will be overwritten later
        self.mycallsign = Station.mycallsign
        self.dxcallsign = Station.dxcallsign

        self.data_queue_transmit = DATA_QUEUE_TRANSMIT
        self.data_queue_received = DATA_QUEUE_RECEIVED

        # length of signalling frame
        self.length_sig0_frame = 14
        self.length_sig1_frame = 14

        # duration of signalling frame
        self.duration_sig0_frame = 2.3
        self.duration_sig1_frame = 2.3
        self.longest_duration = 5.8  # datac5

        # hold session id
        self.session_id = bytes(1)

        # ------- ARQ SESSION
        self.arq_file_transfer = False
        self.IS_ARQ_SESSION_MASTER = False
        self.arq_session_last_received = 0
        self.arq_session_timeout = 30
        self.session_connect_max_retries = 15
        self.irs_buffer_position = 0

        # actual n retries of burst
        self.tx_n_retry_of_burst = 0

        self.transmission_uuid = ""

        self.burst_last_received = 0.0  # time of last "live sign" of a burst
        self.data_channel_last_received = 0.0  # time of last "live sign" of a frame
        self.burst_ack_snr = 0  # SNR from received burst ack frames

        # Flag to indicate if we received an ACK frame for a burst
        self.burst_ack = False
        # Flag to indicate if we received an ACK frame for a data frame
        self.data_frame_ack_received = False
        # Flag to indicate if we received a request for repeater frames
        self.rpt_request_received = False
        self.rpt_request_buffer = []  # requested frames, saved in a list
        self.burst_rpt_counter = 0

        self.rx_start_of_transmission = 0  # time of transmission start

        # 3 bytes for the BOF Beginning of File indicator in a data frame
        self.data_frame_bof = b"BOF"
        # 3 bytes for the EOF End of File indicator in a data frame
        self.data_frame_eof = b"EOF"

        self.tx_n_max_retries_per_burst = 40
        self.rx_n_max_retries_per_burst = 40
        self.n_retries_per_burst = 0
        self.rx_n_frame_of_burst = 0
        self.rx_n_frames_per_burst = 0
        self.max_n_frames_per_burst = 1

        self.broadcast = broadcast.broadcastHandler()

        # Flag to indicate if we received a low bandwidth mode channel opener
        self.received_LOW_BANDWIDTH_MODE = False

        self.data_channel_max_retries = 15
        self.datachannel_timeout = False

        # -------------- AVAILABLE MODES START-----------
        # IMPORTANT: LISTS MUST BE OF EQUAL LENGTH

        # --------------------- LOW BANDWIDTH

        # List of codec2 modes to use in "low bandwidth" mode.
        self.mode_list_low_bw = [
            FREEDV_MODE.datac4.value,
        ]
        # List for minimum SNR operating level for the corresponding mode in self.mode_list
        self.snr_list_low_bw = [-100]
        # List for time to wait for corresponding mode in seconds
        self.time_list_low_bw = [6 + self.duration_sig0_frame + 1]

        # --------------------- HIGH BANDWIDTH

        # List of codec2 modes to use in "high bandwidth" mode.
        self.mode_list_high_bw = [
            FREEDV_MODE.datac4.value,
            FREEDV_MODE.datac3.value,
            FREEDV_MODE.datac1.value,
        ]
        # List for minimum SNR operating level for the corresponding mode in self.mode_list
        self.snr_list_high_bw = [-100, 0, 3]
        # List for time to wait for corresponding mode in seconds
        # test with 6,7 --> caused sometimes a frame timeout if ack frame takes longer
        # TODO: Need to check why ACK frames needs more time
        # TODO: Adjust these times
        self.time_list_high_bw = [6 + self.duration_sig0_frame + 1, 6 + self.duration_sig0_frame + 1, 6 + self.duration_sig0_frame + 1]
        # -------------- AVAILABLE MODES END-----------

        # Mode list for selecting between low bandwidth ( 500Hz ) and modes with higher bandwidth
        # but ability to fall back to low bandwidth modes if needed.
        if TNC.low_bandwidth_mode:
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
        ARQ.arq_speed_level = self.speed_level

        # minimum payload for arq burst
        # import for avoiding byteorder bug and buffer search area
        self.arq_burst_header_size = 3
        self.arq_burst_minimum_payload = 56 - self.arq_burst_header_size
        self.arq_burst_maximum_payload = 510 - self.arq_burst_header_size
        # save last used payload for optimising buffer search area
        self.arq_burst_last_payload = self.arq_burst_maximum_payload

        self.is_IRS = False
        self.burst_nack = False
        self.burst_nack_counter = 0
        self.frame_nack_counter = 0
        self.frame_received_counter = 0

        self.rx_frame_bof_received = False
        self.rx_frame_eof_received = False

        # TIMEOUTS
        self.burst_ack_timeout_seconds = 4.5  # timeout for burst  acknowledges
        self.data_frame_ack_timeout_seconds = 4.5  # timeout for data frame acknowledges
        self.rpt_ack_timeout_seconds = 4.5  # timeout for rpt frame acknowledges
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
            FR_TYPE.IS_WRITING.value: (self.received_is_writing, "IS_WRITING"),
            FR_TYPE.FEC.value: (self.broadcast.received_fec, "FEC"),
            FR_TYPE.FEC_WAKEUP.value: (self.broadcast.received_fec_wakeup, "FEC WAKEUP"),

        }
        self.command_dispatcher = {
            # "CONNECT": (self.arq_session_handler, "CONNECT"),
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
        self.beacon_interval_timer = 0
        self.beacon_thread = threading.Thread(
            target=self.run_beacon, name="watchdog", daemon=True
        )
        self.beacon_thread.start()

    def worker_transmit(self) -> None:
        """Dispatch incoming UI instructions for transmitting operations"""
        while True:
            data = self.data_queue_transmit.get()

            # if we are already in ARQ_STATE, or we're receiving codec2 traffic
            # let's wait with processing data
            # this should avoid weird toggle states where both stations
            # stuck in IRS
            #
            # send transmission queued information once
            if ARQ.arq_state or ModemParam.is_codec2_traffic:
                self.log.debug(
                    "[TNC] TX DISPATCHER - waiting with processing command ",
                    arq_state=ARQ.arq_state,
                )

                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    command=data[0],
                    status="queued",
                )

                # now stay in while loop until state released
                while ARQ.arq_state or ModemParam.is_codec2_traffic:
                    threading.Event().wait(0.01)

                # and finally sleep some time
                threading.Event().wait(1.0)

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
                    Beacon.beacon_state = True
                else:
                    Beacon.beacon_state = False

            elif data[0] == "ARQ_RAW":
                # [1] DATA_OUT bytes
                # [2] self.transmission_uuid str
                # [3] mycallsign with ssid
                # [4] dxcallsign with ssid
                # [5] attempts
                self.open_dc_and_transmit(data[1], data[2], data[3], data[4], data[5])


            elif data[0] == "FEC_IS_WRITING":
                # [1] DATA_OUT bytes
                # [2] MODE str datac0/1/3...
                self.send_fec_is_writing(data[1])

            elif data[0] == "FEC":
                # [1] WAKEUP bool
                # [2] MODE str datac0/1/3...
                # [3] PAYLOAD
                # [4] MYCALLSIGN
                self.send_fec(data[1], data[2], data[3], data[4])
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
            FR_TYPE.IS_WRITING.value,
            FR_TYPE.FEC.value,
            FR_TYPE.FEC_WAKEUP.value,
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
                snr = ModemParam.snr
                self.log.debug("[TNC] RX SNR", snr=snr)
                # send payload data to arq checker without CRC16
                self.arq_data_received(
                    bytes(bytes_out[:-2]), bytes_per_frame, snr, freedv
                )

                # if we received the last frame of a burst or the last remaining rpt frame, do a modem unsync
                # if ARQ.rx_burst_buffer.count(None) <= 1 or (frame+1) == n_frames_per_burst:
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
            frame_to_tx,  # : list[bytearray], # this causes a crash on python 3.7
            c2_mode=FREEDV_MODE.sig0.value,
            copies=1,
            repeat_delay=0,
    ) -> None:
        """
        Send (transmit) supplied frame to TNC

        :param frame_to_tx: Frame data to send
        :type frame_to_tx: list of bytearrays
        :param c2_mode: Codec2 mode to use, defaults to datac13
        :type c2_mode: int, optional
        :param copies: Number of frame copies to send, defaults to 1
        :type copies: int, optional
        :param repeat_delay: Delay time before sending repeat frame, defaults to 0
        :type repeat_delay: int, optional
        """
        #print(frame_to_tx[0])
        #print(frame_to_tx)
        frame_type = FR_TYPE(int.from_bytes(frame_to_tx[0][:1], byteorder="big")).name
        self.log.debug("[TNC] enqueue_frame_for_tx", c2_mode=FREEDV_MODE(c2_mode).name, data=frame_to_tx,
                       type=frame_type)

        # Set the TRANSMITTING flag before adding an object to the transmit queue
        # TODO: This is not that nice, we could improve this somehow
        TNC.transmitting = True
        modem.MODEM_TRANSMIT_QUEUE.put([c2_mode, copies, repeat_delay, frame_to_tx])

        # Wait while transmitting
        while TNC.transmitting:
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
                dxcallsign=str(Station.dxcallsign, "UTF-8"),
                dxgrid=str(Station.dxgrid, "UTF-8"),
                data=base64_data,
            )
        """

        # add mycallsign and dxcallsign to network message if they not exist
        # and make sure we are not overwrite them if they exist
        try:
            if "mycallsign" not in jsondata:
                jsondata["mycallsign"] = str(self.mycallsign, "UTF-8")
            if "dxcallsign" not in jsondata:
                jsondata["dxcallsign"] = str(Station.dxcallsign, "UTF-8")
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
            self.enqueue_frame_for_tx([ident_frame], c2_mode=FREEDV_MODE.sig0.value)
        else:
            return ident_frame

    def send_burst_ack_frame(self, snr) -> None:
        """Build and send ACK frame for burst DATA frame"""

        ack_frame = bytearray(self.length_sig1_frame)
        ack_frame[:1] = bytes([FR_TYPE.BURST_ACK.value])
        ack_frame[1:2] = self.session_id
        ack_frame[2:3] = helpers.snr_to_bytes(snr)
        ack_frame[3:4] = bytes([int(self.speed_level)])
        ack_frame[4:8] = len(ARQ.rx_frame_buffer).to_bytes(4, byteorder="big")

        # wait while timeout not reached and our busy state is busy
        channel_busy_timeout = time.time() + 5
        while ModemParam.channel_busy and time.time() < channel_busy_timeout and not self.check_if_mode_fits_to_busy_slot():
            threading.Event().wait(0.01)

        # Transmit frame
        self.enqueue_frame_for_tx([ack_frame], c2_mode=FREEDV_MODE.sig1.value)

    def send_data_ack_frame(self, snr) -> None:
        """Build and send ACK frame for received DATA frame"""

        ack_frame = bytearray(self.length_sig1_frame)
        ack_frame[:1] = bytes([FR_TYPE.FR_ACK.value])
        ack_frame[1:2] = self.session_id
        ack_frame[2:3] = helpers.snr_to_bytes(snr)

        # wait while timeout not reached and our busy state is busy
        channel_busy_timeout = time.time() + 5
        while ModemParam.channel_busy and time.time() < channel_busy_timeout and not self.check_if_mode_fits_to_busy_slot():
            threading.Event().wait(0.01)

        # reset burst timeout in case we had to wait too long
        self.burst_last_received = time.time() + channel_busy_timeout + 8
        # Transmit frame
        # TODO: Do we have to send , self.send_ident_frame(False) ?
        # self.enqueue_frame_for_tx([ack_frame, self.send_ident_frame(False)], c2_mode=FREEDV_MODE.sig1.value, copies=3, repeat_delay=0)
        self.enqueue_frame_for_tx([ack_frame], c2_mode=FREEDV_MODE.sig1.value, copies=3, repeat_delay=0)

    def send_retransmit_request_frame(self) -> None:
        # check where a None is in our burst buffer and do frame+1, because lists start at 0
        # FIXME: Check to see if there's a `frame - 1` in the receive portion. Remove both if there is.
        #print(ARQ.rx_burst_buffer)
        missing_frames = [
            frame + 1
            for frame, element in enumerate(ARQ.rx_burst_buffer)
            if element is None
        ]

        rpt_frame = bytearray(self.length_sig1_frame)
        rpt_frame[:1] = bytes([FR_TYPE.FR_REPEAT.value])
        rpt_frame[1:2] = self.session_id
        rpt_frame[2:2 + len(missing_frames)] = missing_frames

        self.log.info("[TNC] ARQ | RX | Requesting", frames=missing_frames)
        # Transmit frame
        self.enqueue_frame_for_tx([rpt_frame], c2_mode=FREEDV_MODE.sig1.value, copies=1, repeat_delay=0)

    def send_burst_nack_frame(self, snr: bytes) -> None:
        """Build and send NACK frame for received DATA frame"""

        nack_frame = bytearray(self.length_sig1_frame)
        nack_frame[:1] = bytes([FR_TYPE.FR_NACK.value])
        nack_frame[1:2] = self.session_id
        nack_frame[2:3] = helpers.snr_to_bytes(snr)
        nack_frame[3:4] = bytes([int(self.speed_level)])
        nack_frame[4:8] = len(ARQ.rx_frame_buffer).to_bytes(4, byteorder="big")

        # TRANSMIT NACK FRAME FOR BURST
        # TODO: Do we have to send ident frame?
        # self.enqueue_frame_for_tx([ack_frame, self.send_ident_frame(False)], c2_mode=FREEDV_MODE.sig1.value, copies=3, repeat_delay=0)

        # wait while timeout not reached and our busy state is busy
        channel_busy_timeout = time.time() + 5
        while ModemParam.channel_busy and time.time() < channel_busy_timeout and not self.check_if_mode_fits_to_busy_slot():
            threading.Event().wait(0.01)

        self.enqueue_frame_for_tx([nack_frame], c2_mode=FREEDV_MODE.sig1.value, copies=3, repeat_delay=0)
        # reset burst timeout in case we had to wait too long
        self.burst_last_received = time.time()

    def send_burst_nack_frame_watchdog(self, snr: bytes, tx_n_frames_per_burst) -> None:
        """Build and send NACK frame for watchdog timeout"""

        # increment nack counter for transmission stats
        self.frame_nack_counter += 1


        # we need to clear our rx burst buffer
        ARQ.rx_burst_buffer = []

        # Create and send ACK frame
        self.log.info("[TNC] ARQ | RX | SENDING NACK")
        nack_frame = bytearray(self.length_sig1_frame)
        nack_frame[:1] = bytes([FR_TYPE.BURST_NACK.value])
        nack_frame[1:2] = self.session_id
        nack_frame[2:3] = helpers.snr_to_bytes(snr)
        nack_frame[3:4] = bytes([int(self.speed_level)])
        nack_frame[4:5] = bytes([int(tx_n_frames_per_burst)])
        nack_frame[5:9] = len(ARQ.rx_frame_buffer).to_bytes(4, byteorder="big")


        # wait while timeout not reached and our busy state is busy
        channel_busy_timeout = time.time() + 5 + 5
        while ModemParam.channel_busy and time.time() < channel_busy_timeout and not self.check_if_mode_fits_to_busy_slot():
            threading.Event().wait(0.01)

        # TRANSMIT NACK FRAME FOR BURST
        self.enqueue_frame_for_tx([nack_frame], c2_mode=FREEDV_MODE.sig1.value, copies=1, repeat_delay=0)

        # reset frame counter for not increasing speed level
        self.frame_received_counter = 0

    def send_disconnect_frame(self) -> None:
        """Build and send a disconnect frame"""
        disconnection_frame = bytearray(self.length_sig1_frame)
        disconnection_frame[:1] = bytes([FR_TYPE.ARQ_SESSION_CLOSE.value])
        disconnection_frame[1:2] = self.session_id
        disconnection_frame[2:5] = Station.dxcallsign_crc
        # TODO: Needed? disconnection_frame[7:13] = helpers.callsign_to_bytes(self.mycallsign)
        # self.enqueue_frame_for_tx([disconnection_frame, self.send_ident_frame(False)], c2_mode=FREEDV_MODE.sig0.value, copies=5, repeat_delay=0)
        # TODO: We need to add the ident frame feature with a seperate PR after publishing latest protocol
        # TODO: We need to wait some time between last arq related signalling frame and ident frame
        # TODO: Maybe about 500ms - 1500ms to avoid confusion and too much PTT toggles

        # wait while timeout not reached and our busy state is busy
        channel_busy_timeout = time.time() + 5
        while ModemParam.channel_busy and time.time() < channel_busy_timeout and not self.check_if_mode_fits_to_busy_slot():
            threading.Event().wait(0.01)

        self.enqueue_frame_for_tx([disconnection_frame], c2_mode=FREEDV_MODE.sig0.value, copies=3, repeat_delay=0)

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

        # only process data if we are in ARQ and BUSY state else return to quit
        if not ARQ.arq_state and TNC.tnc_state not in ["BUSY"]:
            self.log.warning("[TNC] wrong tnc state - dropping data", arq_state=ARQ.arq_state,
                             tnc_state=TNC.tnc_state)
            return

        self.arq_file_transfer = True

        TNC.tnc_state = "BUSY"
        ARQ.arq_state = True

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
        if len(ARQ.rx_burst_buffer) != self.rx_n_frames_per_burst:
            ARQ.rx_burst_buffer = [None] * self.rx_n_frames_per_burst

        # Append data to rx burst buffer
        ARQ.rx_burst_buffer[self.rx_n_frame_of_burst] = data_in[self.arq_burst_header_size:]  # type: ignore

        Station.dxgrid = b'------'
        helpers.add_to_heard_stations(
            Station.dxcallsign,
            Station.dxgrid,
            "DATA-CHANNEL",
            snr,
            ModemParam.frequency_offset,
            HamlibParam.hamlib_frequency,
        )

        # Check if we received all frames in the burst by checking if burst buffer has no more "Nones"
        # This is the ideal case because we received all data
        if None not in ARQ.rx_burst_buffer:
            # then iterate through burst buffer and stick the burst together
            # the temp burst buffer is needed for checking, if we already received data
            temp_burst_buffer = b""
            for value in ARQ.rx_burst_buffer:
                # ARQ.rx_frame_buffer += ARQ.rx_burst_buffer[i]
                temp_burst_buffer += bytes(value)  # type: ignore

            # free up burst buffer
            ARQ.rx_burst_buffer = []

            # TODO: Needs to be removed as soon as mode error is fixed
            # catch possible modem error which leads into false byteorder
            # modem possibly decodes too late - data then is pushed to buffer
            # which leads into wrong byteorder
            # Lets put this in try/except so we are not crashing tnc as its highly experimental
            # This might only work for datac1 and datac3
            try:
                # area_of_interest = (modem.get_bytes_per_frame(self.mode_list[speed_level] - 1) -3) * 2
                if ARQ.rx_frame_buffer.endswith(temp_burst_buffer[:246]) and len(temp_burst_buffer) >= 246:
                    self.log.warning(
                        "[TNC] ARQ | RX | wrong byteorder received - dropping data"
                    )
                    # we need to run a return here, so we are not sending an ACK
                    # return
            except Exception as e:
                self.log.warning(
                    "[TNC] ARQ | RX | wrong byteorder check failed", e=e
                )

            self.log.debug("[TNC] temp_burst_buffer", buffer=temp_burst_buffer)
            self.log.debug("[TNC] ARQ.rx_frame_buffer", buffer=ARQ.rx_frame_buffer)

            # if frame buffer ends not with the current frame, we are going to append new data
            # if data already exists, we received the frame correctly,
            # but the ACK frame didn't receive its destination (ISS)
            if ARQ.rx_frame_buffer.endswith(temp_burst_buffer):
                self.log.info(
                    "[TNC] ARQ | RX | Frame already received - sending ACK again"
                )

            else:
                # Here we are going to search for our data in the last received bytes.
                # This reduces the chance we will lose the entire frame in the case of signalling frame loss

                # ARQ.rx_frame_buffer --> existing data
                # temp_burst_buffer --> new data
                # search_area --> area where we want to search

                search_area = self.arq_burst_last_payload * self.rx_n_frames_per_burst

                search_position = len(ARQ.rx_frame_buffer) - search_area
                # if search position < 0, then search position = 0
                search_position = max(0, search_position)

                # find position of data. returns -1 if nothing found in area else >= 0
                # we are beginning from the end, so if data exists twice or more,
                # only the last one should be replaced
                # we are going to only check position against minimum data frame payload
                # use case: receive data, which already contains received data
                # while the payload of data received before is shorter than actual payload
                get_position = ARQ.rx_frame_buffer[search_position:].rfind(
                    temp_burst_buffer[:self.arq_burst_minimum_payload]
                )
                # if we find data, replace it at this position with the new data and strip it
                if get_position >= 0:
                    ARQ.rx_frame_buffer = ARQ.rx_frame_buffer[
                                             : search_position + get_position
                                             ]
                    self.log.warning(
                        "[TNC] ARQ | RX | replacing existing buffer data",
                        area=search_area,
                        pos=get_position,
                    )
                else:
                    self.log.debug("[TNC] ARQ | RX | appending data to buffer")

                ARQ.rx_frame_buffer += temp_burst_buffer

                self.arq_burst_last_payload = len(temp_burst_buffer)

            # Check if we didn't receive a BOF and EOF yet to avoid sending
            # ack frames if we already received all data
            if (
                    not self.rx_frame_bof_received
                    and not self.rx_frame_eof_received
                    and data_in.find(self.data_frame_eof) < 0
            ):
                self.arq_calculate_speed_level(snr)

                self.data_channel_last_received = int(time.time()) + 6 + 6
                self.burst_last_received = int(time.time()) + 6 + 6
                # Create and send ACK frame
                self.log.info("[TNC] ARQ | RX | SENDING ACK", finished=ARQ.arq_seconds_until_finish,
                              bytesperminute=ARQ.bytes_per_minute)

                self.send_burst_ack_frame(snr)

                # Reset n retries per burst counter
                self.n_retries_per_burst = 0

                # calculate statistics
                self.calculate_transfer_rate_rx(
                    self.rx_start_of_transmission, len(ARQ.rx_frame_buffer)
                )

                # send a network message with information
                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    arq="transmission",
                    status="receiving",
                    uuid=self.transmission_uuid,
                    percent=ARQ.arq_transmission_percent,
                    bytesperminute=ARQ.bytes_per_minute,
                    compression=ARQ.arq_compression_factor,
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                    finished=ARQ.arq_seconds_until_finish,
                    irs=helpers.bool_to_string(self.is_IRS)
                )

        # elif self.rx_n_frame_of_burst == self.rx_n_frames_per_burst:
        #    # We have "Nones" in our rx buffer,
        #    # Check if we received last frame of burst - this is an indicator for missed frames.
        #    # With this way of doing this, we always MUST receive the last
        #    # frame of a burst otherwise the entire burst is lost
        #    # TODO: See if a timeout on the send side with re-transmit last burst would help.
        #    self.log.debug(
        #        "[TNC] last frames of burst received:",
        #        frame=self.rx_n_frame_of_burst,
        #        frames=self.rx_n_frames_per_burst,
        #
        #    )
        #    self.calculate_transfer_rate_rx(
        #        self.rx_start_of_transmission, len(ARQ.rx_frame_buffer)
        #    )

        # elif self.rx_n_frame_of_burst not in [self.rx_n_frames_per_burst - 1]:
        #    self.log.info(
        #        "[TNC] data_handler: received burst",
        #        frame=self.rx_n_frame_of_burst + 1,
        #        frames=self.rx_n_frames_per_burst,
        #    )

        # else:
        #    self.log.error(
        #        "[TNC] data_handler: Should not reach this point...",
        #        frame=self.rx_n_frame_of_burst + 1,
        #        frames=self.rx_n_frames_per_burst,
        #    )
        else:
            self.log.warning(
                "[TNC] data_handler: missing data in burst buffer...",
                frame=self.rx_n_frame_of_burst + 1,
                frames=self.rx_n_frames_per_burst
            )

        # We have a BOF and EOF flag in our data. If we received both we received our frame.
        # In case of loosing data, but we received already a BOF and EOF we need to make sure, we
        # received the complete last burst by checking it for Nones
        bof_position = ARQ.rx_frame_buffer.find(self.data_frame_bof)
        eof_position = ARQ.rx_frame_buffer.find(self.data_frame_eof)

        # get total bytes per transmission information as soon we received a frame with a BOF

        if bof_position >= 0:
            self.arq_extract_statistics_from_data_frame(bof_position, eof_position)
        if (
                bof_position >= 0
                and eof_position > 0
                and None not in ARQ.rx_burst_buffer
        ):
            self.log.debug(
                "[TNC] arq_data_received:",
                bof_position=bof_position,
                eof_position=eof_position,
            )
            self.rx_frame_bof_received = True
            self.rx_frame_eof_received = True

            # Extract raw data from buffer
            payload = ARQ.rx_frame_buffer[
                      bof_position + len(self.data_frame_bof): eof_position
                      ]
            # Get the data frame crc
            data_frame_crc = payload[:4]  # 0:4 = 4 bytes
            # Get the data frame length
            frame_length = int.from_bytes(payload[4:8], "big")  # 4:8 = 4 bytes
            ARQ.total_bytes = frame_length
            # 8:9 = compression factor

            data_frame = payload[9:]
            data_frame_crc_received = helpers.get_crc_32(data_frame)

            # Check if data_frame_crc is equal with received crc
            if data_frame_crc == data_frame_crc_received:
                self.arq_process_received_data_frame(data_frame, snr)
            else:
                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    arq="transmission",
                    status="failed",
                    uuid=self.transmission_uuid,
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                    irs=helpers.bool_to_string(self.is_IRS)
                )

                duration = time.time() - self.rx_start_of_transmission
                self.log.warning(
                    "[TNC] ARQ | RX | DATA FRAME NOT SUCCESSFULLY RECEIVED!",
                    e="wrong crc",
                    expected=data_frame_crc.hex(),
                    received=data_frame_crc_received.hex(),
                    overflows=AudioParam.buffer_overflow_counter,
                    nacks=self.frame_nack_counter,
                    duration=duration,
                    bytesperminute=ARQ.bytes_per_minute,
                    compression=ARQ.arq_compression_factor,
                    data=data_frame,

                )
                if TNC.enable_stats:
                    self.stats.push(frame_nack_counter=self.frame_nack_counter, status="wrong_crc", duration=duration)

                self.log.info("[TNC] ARQ | RX | Sending NACK", finished=ARQ.arq_seconds_until_finish,
                              bytesperminute=ARQ.bytes_per_minute)
                self.send_burst_nack_frame(snr)

            # Update arq_session timestamp
            self.arq_session_last_received = int(time.time())

            # Finally cleanup our buffers and states,
            self.arq_cleanup()

    def arq_extract_statistics_from_data_frame(self, bof_position, eof_position):
        payload = ARQ.rx_frame_buffer[
                  bof_position + len(self.data_frame_bof): eof_position
                  ]
        frame_length = int.from_bytes(payload[4:8], "big")  # 4:8 4bytes
        ARQ.total_bytes = frame_length
        compression_factor = int.from_bytes(payload[8:9], "big")  # 4:8 4bytes
        # limit to max value of 255
        compression_factor = np.clip(compression_factor, 0, 255)
        ARQ.arq_compression_factor = compression_factor / 10
        self.calculate_transfer_rate_rx(
            self.rx_start_of_transmission, len(ARQ.rx_frame_buffer)
        )

    def check_if_mode_fits_to_busy_slot(self):
        """
        Check if actual mode is fitting into given busy state

        Returns:

        """
        mode_name = FREEDV_MODE(self.mode_list[self.speed_level]).name
        mode_slots = FREEDV_MODE_USED_SLOTS[mode_name].value
        if mode_slots in [ModemParam.channel_busy_slot]:
            self.log.warning(
                "[TNC] busy slot detection",
                slots=ModemParam.channel_busy_slot,
                mode_slots=mode_slots,
            )
            return False

        else:
            return True

    def arq_calculate_speed_level(self, snr):
        self.frame_received_counter += 1
        # try increasing speed level only if we had two successful decodes
        if self.frame_received_counter >= 2:
            self.frame_received_counter = 0

            # make sure new speed level isn't higher than available modes
            new_speed_level = min(self.speed_level + 1, len(self.mode_list) - 1)
            # check if actual snr is higher than minimum snr for next mode
            if ModemParam.snr >= self.snr_list[new_speed_level]:
                self.speed_level = new_speed_level


            else:
                self.log.info("[TNC] ARQ | increasing speed level not possible because of SNR limit",
                              given_snr=ModemParam.snr,
                              needed_snr=self.snr_list[new_speed_level]
                              )

            # calculate if speed level fits to busy condition
            if not self.check_if_mode_fits_to_busy_slot():
                self.speed_level = 0

            ARQ.arq_speed_level = self.speed_level

        # Update modes we are listening to
        self.set_listening_modes(False, True, self.mode_list[self.speed_level])

    def arq_process_received_data_frame(self, data_frame, snr):
        """


        """
        # transmittion duration
        duration = time.time() - self.rx_start_of_transmission
        self.calculate_transfer_rate_rx(
            self.rx_start_of_transmission, len(ARQ.rx_frame_buffer)
        )
        self.log.info("[TNC] ARQ | RX | DATA FRAME SUCCESSFULLY RECEIVED", nacks=self.frame_nack_counter,
                      bytesperminute=ARQ.bytes_per_minute, total_bytes=ARQ.total_bytes, duration=duration)

        # Decompress the data frame
        data_frame_decompressed = lzma.decompress(data_frame)
        ARQ.arq_compression_factor = len(data_frame_decompressed) / len(
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
            RX_BUFFER.maxsize = int(ARQ.rx_buffer_size)
        else:
            # if full, free space by getting an item
            self.log.info(
                "[TNC] ARQ | RX | RX_BUFFER FULL - dropping old data",
                buffer_size=RX_BUFFER.qsize(),
                maxsize=int(ARQ.rx_buffer_size)
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
                    Station.dxcallsign,
                    Station.dxgrid,
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
                uuid=self.transmission_uuid,
                timestamp=timestamp,
                dxcall=Station.dxcallsign,
                dxgrid=Station.dxgrid,
                data=base64_data
            )

        if ARQ.arq_save_to_folder:
            try:
                self.save_data_to_folder(
                    self.transmission_uuid,
                    timestamp,
                    self.mycallsign,
                    Station.dxcallsign,
                    Station.dxgrid,
                    data_frame
                )
            except Exception as e:
                self.log.error(
                    "[TNC] ARQ | RX | can't save file to folder",
                    e=e,
                    uuid=self.transmission_uuid,
                    timestamp=timestamp,
                    dxcall=Station.dxcallsign,
                    dxgrid=Station.dxgrid,
                    data=base64_data
                )

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            status="received",
            uuid=self.transmission_uuid,
            percent=ARQ.arq_transmission_percent,
            bytesperminute=ARQ.bytes_per_minute,
            compression=ARQ.arq_compression_factor,
            timestamp=timestamp,
            finished=0,
            mycallsign=str(self.mycallsign, "UTF-8"),
            dxcallsign=str(Station.dxcallsign, "UTF-8"),
            dxgrid=str(Station.dxgrid, "UTF-8"),
            data=base64_data,
            irs=helpers.bool_to_string(self.is_IRS)
        )

        if TNC.enable_stats:
            duration = time.time() - self.rx_start_of_transmission
            self.stats.push(frame_nack_counter=self.frame_nack_counter, status="received", duration=duration)

        self.log.info(
            "[TNC] ARQ | RX | SENDING DATA FRAME ACK")

        self.send_data_ack_frame(snr)
        # Update statistics AFTER the frame ACK is sent
        self.calculate_transfer_rate_rx(
            self.rx_start_of_transmission, len(ARQ.rx_frame_buffer)
        )

        self.log.info(
            "[TNC] | RX | DATACHANNEL ["
            + str(self.mycallsign, "UTF-8")
            + "]<< >>["
            + str(Station.dxcallsign, "UTF-8")
            + "]",
            snr=snr,
        )

    def arq_transmit(self, data_out: bytes):
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
        ARQ.total_bytes = len(data_out)
        self.arq_file_transfer = True
        frame_total_size = len(data_out).to_bytes(4, byteorder="big")

        # Compress data frame
        data_frame_compressed = lzma.compress(data_out)
        compression_factor = len(data_out) / len(data_frame_compressed)
        ARQ.arq_compression_factor = np.clip(compression_factor, 0, 255)
        compression_factor = bytes([int(ARQ.arq_compression_factor * 10)])

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            status="transmitting",
            uuid=self.transmission_uuid,
            percent=ARQ.arq_transmission_percent,
            bytesperminute=ARQ.bytes_per_minute,
            compression=ARQ.arq_compression_factor,
            finished=ARQ.arq_seconds_until_finish,
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            irs=helpers.bool_to_string(self.is_IRS)
        )

        self.log.info(
            "[TNC] | TX | DATACHANNEL",
            Bytes=ARQ.total_bytes,
        )

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
        self.log.debug("[TNC] frame raw data:", data=data_out)
        # Initial bufferposition is 0
        bufferposition = 0
        bufferposition_end = 0
        bufferposition_burst_start = 0

        # Iterate through data_out buffer
        while not self.data_frame_ack_received and ARQ.arq_state:
            # we have self.tx_n_max_retries_per_burst attempts for sending a burst
            for self.tx_n_retry_of_burst in range(self.tx_n_max_retries_per_burst):
                # Bound speed level to:
                # - minimum of either the speed or the length of mode list - 1
                # - maximum of either the speed or zero
                self.speed_level = min(self.speed_level, len(self.mode_list) - 1)
                self.speed_level = max(self.speed_level, 0)

                ARQ.arq_speed_level = self.speed_level
                data_mode = self.mode_list[self.speed_level]

                self.log.debug(
                    "[TNC] Speed-level:",
                    level=self.speed_level,
                    retry=self.tx_n_retry_of_burst,
                    mode=FREEDV_MODE(data_mode).name,
                )

                # Payload information
                payload_per_frame = modem.get_bytes_per_frame(data_mode) - 2

                self.log.info("[TNC] early buffer info",
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
                        #print((payload_per_frame * n_frames_per_burst) % len(data_out))
                        n_frames_per_burst += 1
                        if n_frames_per_burst == self.max_n_frames_per_burst:
                            break
                else:
                    n_frames_per_burst = 1
                self.log.info("[TNC] calculated frames_per_burst:", n=n_frames_per_burst)

                tempbuffer = []
                self.rpt_request_buffer = []
                # Append data frames with n_frames_per_burst to tempbuffer
                for n_frame in range(0, n_frames_per_burst):
                    arqheader = bytearray()
                    arqheader[:1] = bytes([FR_TYPE.BURST_01.value + n_frame])
                    #####arqheader[:1] = bytes([FR_TYPE.BURST_01.value])
                    arqheader[1:2] = bytes([n_frames_per_burst])
                    arqheader[2:3] = self.session_id

                    # only check for buffer position if at least one NACK received
                    self.log.info("[TNC] ----- data buffer position:", iss_buffer_pos=bufferposition,
                                  irs_bufferposition=self.irs_buffer_position)
                    if self.frame_nack_counter > 0 and self.irs_buffer_position != bufferposition:
                        self.log.error("[TNC] ----- data buffer offset:", iss_buffer_pos=bufferposition,
                                       irs_bufferposition=self.irs_buffer_position)
                        # only adjust buffer position for experimental versions
                        if 'exp' in TNC.version:
                            self.log.warning("[TNC] ----- data adjustment disabled!")
                            # bufferposition = self.irs_buffer_position

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

                    self.log.debug("[TNC] tempbuffer:", tempbuffer=tempbuffer)
                    self.log.info(
                        "[TNC] ARQ | TX | FRAMES",
                        mode=FREEDV_MODE(data_mode).name,
                        fpb=n_frames_per_burst,
                        retry=self.tx_n_retry_of_burst,
                    )

                self.enqueue_frame_for_tx(tempbuffer, c2_mode=data_mode)

                # After transmission finished, wait for an ACK or RPT frame
                while (
                        ARQ.arq_state
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
                        "[TNC] arq_transmit: Received BURST ACK. Sending next chunk."
                        , irs_snr=self.burst_ack_snr)
                    # update temp bufferposition for n frames per burst early calculation
                    bufferposition_burst_start = bufferposition_end
                    break  # break retry loop

                if self.data_frame_ack_received:
                    self.log.debug(
                        "[TNC] arq_transmit: Received FRAME ACK. Braking retry loop."
                    )
                    break  # break retry loop

                if self.burst_nack:
                    self.tx_n_retry_of_burst += 1

                    self.log.warning(
                        "[TNC] arq_transmit: Received BURST NACK. Resending data",
                        bufferposition_burst_start=bufferposition_burst_start,
                        bufferposition=bufferposition
                    )

                    bufferposition = bufferposition_burst_start
                    self.burst_nack = False  # reset nack state



                # We need this part for leaving the repeat loop
                # ARQ.arq_state == "DATA" --> when stopping transmission manually
                if not ARQ.arq_state:
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
                    overflows=AudioParam.buffer_overflow_counter,
                )

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
                percent=ARQ.arq_transmission_percent,
                bytesperminute=ARQ.bytes_per_minute,
                compression=ARQ.arq_compression_factor,
                finished=ARQ.arq_seconds_until_finish,
                irs_snr=self.burst_ack_snr,
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
                irs=helpers.bool_to_string(self.is_IRS)
            )

            # Stay in the while loop until we receive a data_frame_ack. Otherwise,
            # the loop exits after sending the last frame only once and doesn't
            # wait for an acknowledgement.
            if self.data_frame_ack_received and bufferposition > len(data_out):
                self.log.debug("[TNC] arq_tx: Last fragment sent and acknowledged.")
                break
                # GOING TO NEXT ITERATION

        if self.data_frame_ack_received:
            self.arq_transmit_success()
        else:
            self.arq_transmit_failed()

        if TESTMODE:
            # Quit after transmission
            self.log.debug("[TNC] TESTMODE: arq_transmit exiting.")
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
            freedata="tnc-message",
            arq="transmission",
            status="transmitted",
            uuid=self.transmission_uuid,
            percent=ARQ.arq_transmission_percent,
            bytesperminute=ARQ.bytes_per_minute,
            compression=ARQ.arq_compression_factor,
            finished=ARQ.arq_seconds_until_finish,
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            irs=helpers.bool_to_string(self.is_IRS)
        )

        self.log.info(
            "[TNC] ARQ | TX | DATA TRANSMITTED!",
            BytesPerMinute=ARQ.bytes_per_minute,
            total_bytes=ARQ.total_bytes,
            BitsPerSecond=ARQ.arq_bits_per_second,
            overflows=AudioParam.buffer_overflow_counter,

        )

        # finally do an arq cleanup
        self.arq_cleanup()

    def arq_transmit_failed(self):
        """
        will be called if we not successfully transmitted all of queued data
        """
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            status="failed",
            uuid=self.transmission_uuid,
            percent=ARQ.arq_transmission_percent,
            bytesperminute=ARQ.bytes_per_minute,
            compression=ARQ.arq_compression_factor,
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            irs=helpers.bool_to_string(self.is_IRS)
        )

        self.log.info(
            "[TNC] ARQ | TX | TRANSMISSION FAILED OR TIME OUT!",
            overflows=AudioParam.buffer_overflow_counter,
        )

        self.stop_transmission()

    def burst_ack_nack_received(self, data_in: bytes) -> None:
        """
        Received an ACK/NACK for a transmitted frame, keep track and
        make adjustments to speed level if needed.

        Args:
          data_in:bytes:

        Returns:

        """
        # Process data only if we are in ARQ and BUSY state
        if ARQ.arq_state:
            Station.dxgrid = b'------'
            helpers.add_to_heard_stations(
                self.dxcallsign,
                Station.dxgrid,
                "DATA-CHANNEL",
                ModemParam.snr,
                ModemParam.frequency_offset,
                HamlibParam.hamlib_frequency,
            )

            frametype = int.from_bytes(bytes(data_in[:1]), "big")
            if frametype == FR_TYPE.BURST_ACK.value:
                # Increase speed level if we received a burst ack
                # self.speed_level = min(self.speed_level + 1, len(self.mode_list) - 1)
                # Force data retry loops of TX TNC to stop and continue with next frame
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
                    "[TNC] ARQ | TX | Burst NACK received",
                    burst_nack_counter=self.burst_nack_counter,
                    irs_buffer_position=self.irs_buffer_position,
                )

            # Update data_channel timestamp
            self.data_channel_last_received = int(time.time())
            # self.burst_ack_snr = int.from_bytes(bytes(data_in[2:3]), "big")
            self.burst_ack_snr = helpers.snr_from_bytes(data_in[2:3])
            # self.log.info("SNR ON IRS", snr=self.burst_ack_snr)

            self.speed_level = int.from_bytes(bytes(data_in[3:4]), "big")
            ARQ.arq_speed_level = self.speed_level

    def frame_ack_received(
            self, data_in: bytes  # pylint: disable=unused-argument
    ) -> None:
        """Received an ACK for a transmitted frame"""
        # Process data only if we are in ARQ and BUSY state
        if ARQ.arq_state:
            Station.dxgrid = b'------'
            helpers.add_to_heard_stations(
                Station.dxcallsign,
                Station.dxgrid,
                "DATA-CHANNEL",
                ModemParam.snr,
                ModemParam.frequency_offset,
                HamlibParam.hamlib_frequency,
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
                         percent=ARQ.arq_transmission_percent,
                         bytesperminute=ARQ.bytes_per_minute,
                         mycallsign=str(self.mycallsign, 'UTF-8'),
                         dxcallsign=str(self.dxcallsign, 'UTF-8'),
                         irs=helpers.bool_to_string(self.is_IRS)
                         )

        Station.dxgrid = b'------'
        helpers.add_to_heard_stations(
            Station.dxcallsign,
            Station.dxgrid,
            "DATA-CHANNEL",
            ModemParam.snr,
            ModemParam.frequency_offset,
            HamlibParam.hamlib_frequency,
        )
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            status="failed",
            uuid=self.transmission_uuid,
            percent=ARQ.arq_transmission_percent,
            bytesperminute=ARQ.bytes_per_minute,
            compression=ARQ.arq_compression_factor,
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            irs=helpers.bool_to_string(self.is_IRS)
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
        if not ARQ.arq_state or TNC.tnc_state != "BUSY":
            return
        Station.dxgrid = b'------'
        helpers.add_to_heard_stations(
            Station.dxcallsign,
            Station.dxgrid,
            "DATA-CHANNEL",
            ModemParam.snr,
            ModemParam.frequency_offset,
            HamlibParam.hamlib_frequency,
        )

        self.log.info("[TNC] ARQ REPEAT RECEIVED")

        # self.rpt_request_received = True
        # Update data_channel timestamp
        self.data_channel_last_received = int(time.time())
        # self.rpt_request_buffer = []

        missing_area = bytes(data_in[2:12])  # 1:9
        missing_area = missing_area.strip(b"\x00")
        print(missing_area)
        print(self.rpt_request_buffer)

        tempbuffer_rptframes = []
        for i in range(0, len(missing_area)):
            print(missing_area[i])
            missing_frames_buffer_position = missing_area[i] - 1
            tempbuffer_rptframes.append(self.rpt_request_buffer[missing_frames_buffer_position])

        self.log.info("[TNC] SENDING REPEAT....")
        data_mode = self.mode_list[self.speed_level]
        self.enqueue_frame_for_tx(tempbuffer_rptframes, c2_mode=data_mode)

        # for i in range(0, 6, 2):
        #    if not missing_area[i: i + 2].endswith(b"\x00\x00"):
        #        self.rpt_request_buffer.insert(0, missing_area[i: i + 2])

    ############################################################################################################
    # ARQ SESSION HANDLER
    ############################################################################################################
    def arq_session_handler(self, mycallsign, dxcallsign, attempts) -> bool:
        """
        Create a session with `Station.dxcallsign` and wait until the session is open.

        Returns:
            True if the session was opened successfully
            False if the session open request failed
        """
        # override connection attempts
        self.session_connect_max_retries = attempts

        self.mycallsign = mycallsign
        self.dxcallsign = dxcallsign

        Station.dxcallsign = self.dxcallsign
        Station.dxcallsign_crc = helpers.get_crc_24(self.dxcallsign)

        # TODO: we need to check this, maybe placing it to class init
        self.datachannel_timeout = False
        self.log.info(
            "[TNC] SESSION ["
            + str(self.mycallsign, "UTF-8")
            + "]>> <<["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            state=ARQ.arq_session_state,
        )

        # Let's check if we have a busy channel
        if ModemParam.channel_busy:
            self.log.warning("[TNC] Channel busy, waiting until free...")
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="session",
                status="waiting",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )

            # wait while timeout not reached and our busy state is busy
            channel_busy_timeout = time.time() + 15
            while ModemParam.channel_busy and time.time() < channel_busy_timeout and not self.check_if_mode_fits_to_busy_slot():
                threading.Event().wait(0.01)

            # if channel busy timeout reached stop connecting
            if time.time() > channel_busy_timeout:
                self.log.warning("[TNC] Channel busy, try again later...")
                ARQ.arq_session_state = "failed"
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
        while not ARQ.arq_session and not self.arq_session_timeout:
            threading.Event().wait(0.01)
            ARQ.arq_session_state = "connecting"
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="session",
                status="connecting",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )
        if ARQ.arq_session and ARQ.arq_session_state == "connected":
            # ARQ.arq_session_state = "connected"
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
            state=ARQ.arq_session_state,
        )
        ARQ.arq_session_state = "failed"
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
        ARQ.arq_session_state = "connecting"

        # create a random session id
        self.session_id = np.random.bytes(1)

        connection_frame = bytearray(self.length_sig0_frame)
        connection_frame[:1] = bytes([FR_TYPE.ARQ_SESSION_OPEN.value])
        connection_frame[1:2] = self.session_id
        connection_frame[2:5] = Station.dxcallsign_crc
        connection_frame[5:8] = Station.mycallsign_crc
        connection_frame[8:14] = helpers.callsign_to_bytes(self.mycallsign)

        while not ARQ.arq_session:
            threading.Event().wait(0.01)
            for attempt in range(self.session_connect_max_retries):
                self.log.info(
                    "[TNC] SESSION ["
                    + str(self.mycallsign, "UTF-8")
                    + "]>>?<<["
                    + str(self.dxcallsign, "UTF-8")
                    + "]",
                    a=f"{str(attempt + 1)}/{str(self.session_connect_max_retries)}",
                    state=ARQ.arq_session_state,
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

                self.enqueue_frame_for_tx([connection_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1, repeat_delay=0)

                # Wait for a time, looking to see if `ARQ.arq_session`
                # indicates we've received a positive response from the far station.
                timeout = time.time() + 3
                while time.time() < timeout:
                    threading.Event().wait(0.01)
                    # Stop waiting if data channel is opened
                    if ARQ.arq_session:
                        return True

                    # Stop waiting and interrupt if data channel is getting closed while opening
                    if ARQ.arq_session_state == "disconnecting":
                        # disabled this session close as its called twice
                        # self.close_session()
                        return False

            # Session connect timeout, send close_session frame to
            # attempt to clean up the far-side, if it received the
            # open_session frame and can still hear us.
            if not ARQ.arq_session:
                self.close_session()
                return False

        # Given the while condition, it will only exit when `ARQ.arq_session` is True
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
        if not TNC.respond_to_call:
            return False

        # ignore channel opener if already in ARQ STATE
        # use case: Station A is connecting to Station B while
        # Station B already tries connecting to Station A.
        # For avoiding ignoring repeated connect request in case of packet loss
        # we are only ignoring packets in case we are ISS
        if ARQ.arq_session and self.IS_ARQ_SESSION_MASTER:
            return False

        self.IS_ARQ_SESSION_MASTER = False
        ARQ.arq_session_state = "connecting"

        # Update arq_session timestamp
        self.arq_session_last_received = int(time.time())

        self.session_id = bytes(data_in[1:2])
        Station.dxcallsign_crc = bytes(data_in[5:8])
        self.dxcallsign = helpers.bytes_to_callsign(bytes(data_in[8:14]))
        Station.dxcallsign = self.dxcallsign

        # check if callsign ssid override
        valid, mycallsign = helpers.check_callsign(self.mycallsign, data_in[2:5])
        self.mycallsign = mycallsign
        Station.dxgrid = b'------'
        helpers.add_to_heard_stations(
            Station.dxcallsign,
            Station.dxgrid,
            "DATA-CHANNEL",
            ModemParam.snr,
            ModemParam.frequency_offset,
            HamlibParam.hamlib_frequency,
        )
        self.log.info(
            "[TNC] SESSION ["
            + str(self.mycallsign, "UTF-8")
            + "]>>|<<["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            state=ARQ.arq_session_state,
        )
        ARQ.arq_session = True
        TNC.tnc_state = "BUSY"

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
        ARQ.arq_session_state = "disconnecting"

        self.log.info(
            "[TNC] SESSION ["
            + str(self.mycallsign, "UTF-8")
            + "]<<X>>["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            state=ARQ.arq_session_state,
        )

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="session",
            status="close",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )

        self.IS_ARQ_SESSION_MASTER = False
        ARQ.arq_session = False

        # we need to send disconnect frame before doing arq cleanup
        # we would lose our session id then
        self.send_disconnect_frame()
        self.arq_cleanup()

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
        if (_valid_crc or _valid_session) and ARQ.arq_session_state not in ["disconnected"]:
            ARQ.arq_session_state = "disconnected"
            Station.dxgrid = b'------'
            helpers.add_to_heard_stations(
                Station.dxcallsign,
                Station.dxgrid,
                "DATA-CHANNEL",
                ModemParam.snr,
                ModemParam.frequency_offset,
                HamlibParam.hamlib_frequency,
            )
            self.log.info(
                "[TNC] SESSION ["
                + str(mycallsign, "UTF-8")
                + "]<<X>>["
                + str(self.dxcallsign, "UTF-8")
                + "]",
                state=ARQ.arq_session_state,
            )

            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="session",
                status="close",
                mycallsign=str(mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )

            self.IS_ARQ_SESSION_MASTER = False
            ARQ.arq_session = False
            self.arq_cleanup()

    def transmit_session_heartbeat(self) -> None:
        """Send ARQ sesion heartbeat while connected"""
        # ARQ.arq_session = True
        # TNC.tnc_state = "BUSY"
        # ARQ.arq_session_state = "connected"

        connection_frame = bytearray(self.length_sig0_frame)
        connection_frame[:1] = bytes([FR_TYPE.ARQ_SESSION_HB.value])
        connection_frame[1:2] = self.session_id

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="session",
            status="connected",
            heartbeat="transmitting",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
        )

        self.enqueue_frame_for_tx([connection_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1, repeat_delay=0)

    def received_session_heartbeat(self, data_in: bytes) -> None:
        """
        Received an ARQ session heartbeat, record and update state accordingly.
        Args:
          data_in:bytes:

        """
        # Accept session data if the DXCALLSIGN_CRC matches the station in static or session id.
        _valid_crc, _ = helpers.check_callsign(self.dxcallsign, bytes(data_in[4:7]))
        _valid_session = helpers.check_session_id(self.session_id, bytes(data_in[1:2]))
        if _valid_crc or _valid_session and ARQ.arq_session_state in ["connected", "connecting"]:
            self.log.debug("[TNC] Received session heartbeat")
            Station.dxgrid = b'------'
            helpers.add_to_heard_stations(
                self.dxcallsign,
                Station.dxgrid,
                "SESSION-HB",
                ModemParam.snr,
                ModemParam.frequency_offset,
                HamlibParam.hamlib_frequency,
            )

            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="session",
                status="connected",
                heartbeat="received",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
            )

            ARQ.arq_session = True
            ARQ.arq_session_state = "connected"
            TNC.tnc_state = "BUSY"

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
                    and ARQ.arq_session_state != 'disconnecting'
                    and ARQ.arq_session_state != 'disconnected'
                    and ARQ.arq_session_state != 'failed'
            ):
                self.transmit_session_heartbeat()

    ##########################################################################################################
    # ARQ DATA CHANNEL HANDLER
    ##########################################################################################################
    def open_dc_and_transmit(
            self,
            data_out: bytes,
            transmission_uuid: str,
            mycallsign,
            dxcallsign,
            attempts: int,
    ) -> bool:
        """
        Open data channel and transmit data

        Args:
          data_out:bytes:
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

        Station.dxcallsign = dxcallsign
        Station.dxcallsign_crc = helpers.get_crc_24(Station.dxcallsign)

        # override session connection attempts
        self.data_channel_max_retries = attempts

        TNC.tnc_state = "BUSY"
        self.arq_file_transfer = True

        self.transmission_uuid = transmission_uuid

        # wait a moment for the case, a heartbeat is already on the way back to us
        # this makes channel establishment more clean
        if ARQ.arq_session:
            threading.Event().wait(2.5)

        self.datachannel_timeout = False

        # we need to compress data for getting a compression factor.
        # so we are compressing twice. This is not that nice and maybe there is another way
        # for calculating transmission statistics
        # ARQ.arq_compression_factor = len(data_out) / len(lzma.compress(data_out))

        self.arq_open_data_channel(mycallsign)

        # wait until data channel is open
        while not ARQ.arq_state and not self.datachannel_timeout and TNC.tnc_state in ["BUSY"]:
            threading.Event().wait(0.01)

        if ARQ.arq_state:
            self.arq_transmit(data_out)
            return True

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
        self.is_IRS = False

        # init a new random session id if we are not in an arq session
        if not ARQ.arq_session:
            self.session_id = np.random.bytes(1)

        # Update data_channel timestamp
        self.data_channel_last_received = int(time.time())

        if TNC.low_bandwidth_mode:
            frametype = bytes([FR_TYPE.ARQ_DC_OPEN_N.value])
            self.log.debug("[TNC] Requesting low bandwidth mode")

        else:
            frametype = bytes([FR_TYPE.ARQ_DC_OPEN_W.value])
            self.log.debug("[TNC] Requesting high bandwidth mode")

        connection_frame = bytearray(self.length_sig0_frame)
        connection_frame[:1] = frametype
        connection_frame[1:4] = Station.dxcallsign_crc
        connection_frame[4:7] = Station.mycallsign_crc
        connection_frame[7:13] = helpers.callsign_to_bytes(mycallsign)
        connection_frame[13:14] = self.session_id

        while not ARQ.arq_state:
            threading.Event().wait(0.01)
            for attempt in range(self.data_channel_max_retries):

                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    arq="transmission",
                    status="opening",
                    mycallsign=str(mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                    irs=helpers.bool_to_string(self.is_IRS)
                )

                self.log.info(
                    "[TNC] ARQ | DATA | TX | ["
                    + str(mycallsign, "UTF-8")
                    + "]>> <<["
                    + str(self.dxcallsign, "UTF-8")
                    + "]",
                    attempt=f"{str(attempt + 1)}/{str(self.data_channel_max_retries)}",
                )

                # Let's check if we have a busy channel and if we are not in a running arq session.
                if ModemParam.channel_busy and not ARQ.arq_state:
                    self.log.warning("[TNC] Channel busy, waiting until free...")
                    self.send_data_to_socket_queue(
                        freedata="tnc-message",
                        arq="transmission",
                        status="waiting",
                        mycallsign=str(self.mycallsign, 'UTF-8'),
                        dxcallsign=str(self.dxcallsign, 'UTF-8'),
                        irs=helpers.bool_to_string(self.is_IRS)
                    )

                    # wait while timeout not reached and our busy state is busy
                    channel_busy_timeout = time.time() + 5
                    while ModemParam.channel_busy and time.time() < channel_busy_timeout and not self.check_if_mode_fits_to_busy_slot():
                        threading.Event().wait(0.01)

                self.enqueue_frame_for_tx([connection_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1, repeat_delay=0)

                timeout = time.time() + self.duration_sig1_frame * 3 + (ModemParam.tx_delay / 1000 * 2)
                while time.time() < timeout:
                    threading.Event().wait(0.01)
                    # Stop waiting if data channel is opened
                    if ARQ.arq_state:
                        return True
                    if TNC.tnc_state in ["IDLE"]:
                        return False

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
                percent=ARQ.arq_transmission_percent,
                bytesperminute=ARQ.bytes_per_minute,
                compression=ARQ.arq_compression_factor,
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
                irs=helpers.bool_to_string(self.is_IRS)
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
        if not TNC.respond_to_call and not ARQ.arq_session:
            return False

        # stop processing if not in arq session, but tnc state is busy and we have a different session id
        # use-case we get a connection request while connecting to another station
        if not ARQ.arq_session and TNC.tnc_state in ["BUSY"] and data_in[13:14] != self.session_id:
            return False

        self.arq_file_transfer = True

        # check if callsign ssid override
        _, self.mycallsign = helpers.check_callsign(self.mycallsign, data_in[1:4])

        # ignore channel opener if already in ARQ STATE
        # use case: Station A is connecting to Station B while
        # Station B already tries connecting to Station A.
        # For avoiding ignoring repeated connect request in case of packet loss
        # we are only ignoring packets in case we are ISS
        if ARQ.arq_state and not self.is_IRS:
            return False

        self.is_IRS = True

        Station.dxcallsign_crc = bytes(data_in[4:7])
        self.dxcallsign = helpers.bytes_to_callsign(bytes(data_in[7:13]))
        Station.dxcallsign = self.dxcallsign

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            status="opening",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            irs=helpers.bool_to_string(self.is_IRS)
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

        if frametype == FR_TYPE.ARQ_DC_OPEN_W.value and not TNC.low_bandwidth_mode:
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
        elif frametype == FR_TYPE.ARQ_DC_OPEN_N.value and not TNC.low_bandwidth_mode:
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

        # TODO: MOVE THIS TO arq_calculate_speed_level()
        # calculate speed level in correlation to latest known SNR
        for i in range(len(self.mode_list)):
            if ModemParam.snr >= self.snr_list[i]:
                self.speed_level = i

        # calculate if speed level fits to busy condition
        mode_name = codec2.FREEDV_MODE(self.mode_list[self.speed_level]).name
        mode_slots = codec2.FREEDV_MODE_USED_SLOTS[mode_name].value
        if mode_slots in [ModemParam.channel_busy_slot]:
            self.speed_level = 0
            self.log.warning(
                "[TNC] busy slot detection",
                slots=ModemParam.channel_busy_slot,
                mode_slots=mode_slots,
            )

        self.log.debug(
            "[TNC] calculated speed level",
            speed_level=self.speed_level,
            given_snr=ModemParam.snr,
            min_snr=self.snr_list[self.speed_level],
        )

        # Update modes we are listening to
        self.set_listening_modes(True, True, self.mode_list[self.speed_level])
        Station.dxgrid = b'------'
        helpers.add_to_heard_stations(
            Station.dxcallsign,
            Station.dxgrid,
            "DATA-CHANNEL",
            ModemParam.snr,
            ModemParam.frequency_offset,
            HamlibParam.hamlib_frequency,
        )

        self.session_id = data_in[13:14]

        # check again if callsign ssid override
        _, self.mycallsign = helpers.check_callsign(self.mycallsign, data_in[1:4])

        self.log.info(
            "[TNC] ARQ | DATA | RX | ["
            + str(self.mycallsign, "UTF-8")
            + "]>> <<["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            channel_constellation=constellation,
        )

        # Reset data_channel/burst timestamps
        self.data_channel_last_received = int(time.time())
        self.burst_last_received = int(time.time() + 10)  # we might need some more time so lets increase this

        # Set ARQ State AFTER resetting timeouts
        # this avoids timeouts starting too early
        ARQ.arq_state = True
        TNC.tnc_state = "BUSY"

        self.reset_statistics()

        # Select the frame type based on the current TNC mode
        if TNC.low_bandwidth_mode or self.received_LOW_BANDWIDTH_MODE:
            frametype = bytes([FR_TYPE.ARQ_DC_OPEN_ACK_N.value])
            self.log.debug("[TNC] Responding with low bandwidth mode")
        else:
            frametype = bytes([FR_TYPE.ARQ_DC_OPEN_ACK_W.value])
            self.log.debug("[TNC] Responding with high bandwidth mode")

        connection_frame = bytearray(self.length_sig0_frame)
        connection_frame[:1] = frametype
        connection_frame[1:2] = self.session_id
        connection_frame[8:9] = bytes([self.speed_level])
        connection_frame[13:14] = bytes([ARQ.arq_protocol_version])

        self.enqueue_frame_for_tx([connection_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1, repeat_delay=0)

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            status="opened",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            irs=helpers.bool_to_string(self.is_IRS)
        )

        self.log.info(
            "[TNC] ARQ | DATA | RX | ["
            + str(self.mycallsign, "UTF-8")
            + "]>>|<<["
            + str(self.dxcallsign, "UTF-8")
            + "]",
            bandwidth="wide",
            snr=ModemParam.snr,
        )

        # set start of transmission for our statistics
        self.rx_start_of_transmission = time.time()

        # Reset data_channel/burst timestamps once again for avoiding running into timeout
        self.data_channel_last_received = int(time.time())
        self.burst_last_received = int(time.time() + 10)  # we might need some more time so lets increase this

    def arq_received_channel_is_open(self, data_in: bytes) -> None:
        """
        Called if we received a data channel opener
        Args:
          data_in:bytes:

        """
        protocol_version = int.from_bytes(bytes(data_in[13:14]), "big")
        if protocol_version == ARQ.arq_protocol_version:
            self.send_data_to_socket_queue(
                freedata="tnc-message",
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
            Station.dxgrid = b'------'
            helpers.add_to_heard_stations(
                Station.dxcallsign,
                Station.dxgrid,
                "DATA-CHANNEL",
                ModemParam.snr,
                ModemParam.frequency_offset,
                HamlibParam.hamlib_frequency,
            )

            self.log.info(
                "[TNC] ARQ | DATA | TX | ["
                + str(self.mycallsign, "UTF-8")
                + "]>>|<<["
                + str(self.dxcallsign, "UTF-8")
                + "]",
                snr=ModemParam.snr,
            )

            # as soon as we set ARQ_STATE to DATA, transmission starts
            ARQ.arq_state = True
            # Update data_channel timestamp
            self.data_channel_last_received = int(time.time())
        else:
            TNC.tnc_state = "IDLE"
            ARQ.arq_state = False
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                arq="transmission",
                status="failed",
                reason="protocol version missmatch",
                mycallsign=str(self.mycallsign, 'UTF-8'),
                dxcallsign=str(self.dxcallsign, 'UTF-8'),
                irs=helpers.bool_to_string(self.is_IRS)
            )
            # TODO: We should display a message to this effect on the UI.
            self.log.warning(
                "[TNC] protocol version mismatch:",
                received=protocol_version,
                own=ARQ.arq_protocol_version,
            )
            self.stop_transmission()

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
        Station.dxcallsign = dxcallsign
        Station.dxcallsign_crc = helpers.get_crc_24(Station.dxcallsign)
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            ping="transmitting",
            dxcallsign=str(dxcallsign, "UTF-8"),
            mycallsign=str(mycallsign, "UTF-8"),
            snr=str(ModemParam.snr),
        )
        self.log.info(
            "[TNC] PING REQ ["
            + str(mycallsign, "UTF-8")
            + "] >>> ["
            + str(dxcallsign, "UTF-8")
            + "]"
        )

        ping_frame = bytearray(self.length_sig0_frame)
        ping_frame[:1] = bytes([FR_TYPE.PING.value])
        ping_frame[1:4] = Station.dxcallsign_crc
        ping_frame[4:7] = helpers.get_crc_24(mycallsign)
        ping_frame[7:13] = helpers.callsign_to_bytes(mycallsign)

        if TNC.enable_fsk:
            self.log.info("[TNC] ENABLE FSK", state=TNC.enable_fsk)
            self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.fsk_ldpc_0.value)
        else:
            self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.sig0.value)

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

        Station.dxcallsign_crc = dxcallsign_crc
        Station.dxcallsign = dxcallsign
        self.log.info(
            "[TNC] PING REQ ["
            + str(mycallsign, "UTF-8")
            + "] <<< ["
            + str(dxcallsign, "UTF-8")
            + "]",
            snr=ModemParam.snr,
        )

        Station.dxgrid = b'------'
        helpers.add_to_heard_stations(
            dxcallsign,
            Station.dxgrid,
            "PING",
            ModemParam.snr,
            ModemParam.frequency_offset,
            HamlibParam.hamlib_frequency,
        )

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            ping="received",
            uuid=str(uuid.uuid4()),
            timestamp=int(time.time()),
            dxgrid=str(Station.dxgrid, "UTF-8"),
            dxcallsign=str(dxcallsign, "UTF-8"),
            mycallsign=str(mycallsign, "UTF-8"),
            snr=str(ModemParam.snr),
        )
        if TNC.respond_to_call:
            self.transmit_ping_ack()

    def transmit_ping_ack(self):
        """

        transmit a ping ack frame
        called by def received_ping
        """
        ping_frame = bytearray(self.length_sig0_frame)
        ping_frame[:1] = bytes([FR_TYPE.PING_ACK.value])
        ping_frame[1:4] = Station.dxcallsign_crc
        ping_frame[4:7] = Station.mycallsign_crc
        ping_frame[7:11] = helpers.encode_grid(Station.mygrid.decode("UTF-8"))
        ping_frame[13:14] = helpers.snr_to_bytes(ModemParam.snr)

        if TNC.enable_fsk:
            self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.fsk_ldpc_0.value)
        else:
            self.enqueue_frame_for_tx([ping_frame], c2_mode=FREEDV_MODE.sig0.value)

    def received_ping_ack(self, data_in: bytes) -> None:
        """
        Called if a PING ack has been received
        Args:
          data_in:bytes:

        """

        # check if we received correct ping
        # check if callsign ssid override
        _valid, mycallsign = helpers.check_callsign(self.mycallsign, data_in[1:4])
        if _valid:

            Station.dxgrid = bytes(helpers.decode_grid(data_in[7:11]), "UTF-8")
            dxsnr = helpers.snr_from_bytes(data_in[13:14])
            self.send_data_to_socket_queue(
                freedata="tnc-message",
                ping="acknowledge",
                uuid=str(uuid.uuid4()),
                timestamp=int(time.time()),
                dxgrid=str(Station.dxgrid, "UTF-8"),
                dxcallsign=str(Station.dxcallsign, "UTF-8"),
                mycallsign=str(mycallsign, "UTF-8"),
                snr=str(ModemParam.snr),
                dxsnr=str(dxsnr)
            )
            # combined_snr = own rx snr / snr on dx side
            combined_snr = f"{ModemParam.snr}/{dxsnr}"
            helpers.add_to_heard_stations(
                Station.dxcallsign,
                Station.dxgrid,
                "PING-ACK",
                combined_snr,
                ModemParam.frequency_offset,
                HamlibParam.hamlib_frequency,
            )

            self.log.info(
                "[TNC] PING ACK ["
                + str(mycallsign, "UTF-8")
                + "] >|< ["
                + str(Station.dxcallsign, "UTF-8")
                + "]",
                snr=ModemParam.snr,
                dxsnr=dxsnr,
            )
            TNC.tnc_state = "IDLE"
        else:
            self.log.info(
                "[TNC] FOREIGN PING ACK ["
                + str(self.mycallsign, "UTF-8")
                + "] ??? ["
                + str(bytes(data_in[4:7]), "UTF-8")
                + "]",
                snr=ModemParam.snr,
            )

    def stop_transmission(self) -> None:
        """
        Force a stop of the running transmission
        """
        self.log.warning("[TNC] Stopping transmission!")

        TNC.tnc_state = "IDLE"
        ARQ.arq_state = False
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            status="stopped",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8')
        )

        stop_frame = bytearray(self.length_sig0_frame)
        stop_frame[:1] = bytes([FR_TYPE.ARQ_STOP.value])
        stop_frame[1:4] = Station.dxcallsign_crc
        stop_frame[4:7] = Station.mycallsign_crc
        # TODO: Not sure if we really need the session id when disconnecting
        # stop_frame[1:2] = self.session_id
        stop_frame[7:13] = helpers.callsign_to_bytes(self.mycallsign)

        self.enqueue_frame_for_tx([stop_frame], c2_mode=FREEDV_MODE.sig1.value, copies=3, repeat_delay=0)

        self.arq_cleanup()

    def received_stop_transmission(
            self, data_in: bytes
    ) -> None:  # pylint: disable=unused-argument
        """
        Received a transmission stop
        """
        self.log.warning("[TNC] Stopping transmission!")
        TNC.tnc_state = "IDLE"
        ARQ.arq_state = False
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            arq="transmission",
            status="stopped",
            mycallsign=str(self.mycallsign, 'UTF-8'),
            dxcallsign=str(self.dxcallsign, 'UTF-8'),
            uuid=self.transmission_uuid
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
                while Beacon.beacon_state:
                    if (
                            not ARQ.arq_session
                            and not self.arq_file_transfer
                            and not Beacon.beacon_pause
                            and not ModemParam.channel_busy
                            and TNC.tnc_state not in ["BUSY"]
                            and not ARQ.arq_state
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
                        beacon_frame[7:11] = helpers.encode_grid(Station.mygrid.decode("UTF-8"))

                        if TNC.enable_fsk:
                            self.log.info("[TNC] ENABLE FSK", state=TNC.enable_fsk)
                            self.enqueue_frame_for_tx(
                                [beacon_frame],
                                c2_mode=FREEDV_MODE.fsk_ldpc_0.value,
                            )
                        else:
                            self.enqueue_frame_for_tx([beacon_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1,
                                                      repeat_delay=0)

                    self.beacon_interval_timer = time.time() + self.beacon_interval
                    while (
                            time.time() < self.beacon_interval_timer
                            and Beacon.beacon_state
                            and not Beacon.beacon_pause
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
        Station.dxgrid = bytes(helpers.decode_grid(data_in[7:11]), "UTF-8")
        self.send_data_to_socket_queue(
            freedata="tnc-message",
            beacon="received",
            uuid=str(uuid.uuid4()),
            timestamp=int(time.time()),
            dxcallsign=str(beacon_callsign, "UTF-8"),
            dxgrid=str(Station.dxgrid, "UTF-8"),
            snr=str(ModemParam.snr),
        )

        self.log.info(
            "[TNC] BEACON RCVD ["
            + str(beacon_callsign, "UTF-8")
            + "]["
            + str(Station.dxgrid, "UTF-8")
            + "] ",
            snr=ModemParam.snr,
        )
        helpers.add_to_heard_stations(
            beacon_callsign,
            Station.dxgrid,
            "BEACON",
            ModemParam.snr,
            ModemParam.frequency_offset,
            HamlibParam.hamlib_frequency,
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
        cq_frame[7:11] = helpers.encode_grid(Station.mygrid.decode("UTF-8"))

        self.log.debug("[TNC] CQ Frame:", data=[cq_frame])

        if TNC.enable_fsk:
            self.log.info("[TNC] ENABLE FSK", state=TNC.enable_fsk)
            self.enqueue_frame_for_tx([cq_frame], c2_mode=FREEDV_MODE.fsk_ldpc_0.value)
        else:
            self.enqueue_frame_for_tx([cq_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1, repeat_delay=0)

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
        Station.dxgrid = bytes(helpers.decode_grid(data_in[7:11]), "UTF-8")

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            cq="received",
            mycallsign=str(self.mycallsign, "UTF-8"),
            dxcallsign=str(dxcallsign, "UTF-8"),
            dxgrid=str(Station.dxgrid, "UTF-8"),
        )
        self.log.info(
            "[TNC] CQ RCVD ["
            + str(dxcallsign, "UTF-8")
            + "]["
            + str(Station.dxgrid, "UTF-8")
            + "] ",
            snr=ModemParam.snr,
        )
        helpers.add_to_heard_stations(
            dxcallsign,
            Station.dxgrid,
            "CQ CQ CQ",
            ModemParam.snr,
            ModemParam.frequency_offset,
            HamlibParam.hamlib_frequency,
        )

        if TNC.respond_to_cq and TNC.respond_to_call:
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
        # duration, plus overhead. Set the wait interval to be random between 0 and
        # self.duration_sig1_frame * 4 == 4 slots
        # in self.duration_sig1_frame increments.
        # FIXME: This causes problems when running ctests - we need to figure out why
        if not TESTMODE:
            self.log.info("[TNC] Waiting for QRV slot...")
            helpers.wait(randrange(0, int(self.duration_sig1_frame * 4), self.duration_sig1_frame * 10 // 10.0))

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            qrv="transmitting",
            dxcallsign=str(dxcallsign, "UTF-8"),
        )
        self.log.info("[TNC] Sending QRV!")

        qrv_frame = bytearray(self.length_sig0_frame)
        qrv_frame[:1] = bytes([FR_TYPE.QRV.value])
        qrv_frame[1:7] = helpers.callsign_to_bytes(self.mycallsign)
        qrv_frame[7:11] = helpers.encode_grid(Station.mygrid.decode("UTF-8"))
        qrv_frame[11:12] = helpers.snr_to_bytes(ModemParam.snr)

        if TNC.enable_fsk:
            self.log.info("[TNC] ENABLE FSK", state=TNC.enable_fsk)
            self.enqueue_frame_for_tx([qrv_frame], c2_mode=FREEDV_MODE.fsk_ldpc_0.value)
        else:
            self.enqueue_frame_for_tx([qrv_frame], c2_mode=FREEDV_MODE.sig0.value, copies=1, repeat_delay=0)

    def received_qrv(self, data_in: bytes) -> None:
        """
        Called when we receive a QRV frame
        Args:
          data_in:bytes:

        """
        # here we add the received station to the heard stations buffer
        dxcallsign = helpers.bytes_to_callsign(bytes(data_in[1:7]))
        Station.dxgrid = bytes(helpers.decode_grid(data_in[7:11]), "UTF-8")
        dxsnr = helpers.snr_from_bytes(data_in[11:12])

        combined_snr = f"{ModemParam.snr}/{dxsnr}"

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            qrv="received",
            dxcallsign=str(dxcallsign, "UTF-8"),
            dxgrid=str(Station.dxgrid, "UTF-8"),
            snr=str(ModemParam.snr),
            dxsnr=str(dxsnr)
        )

        self.log.info(
            "[TNC] QRV RCVD ["
            + str(dxcallsign, "UTF-8")
            + "]["
            + str(Station.dxgrid, "UTF-8")
            + "] ",
            snr=ModemParam.snr,
            dxsnr=dxsnr
        )
        helpers.add_to_heard_stations(
            dxcallsign,
            Station.dxgrid,
            "QRV",
            combined_snr,
            ModemParam.frequency_offset,
            HamlibParam.hamlib_frequency,
        )



    def received_is_writing(self, data_in: bytes) -> None:
        """
        Called when we receive a IS WRITING frame
        Args:
          data_in:bytes:

        """
        # here we add the received station to the heard stations buffer
        dxcallsign = helpers.bytes_to_callsign(bytes(data_in[1:7]))

        self.send_data_to_socket_queue(
            freedata="tnc-message",
            fec="is_writing",
            dxcallsign=str(dxcallsign, "UTF-8")
        )

        self.log.info(
            "[TNC] IS_WRITING RCVD ["
            + str(dxcallsign, "UTF-8")
            + "] ",
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
            if ARQ.total_bytes == 0:
                ARQ.total_bytes = 1
            ARQ.arq_transmission_percent = min(
                int(
                    (
                            receivedbytes
                            * ARQ.arq_compression_factor
                            / ARQ.total_bytes
                    )
                    * 100
                ),
                100,
            )

            transmissiontime = time.time() - self.rx_start_of_transmission

            if receivedbytes > 0:
                ARQ.arq_bits_per_second = int((receivedbytes * 8) / transmissiontime)
                ARQ.bytes_per_minute = int(
                    receivedbytes / (transmissiontime / 60)
                )
                ARQ.arq_seconds_until_finish = int(((ARQ.total_bytes - receivedbytes) / (
                            ARQ.bytes_per_minute * ARQ.arq_compression_factor)) * 60) - 20  # offset because of frame ack/nack

                speed_chart = {"snr": ModemParam.snr, "bpm": ARQ.bytes_per_minute, "timestamp": int(time.time())}
                # check if data already in list
                if speed_chart not in ARQ.speed_list:
                    ARQ.speed_list.append(speed_chart)
            else:
                ARQ.arq_bits_per_second = 0
                ARQ.bytes_per_minute = 0
                ARQ.arq_seconds_until_finish = 0
        except Exception as err:
            self.log.error(f"[TNC] calculate_transfer_rate_rx: Exception: {err}")
            ARQ.arq_transmission_percent = 0.0
            ARQ.arq_bits_per_second = 0
            ARQ.bytes_per_minute = 0

        return [
            ARQ.arq_bits_per_second,
            ARQ.bytes_per_minute,
            ARQ.arq_transmission_percent,
        ]

    def reset_statistics(self) -> None:
        """
        Reset statistics
        """
        # reset ARQ statistics
        ARQ.bytes_per_minute_burst = 0
        ARQ.bytes_per_minute = 0
        ARQ.arq_bits_per_second_burst = 0
        ARQ.arq_bits_per_second = 0
        ARQ.arq_transmission_percent = 0
        ARQ.total_bytes = 0
        ARQ.arq_seconds_until_finish = 0

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
            ARQ.arq_transmission_percent = min(
                int((sentbytes / tx_buffer_length) * 100), 100
            )

            transmissiontime = time.time() - tx_start_of_transmission

            if sentbytes > 0:
                ARQ.arq_bits_per_second = int((sentbytes * 8) / transmissiontime)
                ARQ.bytes_per_minute = int(sentbytes / (transmissiontime / 60))
                ARQ.arq_seconds_until_finish = int(((tx_buffer_length - sentbytes) / (
                            ARQ.bytes_per_minute * ARQ.arq_compression_factor)) * 60)

                speed_chart = {"snr": self.burst_ack_snr, "bpm": ARQ.bytes_per_minute,
                               "timestamp": int(time.time())}
                # check if data already in list
                if speed_chart not in ARQ.speed_list:
                    ARQ.speed_list.append(speed_chart)

            else:
                ARQ.arq_bits_per_second = 0
                ARQ.bytes_per_minute = 0
                ARQ.arq_seconds_until_finish = 0

        except Exception as err:
            self.log.error(f"[TNC] calculate_transfer_rate_tx: Exception: {err}")
            ARQ.arq_transmission_percent = 0.0
            ARQ.arq_bits_per_second = 0
            ARQ.bytes_per_minute = 0

        return [
            ARQ.arq_bits_per_second,
            ARQ.bytes_per_minute,
            ARQ.arq_transmission_percent,
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
        # wait a second for smoother arq behaviour
        helpers.wait(1.0)

        self.rx_frame_bof_received = False
        self.rx_frame_eof_received = False
        self.burst_ack = False
        self.rpt_request_received = False
        self.burst_rpt_counter = 0
        self.data_frame_ack_received = False
        ARQ.rx_burst_buffer = []
        ARQ.rx_frame_buffer = b""
        self.burst_ack_snr = 0
        self.arq_burst_last_payload = 0
        self.rx_n_frame_of_burst = 0
        self.rx_n_frames_per_burst = 0

        # reset modem receiving state to reduce cpu load
        modem.RECEIVE_SIG0 = True
        modem.RECEIVE_SIG1 = False
        modem.RECEIVE_DATAC1 = False
        modem.RECEIVE_DATAC3 = False
        modem.RECEIVE_DATAC4 = False
        # modem.RECEIVE_FSK_LDPC_0 = False
        modem.RECEIVE_FSK_LDPC_1 = False

        # reset buffer overflow counter
        AudioParam.buffer_overflow_counter = [0, 0, 0, 0, 0]

        self.is_IRS = False
        self.burst_nack = False
        self.burst_nack_counter = 0
        self.frame_nack_counter = 0
        self.frame_received_counter = 0
        self.speed_level = len(self.mode_list) - 1
        ARQ.arq_speed_level = self.speed_level

        # low bandwidth mode indicator
        self.received_LOW_BANDWIDTH_MODE = False

        # reset retry counter for rx channel / burst
        self.n_retries_per_burst = 0

        # reset max retries possibly overriden by api
        self.session_connect_max_retries = 10
        self.data_channel_max_retries = 10

        # we need to keep these values if in ARQ_SESSION
        if not ARQ.arq_session:
            TNC.tnc_state = "IDLE"
            self.dxcallsign = b"AA0AA-0"
            self.mycallsign = Station.mycallsign
            self.session_id = bytes(1)

        ARQ.arq_session_state = "disconnected"
        ARQ.speed_list = []
        ARQ.arq_state = False
        self.arq_file_transfer = False

        Beacon.beacon_pause = False
        # reset beacon interval timer for not directly starting beacon after ARQ
        self.beacon_interval_timer = time.time() + self.beacon_interval

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
        # sourcery skip: extract-duplicate-method
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

        if mode == codec2.FREEDV_MODE.datac1.value:
            modem.RECEIVE_DATAC1 = True
            modem.RECEIVE_DATAC3 = False
            modem.RECEIVE_DATAC4 = False
            modem.RECEIVE_FSK_LDPC_1 = False
            self.log.debug("[TNC] Changing listening data mode", mode="datac1")
        elif mode == codec2.FREEDV_MODE.datac3.value:
            modem.RECEIVE_DATAC1 = False
            modem.RECEIVE_DATAC3 = True
            modem.RECEIVE_DATAC4 = False
            modem.RECEIVE_FSK_LDPC_1 = False
            self.log.debug("[TNC] Changing listening data mode", mode="datac3")
        elif mode == codec2.FREEDV_MODE.datac4.value:
            modem.RECEIVE_DATAC1 = False
            modem.RECEIVE_DATAC3 = False
            modem.RECEIVE_DATAC4 = True
            modem.RECEIVE_FSK_LDPC_1 = False
            self.log.debug("[TNC] Changing listening data mode", mode="datac4")
        elif mode == codec2.FREEDV_MODE.fsk_ldpc_1.value:
            modem.RECEIVE_DATAC1 = False
            modem.RECEIVE_DATAC3 = False
            modem.RECEIVE_DATAC4 = False
            modem.RECEIVE_FSK_LDPC_1 = True
            self.log.debug("[TNC] Changing listening data mode", mode="fsk_ldpc_1")
        else:
            modem.RECEIVE_DATAC1 = True
            modem.RECEIVE_DATAC3 = True
            modem.RECEIVE_DATAC4 = True
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
                not ARQ.arq_state
                and ARQ.arq_session_state != "connected"
                or not self.is_IRS
        ):
            return

        # get modem error state
        modem_error_state = modem.get_modem_error_state()

        # We want to reach this state only if connected ( == return above not called )
        if self.rx_n_frames_per_burst > 1:
            # uses case for IRS: reduce time for waiting by counting "None" in burst buffer
            frames_left = ARQ.rx_burst_buffer.count(None)
        elif self.rx_n_frame_of_burst == 0 and self.rx_n_frames_per_burst == 0:
            # use case for IRS: We didn't receive a burst yet, because the first one got lost
            # in this case we don't have any information about the expected burst length
            # we must assume, we are getting a burst with max_n_frames_per_burst
            frames_left = self.max_n_frames_per_burst
        else:
            frames_left = 1

        # make sure we don't have a 0 here for avoiding too short timeouts
        if frames_left == 0:
            frames_left = 1

        timeout = self.burst_last_received + (self.time_list[self.speed_level] * frames_left)
        # TODO: Enable this for development
        # print(f"timeout expected in:{round(timeout - time.time())} | frames left: {frames_left} of {self.rx_n_frames_per_burst} | speed level: {self.speed_level}")
        if timeout <= time.time() or modem_error_state:
            self.log.warning(
                "[TNC] Burst decoding error or timeout",
                attempt=self.n_retries_per_burst,
                max_attempts=self.rx_n_max_retries_per_burst,
                speed_level=self.speed_level,
                modem_error_state=modem_error_state
            )

            print(
                f"frames_per_burst {self.rx_n_frame_of_burst} / {self.rx_n_frames_per_burst}, Repeats: {self.burst_rpt_counter} Nones: {ARQ.rx_burst_buffer.count(None)}")

            if self.rx_n_frames_per_burst > 1 and self.burst_rpt_counter < 3 and ARQ.rx_burst_buffer.count(None) > 0:
                # reset self.burst_last_received
                self.burst_last_received = time.time() + self.time_list[self.speed_level] * frames_left
                self.burst_rpt_counter += 1
                self.send_retransmit_request_frame()

            else:

                # reset self.burst_last_received
                self.burst_last_received = time.time() + self.time_list[self.speed_level]

                # reduce speed level if nack counter increased
                self.frame_received_counter = 0
                self.burst_nack_counter += 1
                if self.burst_nack_counter >= 2:
                    self.burst_nack_counter = 0
                    self.speed_level = max(self.speed_level - 1, 0)
                    ARQ.arq_speed_level = self.speed_level

                # TODO: Create better mechanisms for handling n frames per burst for bad channels
                # reduce frames per burst
                if self.burst_rpt_counter >= 2:
                    tx_n_frames_per_burst = max(self.rx_n_frames_per_burst - 1, 1)
                else:
                    tx_n_frames_per_burst = self.rx_n_frames_per_burst

                # Update modes we are listening to
                self.set_listening_modes(True, True, self.mode_list[self.speed_level])

                # TODO: Does SNR make sense for NACK if we dont have an actual SNR information?
                self.send_burst_nack_frame_watchdog(0, tx_n_frames_per_burst)

                # Update data_channel timestamp
                # TODO: Disabled this one for testing.
                # self.data_channel_last_received = time.time()
                self.n_retries_per_burst += 1
        else:
            # print((self.data_channel_last_received + self.time_list[self.speed_level])-time.time())
            pass

        if self.n_retries_per_burst >= self.rx_n_max_retries_per_burst:
            self.stop_transmission()

    def data_channel_keep_alive_watchdog(self) -> None:
        """
        watchdog which checks if we are running into a connection timeout
        DATA CHANNEL
        """
        # and not static.ARQ_SEND_KEEP_ALIVE:
        if ARQ.arq_state and TNC.tnc_state == "BUSY":
            threading.Event().wait(0.01)
            if (
                    self.data_channel_last_received + self.transmission_timeout
                    > time.time()
            ):

                timeleft = int((self.data_channel_last_received + self.transmission_timeout) - time.time())
                if timeleft % 10 == 0:
                    self.log.debug("Time left until channel timeout", seconds=timeleft)

                # threading.Event().wait(5)
                # print(self.data_channel_last_received + self.transmission_timeout - time.time())
                # pass
            else:
                # Clear the timeout timestamp
                self.data_channel_last_received = 0
                self.log.info(
                    "[TNC] DATA ["
                    + str(self.mycallsign, "UTF-8")
                    + "]<<T>>["
                    + str(Station.dxcallsign, "UTF-8")
                    + "]"
                )
                self.send_data_to_socket_queue(
                    freedata="tnc-message",
                    arq="transmission",
                    status="failed",
                    uuid=self.transmission_uuid,
                    mycallsign=str(self.mycallsign, 'UTF-8'),
                    dxcallsign=str(self.dxcallsign, 'UTF-8'),
                    irs=helpers.bool_to_string(self.is_IRS)
                )
                self.arq_cleanup()

    def arq_session_keep_alive_watchdog(self) -> None:
        """
        watchdog which checks if we are running into a connection timeout
        ARQ SESSION
        """
        if (
                ARQ.arq_session
                and TNC.tnc_state == "BUSY"
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
                        ARQ.arq_session
                        and self.IS_ARQ_SESSION_MASTER
                        and ARQ.arq_session_state == "connected"
                        # and not self.arq_file_transfer
                ):
                    threading.Event().wait(1)
                    self.transmit_session_heartbeat()
                    threading.Event().wait(2)

    def send_test_frame(self) -> None:
        """Send an empty test frame"""
        test_frame = bytearray(126)
        test_frame[:1] = bytes([FR_TYPE.TEST_FRAME.value])
        self.enqueue_frame_for_tx(
            frame_to_tx=[test_frame], c2_mode=FREEDV_MODE.datac13.value
        )

    def send_fec(self, mode, wakeup, payload, mycallsign):
        """Send an empty test frame"""
        print(wakeup)
        print(payload)
        print(mycallsign)

        mode_int = codec2.freedv_get_mode_value_by_name(mode)
        payload_per_frame = modem.get_bytes_per_frame(mode_int) - 2
        fec_payload_length = payload_per_frame - 1

        if wakeup:
            mode_int_wakeup = codec2.freedv_get_mode_value_by_name("sig0")
            payload_per_wakeup_frame = modem.get_bytes_per_frame(mode_int_wakeup) - 2
            fec_wakeup_frame = bytearray(payload_per_wakeup_frame)
            fec_wakeup_frame[:1] = bytes([FR_TYPE.FEC_WAKEUP.value])
            fec_wakeup_frame[1:7] = helpers.callsign_to_bytes(mycallsign)
            fec_wakeup_frame[7:8] = bytes([mode_int])
            fec_wakeup_frame[8:9] = bytes([1]) # n payload bursts
            print(mode_int_wakeup)

            self.enqueue_frame_for_tx(
                frame_to_tx=[fec_wakeup_frame], c2_mode=codec2.FREEDV_MODE["sig1"].value
            )
        time.sleep(1)
        fec_frame = bytearray(payload_per_frame)
        fec_frame[:1] = bytes([FR_TYPE.FEC.value])
        fec_frame[1:payload_per_frame] = bytes(payload[:fec_payload_length])
        self.enqueue_frame_for_tx(
            frame_to_tx=[fec_frame], c2_mode=codec2.FREEDV_MODE[mode].value
        )

    def send_fec_is_writing(self, mycallsign) -> None:
        """Send an fec is writing frame"""

        fec_frame = bytearray(14)
        fec_frame[:1] = bytes([FR_TYPE.IS_WRITING.value])
        fec_frame[1:7] = helpers.callsign_to_bytes(mycallsign)

        # send burst only if channel not busy - but without waiting
        # otherwise burst will be dropped
        if not ModemParam.channel_busy and not TNC.transmitting:
            self.enqueue_frame_for_tx(
                frame_to_tx=[fec_frame], c2_mode=codec2.FREEDV_MODE["sig0"].value
            )
        else:
            return False


    def save_data_to_folder(self,
                            transmission_uuid,
                            timestamp,
                            mycallsign,
                            dxcallsign,
                            dxgrid,
                            data_frame
                            ):

        """
        Save received data to folder
        Also supports chat messages
        """

        try:

            self.log.info("[TNC] ARQ | RX | saving data to folder")

            mycallsign = str(mycallsign, "UTF-8")
            dxcallsign = str(dxcallsign, "UTF-8")

            folder_path = "received"
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            callsign_path = f"{mycallsign}_{dxcallsign}"
            if not os.path.exists(f"{folder_path}/{callsign_path}"):
                os.makedirs(f"{folder_path}/{callsign_path}")

            split_char = b"\0;\1;"
            n_objects = 9
            decoded_data = data_frame.split(split_char)
            # if we have a false positive in case our split_char is available in data
            # lets stick the data together, so we are not loosing it
            if len(decoded_data) > n_objects:
                file_data = b''.join(decoded_data[n_objects:])

                # slice is crashing nuitka
                # decoded_data = [*decoded_data[:n_objects], file_data]
                decoded_data = decoded_data[:n_objects] + [file_data]

            if decoded_data[0] in [b'm']:
                checksum_delivered = str(decoded_data[2], "utf-8").lower()
                # transmission_uuid = decoded_data[3]
                message = decoded_data[5]
                filename = decoded_data[6]
                # filetype = decoded_data[7]
                # timestamp = decoded_data[4]
                data = decoded_data[8]
            else:
                message = b''
                filename = b''

            # save file to folder
            if filename not in [b'', b'undefined']:
                # doing crc check
                crc = helpers.get_crc_32(data).hex().lower()
                validity = checksum_delivered == crc
                self.log.info(
                    "[TNC] ARQ | RX | checking data crc",
                    crc_delivered=checksum_delivered,
                    crc_calculated=crc,
                    valid=validity,
                )
                filename = str(filename, "UTF-8")
                filename_complex = f"{timestamp}_{transmission_uuid}_{filename}"
                with open(f"{folder_path}/{callsign_path}/{filename_complex}", "wb") as file:
                    file.write(data)

            if message not in [b'', b'undefined']:
                # save message to folder
                message_name = f"{timestamp}_{transmission_uuid}_msg.txt"
                with open(f"{folder_path}/{callsign_path}/{message_name}", "wb") as file:
                    file.write(message)

        except Exception as e:
            self.log.error("[TNC] error saving data to folder", e=e)