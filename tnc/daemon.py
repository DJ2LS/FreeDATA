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
import config


# signal handler for closing application
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
            threading.Event().wait(1)

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
                threading.Event().wait(1)
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
                # increase length of list for storing additional
                # parameters starting at entry 64
                data = data[:64] + [None] * (64 - len(data))
                print(data)
                # data[1] mycall
                # data[2] mygrid
                # data[3] rx_audio
                # data[4] tx_audio
                # REMOVED - data[5] devicename
                # REMOVED - data[6] deviceport
                # REMOVED - data[7] serialspeed
                # REMOVED - data[8] pttprotocol
                # REMOVED - data[9] pttport
                # REMOVED - data[10] data_bits
                # REMOVED - data[11] stop_bits
                # REMOVED - data[12] handshake
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
                # data[24] rx_buffer_size
                # data[25] explorer
                # data[26] ssid_list
                # data[27] auto_tune
                # data[28] stats
                # TODO: We need to remove 5-12 and adjust the list number for other paramters
                # This is only a dirty fix

                if data[0] == "STARTTNC":
                    self.log.warning("[DMN] Starting TNC", rig=data[5], port=data[6])

                    # list of parameters, necessary for running subprocess command as a list
                    options = ["--port", str(static.DAEMONPORT - 1)]

                    # create an additional list entry for parameters not covered by gui
                    data[50] = int(static.DAEMONPORT - 1)

                    options.append("--mycall")
                    options.extend((data[1], "--mygrid"))
                    options.extend((data[2], "--rx"))
                    options.extend((data[3], "--tx"))
                    options.append(data[4])

                    # if radiocontrol != disabled
                    # this should hopefully avoid a ton of problems if we are just running in
                    # disabled mode

                    if data[5] != "disabled":

                        options.append("--radiocontrol")
                        options.append(data[5])

                        if data[5] == "rigctld":
                            options.append("--rigctld_ip")
                            options.extend((data[6], "--rigctld_port"))
                            options.append(data[7])

                    if data[8] == "True":
                        options.append("--scatter")

                    if data[9] == "True":
                        options.append("--fft")

                    if data[10] == "True":
                        options.append("--500hz")

                    options.append("--tuning_range_fmin")
                    options.extend((data[11], "--tuning_range_fmax"))
                    options.extend((data[12], "--tx-audio-level"))
                    options.append(data[14])

                    if data[15] == "True":
                        options.append("--qrv")

                    options.append("--rx-buffer-size")
                    options.append(data[16])

                    if data[17] == "True":
                        options.append("--explorer")

                    options.append("--ssid")
                    options.extend(str(i) for i in data[18])
                    if data[19] == "True":
                        options.append("--tune")

                    if data[20] == "True":
                        options.append("--stats")

                    # safe data to config file
                    config.write_entire_config(data)




                    # Try running tnc from binary, else run from source
                    # This helps running the tnc in a developer environment
                    try:
                        command = []

                        if (getattr(sys, 'frozen', False) or hasattr(sys, "_MEIPASS")) and sys.platform in ["darwin"]:
                            # If the application is run as a bundle, the PyInstaller bootloader
                            # extends the sys module by a flag frozen=True and sets the app
                            # path into variable _MEIPASS'.
                            application_path = sys._MEIPASS
                            command.append(f'{application_path}/freedata-tnc')

                        elif sys.platform in ["linux", "darwin"]:
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
                        print(command)
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

                # data[9] radiocontrol
                # data[10] rigctld_ip
                # data[11] rigctld_port
                if data[0] == "TEST_HAMLIB":

                    radiocontrol = data[1]
                    rigctld_ip = data[2]
                    rigctld_port = data[3]

                    # check how we want to control the radio
                    if radiocontrol == "direct":
                        print("direct hamlib support deprecated - not usable anymore")
                        sys.exit(1)
                    elif radiocontrol == "rigctl":
                        print("rigctl support deprecated - not usable anymore")
                        sys.exit(1)
                    elif radiocontrol == "rigctld":
                        import rigctld as rig
                    else:
                        import rigdummy as rig

                    hamlib = rig.radio()
                    hamlib.open_rig(
                        rigctld_ip=rigctld_ip,
                        rigctld_port=rigctld_port,
                    )

                    # hamlib_version = rig.hamlib_version

                    hamlib.set_ptt(True)
                    if pttstate := hamlib.get_ptt():
                        self.log.info("[DMN] Hamlib PTT", status="SUCCESS")
                        response = {"command": "test_hamlib", "result": "SUCCESS"}
                    else:
                        self.log.warning("[DMN] Hamlib PTT", status="NO SUCCESS")
                        response = {"command": "test_hamlib", "result": "NOSUCCESS"}

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

    # init config
    config = config.CONFIG("config.ini")

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
        threading.Event().wait(1)
