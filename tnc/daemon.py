#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
daemon.py

Author: DJ2LS, January 2022

"""

import argparse
import threading
import socketserver
import time
import sys
import subprocess
import ujson as json
import psutil
import serial.tools.list_ports
import static
import crcengine
import re
import structlog
import log_handler
import helpers
import os

log_handler.setup_logging("daemon")
structlog.get_logger("structlog").info("[DMN] Starting FreeDATA daemon", author="DJ2LS", year="2022", version="0.1")

# get python version, which is needed later for determining installation path
python_version = str(sys.version_info[0]) + "." + str(sys.version_info[1])
structlog.get_logger("structlog").info("[DMN] Python", version=python_version)


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

    def handle(self, hamlib_version = 0):
        structlog.get_logger("structlog").debug("[DMN] Client connected", ip=self.client_address[0])

        # loop through socket buffer until timeout is reached. then close buffer
        socketTimeout = time.time() + 6
        while socketTimeout > time.time():

            time.sleep(0.01)
            encoding = 'utf-8'
            #data = str(self.request.recv(1024), 'utf-8')

            data = bytes()

            # we need to loop through buffer until end of chunk is reached or timeout occured
            while socketTimeout > time.time():
                data += self.request.recv(64)
                # or chunk.endswith(b'\n'):
                if data.startswith(b'{"type"') and data.endswith(b'}\n'):
                    break
            data = data[:-1]  # remove b'\n'
            data = str(data, encoding)

            if len(data) > 0:
                # reset socket timeout
                socketTimeout = time.time() + static.SOCKET_TIMEOUT
                # only read first line of string. multiple lines will cause an json error
                # this occurs possibly, if we are getting data too fast
                #    data = data.splitlines()[0]
                data = data.splitlines()[0]


            # we need to do some error handling in case of socket timeout or decoding issue
            try:

                # convert data to json object
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
            
                if received_json["type"] == 'SET' and received_json["command"] == 'MYCALLSIGN':
                    callsign = received_json["parameter"]
                    print(received_json)
                    if bytes(callsign, 'utf-8') == b'':
                        self.request.sendall(b'INVALID CALLSIGN')
                        structlog.get_logger("structlog").warning("[DMN] SET MYCALL FAILED", call=static.MYCALLSIGN, crc=static.MYCALLSIGN_CRC8)
                    else:
                        static.MYCALLSIGN = bytes(callsign, 'utf-8')
                        static.MYCALLSIGN_CRC8 = helpers.get_crc_8(static.MYCALLSIGN)
  
                        structlog.get_logger("structlog").info("[DMN] SET MYCALL", call=static.MYCALLSIGN, crc=static.MYCALLSIGN_CRC8)
                
                if received_json["type"] == 'SET' and received_json["command"] == 'MYGRID':
                    mygrid = received_json["parameter"]

                    if bytes(mygrid, 'utf-8') == b'':
                        self.request.sendall(b'INVALID GRID')
                    else:
                        static.MYGRID = bytes(mygrid, 'utf-8')
                        structlog.get_logger("structlog").info("[DMN] SET MYGRID", grid=static.MYGRID)
            

                if received_json["type"] == 'SET' and received_json["command"] == 'STARTTNC' and not static.TNCSTARTED:
                    mycall = str(received_json["parameter"][0]["mycall"])
                    mygrid = str(received_json["parameter"][0]["mygrid"])
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
                    radiocontrol = str(received_json["parameter"][0]["radiocontrol"])
                    rigctld_ip = str(received_json["parameter"][0]["rigctld_ip"])
                    rigctld_port = str(received_json["parameter"][0]["rigctld_port"])
                    
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
                    options.append('--mycall')
                    options.append(mycall)
                    options.append('--mygrid')
                    options.append(mygrid)     
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
                    options.append('--radiocontrol')
                    options.append(radiocontrol)
                    options.append('--rigctld_ip')
                    options.append(rigctld_ip)
                    options.append('--rigctld_port')
                    options.append(rigctld_port)



                    # try running tnc from binary, else run from source
                    # this helps running the tnc in a developer environment
                    try:
                        command = []
                        if sys.platform == 'linux' or sys.platform == 'darwin':
                            command.append('./tnc')
                        elif sys.platform == 'win32' or sys.platform == 'win64':
                            command.append('tnc.exe')
                               
                        command += options
                        p = subprocess.Popen(command)
                        structlog.get_logger("structlog").info("[DMN] TNC started", path="binary")
                    except:
                        command = []
                        if sys.platform == 'linux' or sys.platform == 'darwin':
                            command.append('python3')
                        elif sys.platform == 'win32' or sys.platform == 'win64':
                            command.append('python')
                            
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
                        except Exception as e:
                            p = pyaudio.PyAudio()
                                    
                        for i in range(0, p.get_device_count()):
                            # we need to do a try exception, beacuse for windows theres now audio device range
                            try:
                                maxInputChannels = p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')
                                maxOutputChannels = p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')
                                name = p.get_device_info_by_host_api_device_index(0, i).get('name')
                            except:
                                maxInputChannels = 0
                                maxOutputChannels = 0
                                name = ''
                            #crc_name = crc_algorithm(bytes(name, encoding='utf-8'))
                            #crc_name = crc_name.to_bytes(2, byteorder='big')
                            #crc_name = crc_name.hex()
                            #name = name + ' [' + crc_name + ']' 
            
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
                        radiocontrol = str(received_json["parameter"][0]["radiocontrol"])
                        rigctld_ip = str(received_json["parameter"][0]["rigctld_ip"])
                        rigctld_port = str(received_json["parameter"][0]["rigctld_port"])

                        
                        # check how we want to control the radio
                        if radiocontrol == 'direct':
                            import rig
                        elif radiocontrol == 'rigctl':
                            import rigctl as rig
                        elif radiocontrol == 'rigctld':
                            import rigctld as rig
                        else:
                            raise NotImplementedError 
                                
                        hamlib = rig.radio()
                        hamlib.open_rig(devicename=devicename, deviceport=deviceport, hamlib_ptt_type=pttprotocol, serialspeed=serialspeed, pttport=pttport, data_bits=data_bits, stop_bits=stop_bits, handshake=handshake, rigctld_ip=rigctld_ip, rigctld_port = rigctld_port)

                        hamlib_version = rig.hamlib_version
                        
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
                        structlog.get_logger("structlog").error("[DMN] Hamlib: Can't open rig", e = sys.exc_info()[0], error=e)

            except Exception as e:
                structlog.get_logger("structlog").error("[DMN] Network error", error=e)
        structlog.get_logger("structlog").warning("[DMN] Closing client socket", ip=self.client_address[0], port=self.client_address[1]) 


if __name__ == '__main__':

    # --------------------------------------------GET PARAMETER INPUTS
    PARSER = argparse.ArgumentParser(description='Simons TEST TNC')
    PARSER.add_argument('--port', dest="socket_port",default=3001, help="Socket port", type=int)
    
    ARGS = PARSER.parse_args()
    PORT = ARGS.socket_port
    
    # --------------------------------------------START CMD SERVER

    DAEMON_THREAD = threading.Thread(target=start_daemon, name="daemon")
    DAEMON_THREAD.start()
