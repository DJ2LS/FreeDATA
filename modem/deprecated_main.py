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

import multiprocessing
import os
import signal
import socketserver
import sys
import threading
import argparse
import config
import data_handler
import helpers
import log_handler
import modem
from global_instances import ARQ, AudioParam, Beacon, Channel, Daemon, HamlibParam, ModemParam, Station, Statistics, TCIParam, Modem, MeshParam
import structlog
import explorer
import json
import mesh
from os.path import exists

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
    deprecated_sock.CLOSE_SIGNAL = True
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

# This is for Windows multiprocessing support
multiprocessing.freeze_support()

parser = argparse.ArgumentParser()
parser.add_argument("--use-config", 
                    help = "Specify a config file", 
                    default = 'config.ini')
args = parser.parse_args()

# init config
config_file = args.use_config
if not exists(config_file):
    print("Config file %s not found. Exiting." % config_file)
    exit(1)

conf = config.CONFIG(config_file)

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

    # init config
    conf = config.CONFIG(config_file)
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

    Station.mygrid = bytes(conf.get('STATION', 'mygrid', 'JN12aa'), "utf-8")
    # check if we have an int or str as device name

    # we need to wait until we got all parameters from argparse first before we can load the other modules
    import deprecated_sock

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
    AudioParam.tx_audio_level = int(conf.get('AUDIO', 'txaudiolevel', '100'))
    Modem.respond_to_cq = conf.get('Modem', 'qrv', 'True')
    ARQ.rx_buffer_size = int(conf.get('Modem', 'rx_buffer_size', '16'))
    ARQ.arq_save_to_folder = conf.get('Modem', 'save_to_folder', 'False')
    Modem.enable_explorer = conf.get('Modem', 'explorer', 'False')
    AudioParam.audio_auto_tune = conf.get('AUDIO', 'auto_tune', 'False')
    Modem.enable_stats = conf.get('Modem', 'stats', 'False')
    TCIParam.ip = str(conf.get('TCI', 'tci_ip', 'localhost'))
    TCIParam.port = int(conf.get('TCI', 'tci_port', '50001'))
    ModemParam.tx_delay = int(conf.get('Modem', 'tx_delay', '0'))
    MeshParam.enable_protocol = conf.get('MESH','mesh_enable','False')
except KeyError as e:
    log.warning("[CFG] Error reading config file near", key=str(e))
except Exception as e:
    log.warning("[CFG] Error", e=e)

# make sure the own ssid is always part of the ssid list
my_ssid = int(Station.mycallsign.split(b'-')[1])
if my_ssid not in Station.ssid_list:
    Station.ssid_list.append(my_ssid)

# we need to wait until we got all parameters from argparse first before we can load the other modules
import deprecated_sock

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
data_handler.DATA(conf.config)

# start modem
modem = modem.RF(conf.config)

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

server_thread.join()
