#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:58:45 2020

@author: DJ2LS

main module for running the tnc
"""


# run tnc self test on startup before we are doing other things
# import selftest
# selftest.TEST()

# continue if we passed the test

import argparse
import multiprocessing
import os
import signal
import socketserver
import sys
import threading
import time
import config
import data_handler
import helpers
import log_handler
import modem
import static
import structlog
import explorer
import json

log = structlog.get_logger("main")

def signal_handler(sig, frame):
    """
    a signal handler, which closes the network/socket when closing the application
    Args:
      sig: signal
      frame:

    Returns: system exit

    """
    print("Closing TNC...")
    sock.CLOSE_SIGNAL = True
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    # This is for Windows multiprocessing support
    multiprocessing.freeze_support()
    # --------------------------------------------GET PARAMETER INPUTS
    PARSER = argparse.ArgumentParser(description="FreeDATA TNC")

    #PARSER.add_argument(
    #    "--use-config",
    #    dest="configfile",
    #    action="store_true",
    #    help="Use the default config file config.ini",
    #)
    PARSER.add_argument(
        "--use-config",
        dest="configfile",
        default=False,
        type=str,
        help="Use the default config file config.ini",
    )

    PARSER.add_argument(
        "--save-to-folder",
        dest="savetofolder",
        default=False,
        action="store_true",
        help="Save received data to local folder",
    )

    PARSER.add_argument(
        "--mycall",
        dest="mycall",
        default="AA0AA",
        help="My callsign",
        type=str
    )
    PARSER.add_argument(
        "--ssid",
        dest="ssid_list",
        nargs="*",
        default=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        help="SSID list we are responding to",
        type=int,
    )
    PARSER.add_argument(
        "--mygrid",
        dest="mygrid",
        default="JN12AA",
        help="My gridsquare",
        type=str
    )
    PARSER.add_argument(
        "--rx",
        dest="audio_input_device",
        default=0,
        help="listening sound card",
        type=str,
    )
    PARSER.add_argument(
        "--tx",
        dest="audio_output_device",
        default=0,
        help="transmitting sound card",
        type=str,
    )
    PARSER.add_argument(
        "--port",
        dest="socket_port",
        default=3000,
        help="Socket port  in the range of 1024-65536",
        type=int,
    )
    PARSER.add_argument(
        "--radiocontrol",
        dest="hamlib_radiocontrol",
        choices=["disabled", "direct", "rigctl", "rigctld"],
        default="disabled",
        help="Set how you want to control your radio",
    )
    PARSER.add_argument(
        "--rigctld_port",
        dest="rigctld_port",
        default=4532,
        type=int,
        help="Set rigctld port",
    )
    PARSER.add_argument(
        "--rigctld_ip", dest="rigctld_ip", default="localhost", help="Set rigctld ip"
    )
    PARSER.add_argument(
        "--scatter",
        dest="send_scatter",
        action="store_true",
        help="Send scatter information via network",
    )
    PARSER.add_argument(
        "--fft",
        dest="send_fft",
        action="store_true",
        help="Send fft information via network",
    )
    PARSER.add_argument(
        "--500hz",
        dest="low_bandwidth_mode",
        action="store_true",
        help="Enable low bandwidth mode ( 500 Hz only )",
    )
    PARSER.add_argument(
        "--fsk",
        dest="enable_fsk",
        action="store_true",
        help="Enable FSK mode for ping, beacon and CQ",
    )
    PARSER.add_argument(
        "--qrv",
        dest="enable_respond_to_cq",
        action="store_true",
        help="Enable sending a QRV frame if CQ received",
    )
    PARSER.add_argument(
        "--tuning_range_fmin",
        dest="tuning_range_fmin",
        choices=[-50.0, -100.0, -150.0, -200.0, -250.0],
        default=-50.0,
        help="Tuning range fmin",
        type=float,
    )
    PARSER.add_argument(
        "--tuning_range_fmax",
        dest="tuning_range_fmax",
        choices=[50.0, 100.0, 150.0, 200.0, 250.0],
        default=50.0,
        help="Tuning range fmax",
        type=float,
    )
    PARSER.add_argument(
        "--tx-audio-level",
        dest="tx_audio_level",
        default=50,
        help="Set the tx audio level at an early stage",
        type=int,
    )
    PARSER.add_argument(
        "--rx-buffer-size",
        dest="rx_buffer_size",
        default=16,
        help="Set the maximum size of rx buffer.",
        type=int,
    )
    PARSER.add_argument(
        "--explorer",
        dest="enable_explorer",
        action="store_true",
        help="Enable sending tnc data to https://explorer.freedata.app",
    )

    PARSER.add_argument(
        "--tune",
        dest="enable_audio_auto_tune",
        action="store_true",
        help="Enable auto tuning of audio level with ALC information form hamlib",
    )

    PARSER.add_argument(
        "--stats",
        dest="enable_stats",
        action="store_true",
        help="Enable publishing stats to https://freedata.app",
    )

    PARSER.add_argument(
        "--tci",
        dest="audio_enable_tci",
        action="store_true",
        help="Enable TCI as audio source",
    )

    PARSER.add_argument(
        "--tci-ip",
        dest="tci_ip",
        default='127.0.0.1',
        type=str,
        help="Set tci destination ip",
    )

    PARSER.add_argument(
        "--tci-port",
        dest="tci_port",
        default=9000,
        type=int,
        help="Set tci destination port",
    )

    ARGS = PARSER.parse_args()

    # set save to folder state for allowing downloading files to local file system
    static.ARQ_SAVE_TO_FOLDER = ARGS.savetofolder

    if not ARGS.configfile:
    
    
        # additional step for being sure our callsign is correctly
        # in case we are not getting a station ssid
        # then we are forcing a station ssid = 0
        try:
            mycallsign = bytes(ARGS.mycall.upper(), "utf-8")
            mycallsign = helpers.callsign_to_bytes(mycallsign)
            static.MYCALLSIGN = helpers.bytes_to_callsign(mycallsign)
            static.MYCALLSIGN_CRC = helpers.get_crc_24(static.MYCALLSIGN)
            static.SSID_LIST = ARGS.ssid_list
            # check if own ssid is always part of ssid list
            own_ssid = int(static.MYCALLSIGN.split(b"-")[1])
            if own_ssid not in static.SSID_LIST:
                static.SSID_LIST.append(own_ssid)

            static.MYGRID = bytes(ARGS.mygrid, "utf-8")

            # check if we have an int or str as device name
            try:
                static.AUDIO_INPUT_DEVICE = int(ARGS.audio_input_device)
            except ValueError:
                static.AUDIO_INPUT_DEVICE = ARGS.audio_input_device
            try:
                static.AUDIO_OUTPUT_DEVICE = int(ARGS.audio_output_device)
            except ValueError:
                static.AUDIO_OUTPUT_DEVICE = ARGS.audio_output_device

            static.PORT = ARGS.socket_port
            static.HAMLIB_RADIOCONTROL = ARGS.hamlib_radiocontrol
            static.HAMLIB_RIGCTLD_IP = ARGS.rigctld_ip
            static.HAMLIB_RIGCTLD_PORT = str(ARGS.rigctld_port)
            static.ENABLE_SCATTER = ARGS.send_scatter
            static.ENABLE_FFT = ARGS.send_fft
            static.ENABLE_FSK = ARGS.enable_fsk
            static.LOW_BANDWIDTH_MODE = ARGS.low_bandwidth_mode
            static.TUNING_RANGE_FMIN = ARGS.tuning_range_fmin
            static.TUNING_RANGE_FMAX = ARGS.tuning_range_fmax
            static.TX_AUDIO_LEVEL = ARGS.tx_audio_level
            static.RESPOND_TO_CQ = ARGS.enable_respond_to_cq
            static.RX_BUFFER_SIZE = ARGS.rx_buffer_size
            static.ENABLE_EXPLORER = ARGS.enable_explorer
            static.AUDIO_AUTO_TUNE = ARGS.enable_audio_auto_tune
            static.ENABLE_STATS = ARGS.enable_stats
            static.AUDIO_ENABLE_TCI = ARGS.audio_enable_tci
            static.TCI_IP = ARGS.tci_ip
            static.TCI_PORT = ARGS.tci_port

        except Exception as e:
            log.error("[DMN] Error reading config file", exception=e)

    else:
        configfile = ARGS.configfile
        # init config
        conf = config.CONFIG(configfile)
        try:
            # additional step for being sure our callsign is correctly
            # in case we are not getting a station ssid
            # then we are forcing a station ssid = 0
            mycallsign = bytes(conf.get('STATION', 'mycall', 'AA0AA'), "utf-8")
            mycallsign = helpers.callsign_to_bytes(mycallsign)
            static.MYCALLSIGN = helpers.bytes_to_callsign(mycallsign)
            static.MYCALLSIGN_CRC = helpers.get_crc_24(static.MYCALLSIGN)

            #json.loads = for converting str list to list
            static.SSID_LIST = json.loads(conf.get('STATION', 'ssid_list', '[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]'))

            static.MYGRID = bytes(conf.get('STATION', 'mygrid', 'JN12aa'), "utf-8")
            # check if we have an int or str as device name
            try:
                static.AUDIO_INPUT_DEVICE = int(conf.get('AUDIO', 'rx', '0'))
            except ValueError:
                static.AUDIO_INPUT_DEVICE = conf.get('AUDIO', 'rx', '0')
            try:
                static.AUDIO_OUTPUT_DEVICE = int(conf.get('AUDIO', 'tx', '0'))
            except ValueError:
                static.AUDIO_OUTPUT_DEVICE = conf.get('AUDIO', 'tx', '0')

            static.PORT = int(conf.get('NETWORK', 'tncport', '3000'))
            static.HAMLIB_RADIOCONTROL = conf.get('RADIO', 'radiocontrol', 'rigctld')
            static.HAMLIB_RIGCTLD_IP = conf.get('RADIO', 'rigctld_ip', '127.0.0.1')
            static.HAMLIB_RIGCTLD_PORT = str(conf.get('RADIO', 'rigctld_port', '4532'))
            static.ENABLE_SCATTER = conf.get('TNC', 'scatter', 'True')
            static.ENABLE_FFT = conf.get('TNC', 'fft', 'True')
            static.ENABLE_FSK = conf.get('TNC', 'fsk', 'False')
            static.LOW_BANDWIDTH_MODE = conf.get('TNC', 'narrowband', 'False')
            static.TUNING_RANGE_FMIN = float(conf.get('TNC', 'fmin', '-50.0'))
            static.TUNING_RANGE_FMAX = float(conf.get('TNC', 'fmax', '50.0'))
            static.TX_AUDIO_LEVEL = int(conf.get('AUDIO', 'txaudiolevel', '100'))
            static.RESPOND_TO_CQ = conf.get('TNC', 'qrv', 'True')
            static.RX_BUFFER_SIZE = int(conf.get('TNC', 'rxbuffersize', '16'))
            static.ENABLE_EXPLORER = conf.get('TNC', 'explorer', 'False')
            static.AUDIO_AUTO_TUNE = conf.get('AUDIO', 'auto_tune', 'False')
            static.ENABLE_STATS = conf.get('TNC', 'stats', 'False')
            static.AUDIO_ENABLE_TCI = conf.get('AUDIO', 'enable_tci', 'False')
            static.TCI_IP = str(conf.get('AUDIO', 'tci_ip', 'localhost'))
            static.TCI_PORT = int(conf.get('AUDIO', 'tci_port', '50001'))
        except KeyError as e:
            log.warning("[CFG] Error reading config file near", key=str(e))
        except Exception as e:
            log.warning("[CFG] Error", e=e)

    # make sure the own ssid is always part of the ssid list
    my_ssid = int(static.MYCALLSIGN.split(b'-')[1])
    if my_ssid not in static.SSID_LIST:
        static.SSID_LIST.append(my_ssid)

    # we need to wait until we got all parameters from argparse first before we can load the other modules
    import sock

    # config logging
    try:
        if sys.platform == "linux":
            logging_path = os.getenv("HOME") + "/.config/" + "FreeDATA/" + "tnc"

        if sys.platform == "darwin":
            logging_path = (
                os.getenv("HOME")
                + "/Library/"
                + "Application Support/"
                + "FreeDATA/"
                + "tnc"
            )

        if sys.platform in ["win32", "win64"]:
            logging_path = os.getenv("APPDATA") + "/" + "FreeDATA/" + "tnc"

        if not os.path.exists(logging_path):
            os.makedirs(logging_path)
        log_handler.setup_logging(logging_path)
    except Exception as err:
        log.error("[DMN] logger init error", exception=err)

    log.info(
        "[TNC] Starting FreeDATA", author="DJ2LS", version=static.VERSION
    )

    # start data handler
    data_handler.DATA()

    # start modem
    modem = modem.RF()

    # optionally start explorer module
    if static.ENABLE_EXPLORER:
        log.info("[EXPLORER] Publishing to https://explorer.freedata.app", state=static.ENABLE_EXPLORER)
        explorer = explorer.explorer()

    # --------------------------------------------START CMD SERVER
    try:
        log.info("[TNC] Starting TCP/IP socket", port=static.PORT)
        # https://stackoverflow.com/a/16641793
        socketserver.TCPServer.allow_reuse_address = True
        cmdserver = sock.ThreadedTCPServer(
            (static.HOST, static.PORT), sock.ThreadedTCPRequestHandler
        )
        server_thread = threading.Thread(target=cmdserver.serve_forever)

        server_thread.daemon = True
        server_thread.start()

    except Exception as err:
        log.error("[TNC] Starting TCP/IP socket failed", port=static.PORT, e=err)
        sys.exit(1)
    while True:
        threading.Event().wait(1)
