#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:58:45 2020

@author: DJ2LS

"""

import argparse
import threading
import socketserver
import time
import os
import sys
import subprocess
import ujson as json
import psutil
import serial.tools.list_ports
import static
import crcengine
import re
import rig
import logging, structlog, log_handler

log_handler.setup_logging("daemon")
# get python version, which is needed later for determining installation path
python_version = str(sys.version_info[0]) + "." + str(sys.version_info[1])
structlog.get_logger("structlog").info("[DMN] Starting...", python=python_version)


####################################################
# https://stackoverflow.com/questions/7088672/pyaudio-working-but-spits-out-error-messages-each-time
# https://github.com/DJ2LS/FreeDATA/issues/22
# we need to have a look at this if we want to run this on Windows and MacOS !
# Currently it seems, this is a Linux-only problem

from ctypes import *
from contextlib import contextmanager
import pyaudio

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def noalsaerr():
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)
    
# with noalsaerr():
#   p = pyaudio.PyAudio()
######################################################    

# try importing hamlib    
try:
    # installation path for Ubuntu 20.04 LTS python modules
    sys.path.append('/usr/local/lib/python'+ python_version +'/site-packages')
    # installation path for Ubuntu 20.10 +
    sys.path.append('/usr/local/lib/')
    import Hamlib
            
    # https://stackoverflow.com/a/4703409
    hamlib_version = re.findall(r"[-+]?\d*\.?\d+|\d+", Hamlib.cvar.hamlib_version)    
    hamlib_version = float(hamlib_version[0])
            
    min_hamlib_version = 4.1
    if hamlib_version > min_hamlib_version:
        structlog.get_logger("structlog").info("[DMN] Hamlib found", version=hamlib_version)
    else:
        structlog.get_logger("structlog").warning("[DMN] Hamlib outdated", found=hamlib_version, recommend=min_hamlib_version)
except Exception as e:
    structlog.get_logger("structlog").critical("[DMN] Hamlib not found", error=e)

# load crc engine    
crc_algorithm = crcengine.new('crc16-ccitt-false')  # load crc8 library


def start_daemon():

    try:
        structlog.get_logger("structlog").info("[DMN] Starting TCP/IP socket", port=PORT)
        # https://stackoverflow.com/a/16641793
        socketserver.TCPServer.allow_reuse_address = True
        daemon = socketserver.TCPServer(('0.0.0.0', PORT), CMDTCPRequestHandler)
        daemon.serve_forever()

    finally:
        structlog.get_logger("structlog").warning("[DMN] Closing socket", port=PORT)
        daemon.server_close()


class CMDTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        structlog.get_logger("structlog").debug("[DMN] Client connected", ip=self.client_address[0])

        # loop through socket buffer until timeout is reached. then close buffer
        socketTimeout = time.time() + 3
        while socketTimeout > time.time():

            time.sleep(0.01)
            encoding = 'utf-8'
            #data = str(self.request.recv(1024), 'utf-8')

            data = bytes()

            # we need to loop through buffer until end of chunk is reached or timeout occured
            while True and socketTimeout > time.time():
                chunk = self.request.recv(45)
                data += chunk
                # or chunk.endswith(b'\n'):
                if chunk.endswith(b'}\n') or chunk.endswith(b'}'):
                    break
            data = data[:-1]  # remove b'\n'
            data = str(data, 'utf-8')

            if len(data) > 0:
                socketTimeout = time.time() + 3

            # convert data to json object
            # we need to do some error handling in case of socket timeout

            try:
                # only read first line of string. multiple lines will cause an json error
                # this occurs possibly, if we are getting data too fast
                data = data.splitlines()[0]
                received_json = json.loads(data)

            # GET COMMANDS
            # "command" : "..."

            # SET COMMANDS
            # "command" : "..."
            # "parameter" : " ..."

            # DATA COMMANDS
            # "command" : "..."
            # "type" : "..."
            # "dxcallsign" : "..."
            # "data" : "..."

            # print(received_json)
            # print(received_json["type"])
            # print(received_json["command"])
            # try:

                if received_json["type"] == 'SET' and received_json["command"] == 'STARTTNC' and not static.TNCSTARTED:
                    rx_audio = str(received_json["parameter"][0]["rx_audio"])
                    tx_audio = str(received_json["parameter"][0]["tx_audio"])
                    devicename = str(received_json["parameter"][0]["devicename"])
                    deviceport = str(received_json["parameter"][0]["deviceport"])
                    serialspeed = str(received_json["parameter"][0]["serialspeed"])
                    pttprotocol = str(received_json["parameter"][0]["pttprotocol"])
                    pttport = str(received_json["parameter"][0]["pttport"])
                    data_bits = str(received_json["parameter"][0]["data_bits"])
                    stop_bits = str(received_json["parameter"][0]["stop_bits"])
                    handshake = str(received_json["parameter"][0]["handshake"])
                    

                    
                    structlog.get_logger("structlog").warning("[DMN] Starting TNC", rig=devicename, port=deviceport)
                    #print(received_json["parameter"][0])

                    # command = "--rx "+ rx_audio +" \
                    #    --tx "+ tx_audio +" \
                    #    --deviceport "+ deviceport +" \
                    #    --deviceid "+ deviceid + " \
                    #    --serialspeed "+ serialspeed + " \
                    #    --pttprotocol "+ pttprotocol + " \
                    #    --pttport "+ pttport

                    # list of parameters, necessary for running subprocess command as a list
                    options = []
                    options.append('--rx')
                    options.append(rx_audio)
                    options.append('--tx')
                    options.append(tx_audio)
                    options.append('--deviceport')
                    options.append(deviceport)
                    options.append('--devicename')
                    options.append(devicename)
                    options.append('--serialspeed')
                    options.append(serialspeed)
                    options.append('--pttprotocol')
                    options.append(pttprotocol)
                    options.append('--pttport')
                    options.append(pttport)
                    options.append('--data_bits')
                    options.append(data_bits)
                    options.append('--stop_bits')
                    options.append(stop_bits)
                    options.append('--handshake')
                    options.append(handshake)


                    # try running tnc from binary, else run from source
                    # this helps running the tnc in a developer environment
                    try:
                        command = []
                        command.append('./tnc')
                        command += options
                        p = subprocess.Popen(command)
                        structlog.get_logger("structlog").info("[DMN] TNC started", path="binary")
                    except:
                        command = []
                        command.append('python3')
                        command.append('main.py')
                        command += options
                        p = subprocess.Popen(command)
                        structlog.get_logger("structlog").info("[DMN] TNC started", path="source")

                    static.TNCPROCESS = p  # .pid
                    static.TNCSTARTED = True

                if received_json["type"] == 'SET' and received_json["command"] == 'STOPTNC':
                    static.TNCPROCESS.kill()
                    structlog.get_logger("structlog").warning("[DMN] Stopping TNC")
                    #os.kill(static.TNCPROCESS, signal.SIGKILL)
                    static.TNCSTARTED = False

                if received_json["type"] == 'GET' and received_json["command"] == 'DAEMON_STATE':

                    data = {
                        'COMMAND': 'DAEMON_STATE',
                        'DAEMON_STATE': [],
                        'PYTHON_VERSION': str(python_version),
                        'HAMLIB_VERSION': str(hamlib_version),
                        'INPUT_DEVICES': [],
                        'OUTPUT_DEVICES': [],
                        'SERIAL_DEVICES': [
                    ], "CPU": str(psutil.cpu_percent()), "RAM": str(psutil.virtual_memory().percent), "VERSION": "0.1-prototype"}

                    if static.TNCSTARTED:
                        data["DAEMON_STATE"].append({"STATUS": "running"})
                    else:
                        data["DAEMON_STATE"].append({"STATUS": "stopped"})

                        # UPDATE LIST OF AUDIO DEVICES    
                        try:
                        # we need to "try" this, because sometimes libasound.so isn't in the default place                   
                            # try to supress error messages
                            with noalsaerr(): # https://github.com/DJ2LS/FreeDATA/issues/22
                                p = pyaudio.PyAudio()
                        # else do it the default way
                        except:
                            p = pyaudio.Pyaudio()
                                    
                        for i in range(0, p.get_device_count()):

                            maxInputChannels = p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')
                            maxOutputChannels = p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')
                            name = p.get_device_info_by_host_api_device_index(0, i).get('name')
                            crc_name = crc_algorithm(bytes(name, encoding='utf-8'))
                            crc_name = crc_name.to_bytes(2, byteorder='big')
                            crc_name = crc_name.hex()
                            name = name + ' [' + crc_name + ']' 
            
                            if maxInputChannels > 0:
                                data["INPUT_DEVICES"].append(
                                    {"ID": i, "NAME": str(name)})
                            if maxOutputChannels > 0:
                                data["OUTPUT_DEVICES"].append(
                                    {"ID": i, "NAME": str(name)})
                        p.terminate()
                        
                        # UPDATE LIST OF SERIAL DEVICES
                        ports = serial.tools.list_ports.comports()
                        for port, desc, hwid in ports:
                        
                            # calculate hex of hwid if we have unique names
                            crc_hwid = crc_algorithm(bytes(hwid, encoding='utf-8'))
                            crc_hwid = crc_hwid.to_bytes(2, byteorder='big')
                            crc_hwid = crc_hwid.hex()
                            description = desc + ' [' + crc_hwid + ']'
                            
                            data["SERIAL_DEVICES"].append(
                                {"PORT": str(port), "DESCRIPTION": str(description) })

                    
                    jsondata = json.dumps(data)
                    self.request.sendall(bytes(jsondata, encoding))


                if received_json["type"] == 'GET' and received_json["command"] == 'TEST_HAMLIB':

                    try:
                        print(received_json["parameter"])

                        devicename = str(received_json["parameter"][0]["devicename"])
                        deviceport = str(received_json["parameter"][0]["deviceport"])
                        serialspeed = str(received_json["parameter"][0]["serialspeed"])
                        pttprotocol = str(received_json["parameter"][0]["pttprotocol"])
                        pttport = str(received_json["parameter"][0]["pttport"])
                        data_bits = str(received_json["parameter"][0]["data_bits"])
                        stop_bits = str(received_json["parameter"][0]["stop_bits"])
                        handshake = str(received_json["parameter"][0]["handshake"])
                        
                        hamlib = rig.radio()
                        hamlib.open_rig(devicename=devicename, deviceport=deviceport, hamlib_ptt_type=pttprotocol, serialspeed=serialspeed, pttport=pttport, data_bits=data_bits, stop_bits=stop_bits, handshake=handshake)
                        
                        hamlib.set_ptt(True)      
                        pttstate = hamlib.get_ptt()
                        if pttstate:
                            structlog.get_logger("structlog").info("[DMN] Hamlib PTT", status = 'SUCCESS')
                            data = {'COMMAND': 'TEST_HAMLIB', 'RESULT': 'SUCCESS'}
                        elif not pttstate:
                            structlog.get_logger("structlog").warning("[DMN] Hamlib PTT", status = 'NO SUCCESS')
                            data = {'COMMAND': 'TEST_HAMLIB', 'RESULT': 'NOSUCCESS'}
                        else:
                            structlog.get_logger("structlog").error("[DMN] Hamlib PTT", status = 'FAILED')
                            data = {'COMMAND': 'TEST_HAMLIB', 'RESULT': 'FAILED'}
                            
                        hamlib.set_ptt(False)                 
                        hamlib.close_rig()
                            
                        jsondata = json.dumps(data)
                        self.request.sendall(bytes(jsondata, encoding))
                        
                    except Exception as e:
                        print(e)
                        structlog.get_logger("structlog").error("[DMN] Hamlib: Can't open rig", e = sys.exc_info()[0])

            # exception, if JSON cant be decoded
            # except Exception as e:
            except ValueError as e:
                print("############ START OF ERROR #####################")
                print('DAEMON PROGRAM ERROR: %s' % str(e))
                print("Wrong command")
                print(data)
                print(e)
                exc_type, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                print("############ END OF ERROR #######################")

            # exception for any other errors
            # in case of index error for example which is caused by a hard network interruption
            except:
                structlog.get_logger("structlog").error("[DMN] Network error", e = sys.exc_info()[0])
        structlog.get_logger("structlog").warning("[DMN] Closing client socket")                
        

if __name__ == '__main__':

    # --------------------------------------------GET PARAMETER INPUTS
    PARSER = argparse.ArgumentParser(description='Simons TEST TNC')
    PARSER.add_argument('--port', dest="socket_port",default=3001, help="Socket port", type=int)

    ARGS = PARSER.parse_args()
    PORT = ARGS.socket_port

    # --------------------------------------------START CMD SERVER

    DAEMON_THREAD = threading.Thread(target=start_daemon, name="daemon")
    DAEMON_THREAD.start()
