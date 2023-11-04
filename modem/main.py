#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:58:45 2020

@author: DJ2LS

main module for running the modem
"""


# run modem self test on startup before we are doing other things
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
from global_instances import ARQ, AudioParam, Beacon, Channel, Daemon, HamlibParam, ModemParam, Station, Statistics, TCIParam, Modem, MeshParam
import structlog
import explorer
import json
import mesh
log = structlog.get_logger("main")

def signal_handler(sig, frame):
    """
    a signal handler, which closes the network/socket when closing the application
    Args:
      sig: signal
      frame:

    Returns: system exit

    """
    print("Closing Modem...")
    sock.CLOSE_SIGNAL = True
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    # This is for Windows multiprocessing support
    multiprocessing.freeze_support()
    # --------------------------------------------GET PARAMETER INPUTS
    PARSER = argparse.ArgumentParser(description="FreeDATA Modem")

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
        choices=["disabled", "rigctld", "tci"],
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
        default=0,
        help="Set the tx audio level at an early stage",
        type=int,
    )
    PARSER.add_argument(
        "--rx-audio-level",
        dest="rx_audio_level",
        default=0,
        help="Set the rx audio level at an early stage",
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
        help="Enable sending modem data to https://explorer.freedata.app",
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
        "--tci-ip",
        dest="tci_ip",
        default='127.0.0.1',
        type=str,
        help="Set tci destination ip",
    )

    PARSER.add_argument(
        "--tci-port",
        dest="tci_port",
        default=50001,
        type=int,
        help="Set tci destination port",
    )

    PARSER.add_argument(
        "--tx-delay",
        dest="tx_delay",
        default=0,
        help="delay in ms before modulation is pushed to audio device",
        type=int,
    )

    PARSER.add_argument(
        "--mesh",
        dest="enable_mesh",
        action="store_true",
        help="Enable mesh protocol",
    )

    PARSER.add_argument(
        "--hmac",
        dest="enable_hmac",
        action="store_true",
        default=True,
        help="Enable and set hmac message salt",
    )

    PARSER.add_argument(
        "--morse",
        dest="transmit_morse_identifier",
        action="store_true",
        default=False,
        help="Enable and send a morse identifier on disconnect an beacon",
    )


    ARGS = PARSER.parse_args()

    # set save to folder state for allowing downloading files to local file system
    ARQ.arq_save_to_folder = ARGS.savetofolder

    if not ARGS.configfile:
    
    
        # additional step for being sure our callsign is correctly
        # in case we are not getting a station ssid
        # then we are forcing a station ssid = 0
        try:
            mycallsign = bytes(ARGS.mycall.upper(), "utf-8")
            mycallsign = helpers.callsign_to_bytes(mycallsign)
            Station.mycallsign = helpers.bytes_to_callsign(mycallsign)
            Station.mycallsign_crc = helpers.get_crc_24(Station.mycallsign)
            Station.ssid_list = ARGS.ssid_list
            # check if own ssid is always part of ssid list
            own_ssid = int(Station.mycallsign.split(b"-")[1])
            if own_ssid not in Station.ssid_list:
                Station.ssid_list.append(own_ssid)

            Station.mygrid = bytes(ARGS.mygrid, "utf-8")

            # check if we have an int or str as device name
            try:
                AudioParam.audio_input_device = int(ARGS.audio_input_device)
            except ValueError:
                AudioParam.audio_input_device = ARGS.audio_input_device
            try:
                AudioParam.audio_output_device = int(ARGS.audio_output_device)
            except ValueError:
                AudioParam.audio_output_device = ARGS.audio_output_device

            Modem.port = ARGS.socket_port
            HamlibParam.hamlib_radiocontrol = ARGS.hamlib_radiocontrol
            HamlibParam.hamlib_rigctld_ip = ARGS.rigctld_ip
            HamlibParam.hamlib_rigctld_port = str(ARGS.rigctld_port)
            ModemParam.enable_scatter = ARGS.send_scatter
            AudioParam.enable_fft = ARGS.send_fft
            Modem.enable_fsk = ARGS.enable_fsk
            Modem.low_bandwidth_mode = ARGS.low_bandwidth_mode
            ModemParam.tuning_range_fmin = ARGS.tuning_range_fmin
            ModemParam.tuning_range_fmax = ARGS.tuning_range_fmax
            AudioParam.tx_audio_level = ARGS.tx_audio_level
            AudioParam.rx_audio_level = ARGS.rx_audio_level
            Modem.respond_to_cq = ARGS.enable_respond_to_cq
            ARQ.rx_buffer_size = ARGS.rx_buffer_size
            Modem.enable_explorer = ARGS.enable_explorer
            AudioParam.audio_auto_tune = ARGS.enable_audio_auto_tune
            Modem.enable_stats = ARGS.enable_stats
            TCIParam.ip = ARGS.tci_ip
            TCIParam.port = ARGS.tci_port
            ModemParam.tx_delay = ARGS.tx_delay
            MeshParam.enable_protocol = ARGS.enable_mesh
            Modem.enable_hmac = ARGS.enable_hmac
            Modem.transmit_morse_identifier = ARGS.transmit_morse_identifier

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
            Station.mycallsign = helpers.bytes_to_callsign(mycallsign)
            Station.mycallsign_crc = helpers.get_crc_24(Station.mycallsign)

            #json.loads = for converting str list to list
            Station.ssid_list = json.loads(conf.get('STATION', 'ssid_list', '[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]'))

            Station.mygrid = bytes(conf.get('STATION', 'mygrid', 'JN12aa'), "utf-8")
            # check if we have an int or str as device name
            try:
                AudioParam.audio_input_device = int(conf.get('AUDIO', 'rx', '0'))
            except ValueError:
                AudioParam.audio_input_device = conf.get('AUDIO', 'rx', '0')
            try:
                AudioParam.audio_output_device = int(conf.get('AUDIO', 'tx', '0'))
            except ValueError:
                AudioParam.audio_output_device = conf.get('AUDIO', 'tx', '0')

            Modem.port = int(conf.get('NETWORK', 'modemport', '3000'))
            HamlibParam.hamlib_radiocontrol = conf.get('RADIO', 'radiocontrol', 'disabled')
            HamlibParam.hamlib_rigctld_ip = conf.get('RADIO', 'rigctld_ip', '127.0.0.1')
            HamlibParam.hamlib_rigctld_port = str(conf.get('RADIO', 'rigctld_port', '4532'))
            ModemParam.enable_scatter = conf.get('Modem', 'scatter', 'True')
            AudioParam.enable_fft = conf.get('Modem', 'fft', 'True')
            Modem.enable_fsk = conf.get('Modem', 'fsk', 'False')
            Modem.low_bandwidth_mode = conf.get('Modem', 'narrowband', 'False')
            ModemParam.tuning_range_fmin = float(conf.get('Modem', 'fmin', '-50.0'))
            ModemParam.tuning_range_fmax = float(conf.get('Modem', 'fmax', '50.0'))
            AudioParam.tx_audio_level = int(conf.get('AUDIO', 'txaudiolevel', '0'))
            AudioParam.rx_audio_level = int(conf.get('AUDIO', 'rxaudiolevel', '0'))
            Modem.respond_to_cq = conf.get('Modem', 'qrv', 'True')
            ARQ.rx_buffer_size = int(conf.get('Modem', 'rx_buffer_size', '16'))
            Modem.enable_explorer = conf.get('Modem', 'explorer', 'False')
            AudioParam.audio_auto_tune = conf.get('AUDIO', 'auto_tune', 'False')
            Modem.enable_stats = conf.get('Modem', 'stats', 'False')
            TCIParam.ip = str(conf.get('TCI', 'tci_ip', 'localhost'))
            TCIParam.port = int(conf.get('TCI', 'tci_port', '50001'))
            ModemParam.tx_delay = int(conf.get('Modem', 'tx_delay', '0'))
            MeshParam.enable_protocol = conf.get('MESH','mesh_enable','False')
            MeshParam.transmit_morse_identifier = conf.get('Modem','transmit_morse_identifier','False')

        except KeyError as e:
            log.warning("[CFG] Error reading config file near", key=str(e))
        except Exception as e:
            log.warning("[CFG] Error", e=e)

    # make sure the own ssid is always part of the ssid list
    my_ssid = int(Station.mycallsign.split(b'-')[1])
    if my_ssid not in Station.ssid_list:
        Station.ssid_list.append(my_ssid)

    # we need to wait until we got all parameters from argparse first before we can load the other modules
    import sock

    # config logging
    try:
        if sys.platform == "linux":
            logging_path = os.getenv("HOME") + "/.config/" + "FreeDATA/" + "modem"

        if sys.platform == "darwin":
            logging_path = (
                os.getenv("HOME")
                + "/Library/"
                + "Application Support/"
                + "FreeDATA/"
                + "modem"
            )

        if sys.platform in ["win32", "win64"]:
            logging_path = os.getenv("APPDATA") + "/" + "FreeDATA/" + "modem"

        if not os.path.exists(logging_path):
            os.makedirs(logging_path)
        log_handler.setup_logging(logging_path)
    except Exception as err:
        log.error("[DMN] logger init error", exception=err)

    log.info(
        "[Modem] Starting FreeDATA", author="DJ2LS", version=Modem.version
    )

    # start data handler
    data_handler.DATA()

    # start modem
    modem = modem.RF()

    # start mesh protocol only if enabled
    if MeshParam.enable_protocol:
        log.info("[MESH] loading module")
        # start mesh module
        mesh = mesh.MeshRouter()

    # optionally start explorer module
    if Modem.enable_explorer:
        log.info("[EXPLORER] Publishing to https://explorer.freedata.app", state=Modem.enable_explorer)
        explorer = explorer.explorer()

    # --------------------------------------------START CMD SERVER
    try:
        log.info("[Modem] Starting TCP/IP socket", port=Modem.port)
        # https://stackoverflow.com/a/16641793
        socketserver.TCPServer.allow_reuse_address = True
        cmdserver = sock.ThreadedTCPServer(
            (Modem.host, Modem.port), sock.ThreadedTCPRequestHandler
        )
        server_thread = threading.Thread(target=cmdserver.serve_forever)

        server_thread.daemon = True
        server_thread.start()

    except Exception as err:
        log.error("[Modem] Starting TCP/IP socket failed", port=Modem.port, e=err)
        sys.exit(1)
    while True:
        threading.Event().wait(1)