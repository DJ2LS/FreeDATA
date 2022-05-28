#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
daemon.py

Author: DJ2LS, January 2022

daemon for providing basic information for the tnc like audio or serial devices

"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel

import argparse
import atexit
import multiprocessing
import os
import signal
import socketserver
import subprocess
import sys
import threading
import time

import audio
import crcengine
import log_handler
import serial.tools.list_ports
import sock
import static
import structlog
import ujson as json


# signal handler for closing aplication
def signal_handler(sig, frame):
    """
    Signal handler for closing the network socket on app exit
    Args:
      sig:
      frame:

    Returns: system exit
    """
    print("Closing daemon...")
    sock.CLOSE_SIGNAL = True
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


class DAEMON:
    """
    Daemon class

    """
    log = structlog.get_logger("DAEMON")

    def __init__(self):
        # load crc engine
        self.crc_algorithm = crcengine.new("crc16-ccitt-false")  # load crc8 library

        self.daemon_queue = sock.DAEMON_QUEUE
        update_audio_devices = threading.Thread(
            target=self.update_audio_devices, name="UPDATE_AUDIO_DEVICES", daemon=True
        )
        update_audio_devices.start()

        update_serial_devices = threading.Thread(
            target=self.update_serial_devices, name="UPDATE_SERIAL_DEVICES", daemon=True
        )
        update_serial_devices.start()

        worker = threading.Thread(target=self.worker, name="WORKER", daemon=True)
        worker.start()

    def update_audio_devices(self):
        """
        Update audio devices and set to static
        """
        while True:
            try:
                if not static.TNCSTARTED:
                    (
                        static.AUDIO_INPUT_DEVICES,
                        static.AUDIO_OUTPUT_DEVICES,
                    ) = audio.get_audio_devices()
            except Exception as err1:
                self.log.error(
                    "[DMN] update_audio_devices: Exception gathering audio devices:",
                    e=err1,
                )
            time.sleep(1)

    def update_serial_devices(self):
        """
        Update serial devices and set to static
        """
        while True:
            try:
                serial_devices = []
                ports = serial.tools.list_ports.comports()
                for port, desc, hwid in ports:
                    # calculate hex of hwid if we have unique names
                    crc_hwid = self.crc_algorithm(bytes(hwid, encoding="utf-8"))
                    crc_hwid = crc_hwid.to_bytes(2, byteorder="big")
                    crc_hwid = crc_hwid.hex()
                    description = f"{desc} [{crc_hwid}]"
                    serial_devices.append(
                        {"port": str(port), "description": str(description)}
                    )

                static.SERIAL_DEVICES = serial_devices
                time.sleep(1)
            except Exception as err1:
                self.log.error(
                    "[DMN] update_serial_devices: Exception gathering serial devices:",
                    e=err1,
                )

    def worker(self):
        """
        Worker to handle the received commands
        """
        while True:
            try:
                data = self.daemon_queue.get()

                # data[1] mycall
                # data[2] mygrid
                # data[3] rx_audio
                # data[4] tx_audio
                # data[5] devicename
                # data[6] deviceport
                # data[7] serialspeed
                # data[8] pttprotocol
                # data[9] pttport
                # data[10] data_bits
                # data[11] stop_bits
                # data[12] handshake
                # data[13] radiocontrol
                # data[14] rigctld_ip
                # data[15] rigctld_port
                # data[16] send_scatter
                # data[17] send_fft
                # data[18] low_bandwidth_mode
                # data[19] tuning_range_fmin
                # data[20] tuning_range_fmax
                # data[21] enable FSK
                # data[22] tx-audio-level
                # data[23] respond_to_cq

                if data[0] == "STARTTNC":
                    self.log.warning("[DMN] Starting TNC", rig=data[5], port=data[6])

                    # list of parameters, necessary for running subprocess command as a list
                    options = []

                    options.append("--port")
                    options.append(str(static.DAEMONPORT - 1))

                    options.append("--mycall")
                    options.append(data[1])

                    options.append("--mygrid")
                    options.append(data[2])

                    options.append("--rx")
                    options.append(data[3])

                    options.append("--tx")
                    options.append(data[4])

                    # if radiocontrol != disabled
                    # this should hopefully avoid a ton of problems if we are just running in
                    # disabled mode

                    if data[13] != "disabled":
                        options.append("--devicename")
                        options.append(data[5])

                        options.append("--deviceport")
                        options.append(data[6])

                        options.append("--serialspeed")
                        options.append(data[7])

                        options.append("--pttprotocol")
                        options.append(data[8])

                        options.append("--pttport")
                        options.append(data[9])

                        options.append("--data_bits")
                        options.append(data[10])

                        options.append("--stop_bits")
                        options.append(data[11])

                        options.append("--handshake")
                        options.append(data[12])

                        options.append("--radiocontrol")
                        options.append(data[13])

                        if data[13] == "rigctld":
                            options.append("--rigctld_ip")
                            options.append(data[14])

                            options.append("--rigctld_port")
                            options.append(data[15])

                    if data[16] == "True":
                        options.append("--scatter")

                    if data[17] == "True":
                        options.append("--fft")

                    if data[18] == "True":
                        options.append("--500hz")

                    options.append("--tuning_range_fmin")
                    options.append(data[19])

                    options.append("--tuning_range_fmax")
                    options.append(data[20])

                    # overriding FSK mode
                    # if data[21] == "True":
                    #    options.append("--fsk")

                    options.append("--tx-audio-level")
                    options.append(data[22])

                    if data[23] == "True":
                        options.append("--qrv")

                    # Try running tnc from binary, else run from source
                    # This helps running the tnc in a developer environment
                    try:
                        command = []
                        if sys.platform in ["linux", "darwin"]:
                            command.append("./freedata-tnc")
                        elif sys.platform in ["win32", "win64"]:
                            command.append("freedata-tnc.exe")

                        command += options
                        proc = subprocess.Popen(command)

                        atexit.register(proc.kill)

                        self.log.info("[DMN] TNC started", path="binary")
                    except FileNotFoundError as err1:
                        self.log.info("[DMN] worker: ", e=err1)
                        command = []
                        if sys.platform in ["linux", "darwin"]:
                            command.append("python3")
                        elif sys.platform in ["win32", "win64"]:
                            command.append("python")

                        command.append("main.py")
                        command += options
                        proc = subprocess.Popen(command)
                        atexit.register(proc.kill)

                        self.log.info("[DMN] TNC started", path="source")

                    static.TNCPROCESS = proc
                    static.TNCSTARTED = True
                """
                # WE HAVE THIS PART in SOCKET
                if data[0] == "STOPTNC":
                        static.TNCPROCESS.kill()
                        self.log.warning("[DMN] Stopping TNC")
                        #os.kill(static.TNCPROCESS, signal.SIGKILL)
                        static.TNCSTARTED = False
                """
                # data[1] devicename
                # data[2] deviceport
                # data[3] serialspeed
                # data[4] pttprotocol
                # data[5] pttport
                # data[6] data_bits
                # data[7] stop_bits
                # data[8] handshake
                # data[9] radiocontrol
                # data[10] rigctld_ip
                # data[11] rigctld_port
                if data[0] == "TEST_HAMLIB":
                    devicename = data[1]
                    deviceport = data[2]
                    serialspeed = data[3]
                    pttprotocol = data[4]
                    pttport = data[5]
                    data_bits = data[6]
                    stop_bits = data[7]
                    handshake = data[8]
                    radiocontrol = data[9]
                    rigctld_ip = data[10]
                    rigctld_port = data[11]

                    # check how we want to control the radio
                    if radiocontrol == "direct":
                        import rig
                    elif radiocontrol == "rigctl":
                        import rigctl as rig
                    elif radiocontrol == "rigctld":
                        import rigctld as rig
                    else:
                        import rigdummy as rig

                    hamlib = rig.radio()
                    hamlib.open_rig(
                        devicename=devicename,
                        deviceport=deviceport,
                        hamlib_ptt_type=pttprotocol,
                        serialspeed=serialspeed,
                        pttport=pttport,
                        data_bits=data_bits,
                        stop_bits=stop_bits,
                        handshake=handshake,
                        rigctld_ip=rigctld_ip,
                        rigctld_port=rigctld_port,
                    )

                    # hamlib_version = rig.hamlib_version

                    hamlib.set_ptt(True)
                    pttstate = hamlib.get_ptt()

                    if pttstate:
                        self.log.info("[DMN] Hamlib PTT", status="SUCCESS")
                        response = {"command": "test_hamlib", "result": "SUCCESS"}
                    elif not pttstate:
                        self.log.warning("[DMN] Hamlib PTT", status="NO SUCCESS")
                        response = {"command": "test_hamlib", "result": "NOSUCCESS"}
                    else:
                        self.log.error("[DMN] Hamlib PTT", status="FAILED")
                        response = {"command": "test_hamlib", "result": "FAILED"}

                    hamlib.set_ptt(False)
                    hamlib.close_rig()

                    jsondata = json.dumps(response)
                    sock.SOCKET_QUEUE.put(jsondata)

            except Exception as err1:
                self.log.error("[DMN] worker: Exception: ", e=err1)


