#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
daemon.py

Author: DJ2LS, January 2022

daemon for providing basic information for the modem like audio or serial devices

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
from global_instances import ARQ, AudioParam, Beacon, Channel, Daemon, HamlibParam, ModemParam, Station, Statistics, TCIParam, Modem

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

        rigctld_watchdog_thread = threading.Thread(target=self.rigctld_watchdog, name="WORKER", daemon=True)
        rigctld_watchdog_thread.start()


    def rigctld_watchdog(self):
        """
        Check for rigctld status
        Returns:

        """
        while True:
            threading.Event().wait(0.01)
            try:
                print(Daemon.rigctldprocess)
                result = Daemon.rigctldprocess
                print(f'Standard Output: {result.stdout}')
                print(f'Standard Error: {result.stderr}')
            except Exception:
                pass


            # only continue, if we have a process object initialized
            if hasattr(Daemon.rigctldprocess, "returncode"):

                if Daemon.rigctldprocess.returncode in [None, "None"] or not Daemon.rigctldstarted:
                    Daemon.rigctldstarted = True
                    #outs, errs = Daemon.rigctldprocess.communicate(timeout=10)
                    #print(f"outs: {outs}")
                    #print(f"errs: {errs}")
                    print(Daemon.rigctldprocess)
                    result = Daemon.rigctldprocess
                    print(f'Standard Output: {result.stdout}')
                    print(f'Standard Error: {result.stderr}')


                else:
                    self.log.warning("[DMN] [RIGCTLD] [Watchdog] returncode detected",process=Daemon.rigctldprocess)
                    Daemon.rigctldstarted = False
                    # triggering another kill
                    Daemon.rigctldprocess.kill()
                    # erase process object
                    Daemon.rigctldprocess = None
            else:
                #Daemon.rigctldstarted = False
                pass
            #try:
            #    outs, errs = proc.communicate(timeout=15)
            #except TimeoutExpired:
            #    proc.kill()
            #    outs, errs = proc.communicate()


    def update_audio_devices(self):
        """
        Update audio devices and set to static
        """
        while True:
            try:
                if not Daemon.modemstarted:
                    (
                        AudioParam.audio_input_devices,
                        AudioParam.audio_output_devices,
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

                Daemon.serial_devices = serial_devices
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
                # data[1] mycall
                # data[2] mygrid
                # data[3] rx_audio
                # data[4] tx_audio
                # data[5] radiocontrol
                # data[6] rigctld_ip
                # data[7] rigctld_port
                # data[8] send_scatter
                # data[9] send_fft
                # data[10] low_bandwidth_mode
                # data[11] tuning_range_fmin
                # data[12] tuning_range_fmax
                # data[13] enable FSK
                # data[14] tx-audio-level
                # data[15] respond_to_cq
                # data[16] rx_buffer_size
                # data[17] explorer
                # data[18] ssid_list
                # data[19] auto_tune
                # data[20] stats
                # data[21] tx_delay

                if data[0] == "STARTModem":
                    self.start_modem(data)

                if data[0] == "TEST_HAMLIB":
                    # data[9] radiocontrol
                    # data[10] rigctld_ip
                    # data[11] rigctld_port
                    self.test_hamlib_ptt(data)

                if data[0] == "START_RIGCTLD":
                    """
                    data[0] START_RIGCTLD,
                    data[1] hamlib_deviceid,
                    data[2] hamlib_deviceport,
                    data[3] hamlib_stop_bits,
                    data[4] hamlib_data_bits,
                    data[5] hamlib_handshake,
                    data[6] hamlib_serialspeed,
                    data[7] hamlib_dtrstate,
                    data[8] hamlib_pttprotocol,
                    data[9] hamlib_ptt_port,
                    data[10] hamlib_dcd,
                    data[11] hamlbib_serialspeed_ptt,
                    data[12] hamlib_rigctld_port,
                    data[13] hamlib_rigctld_ip,
                    data[14] hamlib_rigctld_path,
                    data[15] hamlib_rigctld_server_port,
                    data[16] hamlib_rigctld_custom_args
                    """
                    self.start_rigctld(data)


            except Exception as err1:
                self.log.error("[DMN] worker: Exception: ", e=err1)

    def test_hamlib_ptt(self, data):
        radiocontrol = data[1]

        # check how we want to control the radio
        if radiocontrol == "direct":
            print("direct hamlib support deprecated - not usable anymore")
            sys.exit(1)
        elif radiocontrol == "rigctl":
            print("rigctl support deprecated - not usable anymore")
            sys.exit(1)
        elif radiocontrol == "rigctld":
            import rigctld as rig
            rigctld_ip = data[2]
            rigctld_port = data[3]

        elif radiocontrol == "tci":
            import tci as rig
            rigctld_ip = data[22]
            rigctld_port = data[23]

        else:
            import rigdummy as rig
            rigctld_ip = '127.0.0.1'
            rigctld_port = '0'

        hamlib = rig.radio()
        hamlib.open_rig(
            rigctld_ip=rigctld_ip,
            rigctld_port=rigctld_port,
        )

        # hamlib_version = rig.hamlib_version

        hamlib.set_ptt(True)
        #Allow a little time for network based rig to register PTT is active
        time.sleep(.250)
        if hamlib.get_ptt():
            self.log.info("[DMN] Hamlib PTT", status="SUCCESS")
            response = {"command": "test_hamlib", "result": "SUCCESS"}
        else:
            self.log.warning("[DMN] Hamlib PTT", status="NO SUCCESS")
            response = {"command": "test_hamlib", "result": "NOSUCCESS"}

        hamlib.set_ptt(False)
        hamlib.close_rig()

        jsondata = json.dumps(response)
        sock.SOCKET_QUEUE.put(jsondata)

    def start_rigctld(self, data):
        # Seems to be working on Win
        """
        data[0] START_RIGCTLD,
        data[1] hamlib_deviceid,
        data[2] hamlib_deviceport,
        data[3] hamlib_stop_bits,
        data[4] hamlib_data_bits,
        data[5] hamlib_handshake,
        data[6] hamlib_serialspeed,
        data[7] hamlib_dtrstate,
        data[8] hamlib_pttprotocol,
        data[9] hamlib_ptt_port,
        data[10] hamlib_dcd,
        data[11] hamlbib_serialspeed_ptt,
        data[12] hamlib_rigctld_port,
        data[13] hamlib_rigctld_ip,
        data[14] hamlib_rigctld_path,
        data[15] hamlib_rigctld_server_port,
        data[16] hamlib_rigctld_custom_args
        """
        try:
            command = []

            isWin = False

            if sys.platform in ["darwin"]:
                if data[14] not in [""]:
                    # hamlib_rigctld_path
                    application_path = data[14]
                else:
                    application_path = "rigctld"

                command.append(f'{application_path}')

            elif sys.platform in ["linux", "darwin"]:
                if data[14] not in [""]:
                    # hamlib_rigctld_path
                    application_path = data[14]
                else:
                    application_path = "rigctld"
                command.append(f'{application_path}')
            elif sys.platform in ["win32", "win64"]:
                isWin=True
                if data[13].lower() == "localhost":
                    data[13]="127.0.0.1"
                if data[14] not in [""]:
                    # hamlib_rigctld_path
                    application_path = data[14]
                else:
                    application_path = "rigctld.exe"
                command.append(f'{application_path}')


            options = []

            # hamlib_deviceid
            if data[1] not in [None, "None", "ignore"]:
                options.append(("--model=" + data[1] ))

            # hamlib_deviceport
            if data[2] not in [None, "None", "ignore"]:
                options.append(("--rig-file="+ data[2]))
            # hamlib_stop_bits
            if data[3] not in [None, "None", "ignore"]:
                options.append(("--set-conf=stop_bits=" + data[3]))

            # hamlib_data_bits
            if data[4] not in [None, "None", "ignore"]:
                options.append(("--set-conf=data_bits=" + data[4]))


            # hamlib_handshake
            if data[5] not in [None, "None", "ignore"]:
                options.append(("--set-conf=serial_handshake=" + data[5]))


            # hamlib_serialspeed
            if data[6] not in [None, "None", "ignore"]:
                options.append(("--serial-speed=" + data[6]))

            # hamlib_dtrstate
            if data[7] not in [None, "None", "ignore"]:
                options.append(("--set-conf=dtr_state=" + data[7]))


            # hamlib_pttprotocol
            if data[8] not in [None, "None", "ignore"]:
                options.append(("--ptt-type=" + data[8]))


            # hamlib_ptt_port
            if data[9] not in [None, "None", "ignore"]:
                options.append(("--ptt-file=" + data[9]))


            # hamlib_dcd
            if data[10] not in [None, "None", "ignore"]:
                options.append(("--dcd-type=" + data[10]))


            # hamlbib_serialspeed_ptt
            if data[11] not in [None, "None", "ignore"]:
                # options.extend(("-m", data[11]))
                pass

            # hamlib_rigctld_port
            # Using this ensures rigctld starts on port configured in GUI
            if data[12] not in [None, "None", "ignore"]:
                 options.append(("--port="+ data[12]))

            # hamlib_rigctld_ip
            if data[13] not in [None, "None", "ignore"]:
                options.append(("--listen-addr="+ data[13]))

            # data[14] == hamlib_rigctld_path
            # maybe at wrong place in list...
            #Not needed for setting command line arguments

            # hamlib_rigctld_server_port
            # Ignore configured value and use value configured in GUI
            #if data[15] not in [None, "None", "ignore"]:
                # options.extend(("-m", data[15]))
            #    pass

            # hamlib_rigctld_custom_args
            if data[16] not in [None, "None", "ignore"]:
                for o in data[16].split(" "):
                    options.append(o)

            # append debugging paramter
            options.append(("-vvv"))
            command += options

            self.log.info("[DMN] starting rigctld: ", param=command)
            
            if not isWin:
                #proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                #proc = subprocess.Popen(command)
                proc = subprocess.run(command, shell=False, check=True, text=True, capture_output=True)
                print(f'Standard Output: {proc.stdout}')
                print(f'Standard Error: {proc.stderr}')
            else:
                #On windows, open rigctld in new window for easier troubleshooting
                proc = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE,close_fds=True)

            atexit.register(proc.kill)

            Daemon.rigctldstarted = True
            Daemon.rigctldprocess = proc



        except Exception as err:
            self.log.warning("[DMN] err starting rigctld: ", e=err)



    def start_modem(self, data):
        self.log.warning("[DMN] Starting Modem", rig=data[5], port=data[6])

        # list of parameters, necessary for running subprocess command as a list
        options = ["--port", str(DAEMON.port - 1)]

        # create an additional list entry for parameters not covered by gui
        data[50] = int(DAEMON.port - 1)

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

            if data[5] == "tci":
                options.append("--tci-ip")
                options.extend((data[22], "--tci-port"))
                options.append(data[23])


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

        if data[13] == "True":
            options.append("--fsk")

        options.append("--tx-delay")
        options.append(data[21])

        #Mesh
        print(data[24])
        if data[24] == "True":
            options.append("--mesh")
        print(options)
        # safe data to config file
        config.write_entire_config(data)

        # Try running modem from binary, else run from source
        # This helps running the modem in a developer environment
        try:
            command = []

            if (getattr(sys, 'frozen', False) or hasattr(sys, "_MEIPASS")) and sys.platform in ["darwin"]:
                # If the application is run as a bundle, the PyInstaller bootloader
                # extends the sys module by a flag frozen=True and sets the app
                # path into variable _MEIPASS'.
                application_path = sys._MEIPASS
                command.append(f'{application_path}/freedata-modem')

            elif sys.platform in ["linux", "darwin"]:
                command.append("./freedata-modem")
            elif sys.platform in ["win32", "win64"]:
                command.append("freedata-modem.exe")

            command += options

            proc = subprocess.Popen(command)

            atexit.register(proc.kill)

            Daemon.modemprocess = proc
            Daemon.modemstarted = True


            self.log.info("[DMN] Modem started", path="binary")
        except FileNotFoundError as err1:

            try:
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

                self.log.info("[DMN] Modem started", path="source")

                Daemon.modemprocess = proc
                Daemon.modemstarted = True
            except Exception as e:
                self.log.error("[DMN] Modem not started", error=e)
                Daemon.modemstarted = False



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

    DAEMON.port = ARGS.socket_port

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
        mainlog.info("[DMN] Starting TCP/IP socket", port=DAEMON.port)
        # https://stackoverflow.com/a/16641793
        socketserver.TCPServer.allow_reuse_address = True
        cmdserver = sock.ThreadedTCPServer(
            (Modem.host, DAEMON.port), sock.ThreadedTCPRequestHandler
        )
        server_thread = threading.Thread(target=cmdserver.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    except Exception as err:
        mainlog.error(
            "[DMN] Starting TCP/IP socket failed", port=DAEMON.port, e=err
        )
        sys.exit(1)
    daemon = DAEMON()

    mainlog.info(
        "[DMN] Starting FreeDATA Daemon",
        author="DJ2LS",
        year="2023",
        version=Modem.version,
    )
    while True:
        threading.Event().wait(1)