if __name__ == "__main__":
    mainlog = structlog.get_logger(__file__)
    # we need to run this on Windows for multiprocessing support
    multiprocessing.freeze_support()

    # --------------------------------------------GET PARAMETER INPUTS
    PARSER = argparse.ArgumentParser(description="FreeDATA Daemon")
    PARSER.add_argument(
        "--port",
        dest="socket_port",
        default=3001,
        help="Socket port in the range of 1024-65535",
        type=int,
    )
    ARGS = PARSER.parse_args()

    static.DAEMONPORT = ARGS.socket_port

    try:
        if sys.platform == "linux":
            logging_path = os.getenv("HOME") + "/.config/" + "FreeDATA/" + "daemon"

        if sys.platform == "darwin":
            logging_path = (
                os.getenv("HOME")
                + "/Library/"
                + "Application Support/"
                + "FreeDATA/"
                + "daemon"
            )

        if sys.platform in ["win32", "win64"]:
            logging_path = os.getenv("APPDATA") + "/" + "FreeDATA/" + "daemon"

        if not os.path.exists(logging_path):
            os.makedirs(logging_path)
        log_handler.setup_logging(logging_path)
    except Exception as err:
        mainlog.error("[DMN] logger init error", exception=err)

    try:
        mainlog.info("[DMN] Starting TCP/IP socket", port=static.DAEMONPORT)
        # https://stackoverflow.com/a/16641793
        socketserver.TCPServer.allow_reuse_address = True
        cmdserver = sock.ThreadedTCPServer(
            (static.HOST, static.DAEMONPORT), sock.ThreadedTCPRequestHandler
        )
        server_thread = threading.Thread(target=cmdserver.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    except Exception as err:
        mainlog.error(
            "[DMN] Starting TCP/IP socket failed", port=static.DAEMONPORT, e=err
        )
        sys.exit(1)
    daemon = DAEMON()

    mainlog.info(
        "[DMN] Starting FreeDATA Daemon",
        author="DJ2LS",
        year="2022",
        version=static.VERSION,
    )
    while True:
        time.sleep(1)
