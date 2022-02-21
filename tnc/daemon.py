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
import queue
import audio
import sock
import atexit
import signal
import multiprocessing

# signal handler for closing aplication
def signal_handler(sig, frame):
    print('Closing daemon...')
    sock.CLOSE_SIGNAL = True
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)



class DAEMON():
    def __init__(self):
        
        # load crc engine    
        self.crc_algorithm = crcengine.new('crc16-ccitt-false')  # load crc8 library
        
        self.daemon_queue = sock.DAEMON_QUEUE
        update_audio_devices = threading.Thread(target=self.update_audio_devices, name="UPDATE_AUDIO_DEVICES", daemon=True)
        update_audio_devices.start()

        update_serial_devices = threading.Thread(target=self.update_serial_devices, name="UPDATE_SERIAL_DEVICES", daemon=True)
        update_serial_devices.start()

        worker = threading.Thread(target=self.worker, name="WORKER", daemon=True)
        worker.start()
        
        
        
    def update_audio_devices(self):
        while 1:
            try:
                if not static.TNCSTARTED:
                    
                    static.AUDIO_INPUT_DEVICES, static.AUDIO_OUTPUT_DEVICES = audio.get_audio_devices()
            except Exception as e:
                print(e)
            time.sleep(1)
            
            
    def update_serial_devices(self):
        while 1:
            try:
                #print("update serial")
                serial_devices = []
                ports = serial.tools.list_ports.comports()
                for port, desc, hwid in ports:
                
                    # calculate hex of hwid if we have unique names
                    crc_hwid = self.crc_algorithm(bytes(hwid, encoding='utf-8'))
                    crc_hwid = crc_hwid.to_bytes(2, byteorder='big')
                    crc_hwid = crc_hwid.hex()
                    description = desc + ' [' + crc_hwid + ']'
                    serial_devices.append({"port": str(port), "description": str(description) })
                
                static.SERIAL_DEVICES = serial_devices
                time.sleep(1)
            except Exception as e:
                print(e)
                
    def worker(self):
        while 1:
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
                # data[18] low_bandwith_mode
                
                if data[0] == 'STARTTNC':
                    structlog.get_logger("structlog").warning("[DMN] Starting TNC", rig=data[5], port=data[6])

                    # list of parameters, necessary for running subprocess command as a list
                    options = []
                    
                    options.append('--port')
                    options.append(str(static.DAEMONPORT - 1))
                    
                    options.append('--mycall')
                    options.append(data[1])
                    
                    options.append('--mygrid')
                    options.append(data[2])
                    
                    options.append('--rx')
                    options.append(data[3])
                    
                    options.append('--tx')
                    options.append(data[4])
                    
                    options.append('--devicename')
                    options.append(data[5])
                    
                    options.append('--deviceport')
                    options.append(data[6])
                    
                    options.append('--serialspeed')
                    options.append(data[7])
                    
                    options.append('--pttprotocol')
                    options.append(data[8])
                    
                    options.append('--pttport')
                    options.append(data[9])
                    
                    options.append('--data_bits')
                    options.append(data[10])
                    
                    options.append('--stop_bits')
                    options.append(data[11])
                    
                    options.append('--handshake')
                    options.append(data[12])
                    
                    options.append('--radiocontrol')
                    options.append(data[13])
                    
                    options.append('--rigctld_ip')
                    options.append(data[14])
                    
                    options.append('--rigctld_port')
                    options.append(data[15])
                    
                    if data[16] == 'True':
                        options.append('--scatter')
                        
                    if data[17] == 'True':
                        options.append('--fft')

                    if data[18] == 'True':
                        options.append('--500hz')

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
                        
                        atexit.register(p.kill)

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
                        atexit.register(p.kill)

                        structlog.get_logger("structlog").info("[DMN] TNC started", path="source")

                    static.TNCPROCESS = p  # .pid
                    static.TNCSTARTED = True
                '''
                # WE HAVE THIS PART in SOCKET
                if data[0] == 'STOPTNC':
                        static.TNCPROCESS.kill()
                        structlog.get_logger("structlog").warning("[DMN] Stopping TNC")
                        #os.kill(static.TNCPROCESS, signal.SIGKILL)
                        static.TNCSTARTED = False
                '''        
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
                if data[0] == 'TEST_HAMLIB':

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
                    if radiocontrol == 'direct':
                        import rig
                    elif radiocontrol == 'rigctl':
                        import rigctl as rig
                    elif radiocontrol == 'rigctld':
                        import rigctld as rig
                    else:
                        import rigdummy as rig
                            
                    hamlib = rig.radio()
                    hamlib.open_rig(devicename=devicename, deviceport=deviceport, hamlib_ptt_type=pttprotocol, serialspeed=serialspeed, pttport=pttport, data_bits=data_bits, stop_bits=stop_bits, handshake=handshake, rigctld_ip=rigctld_ip, rigctld_port = rigctld_port)

                    hamlib_version = rig.hamlib_version

                    hamlib.set_ptt(True)      
                    pttstate = hamlib.get_ptt()
                    
                    if pttstate:
                        structlog.get_logger("structlog").info("[DMN] Hamlib PTT", status = 'SUCCESS')
                        response = {'command': 'test_hamlib', 'result': 'SUCCESS'}
                    elif not pttstate:
                        structlog.get_logger("structlog").warning("[DMN] Hamlib PTT", status = 'NO SUCCESS')
                        response = {'command': 'test_hamlib', 'result': 'NOSUCCESS'}
                    else:
                        structlog.get_logger("structlog").error("[DMN] Hamlib PTT", status = 'FAILED')
                        response = {'command': 'test_hamlib', 'result': 'FAILED'}
                        
                    hamlib.set_ptt(False)                 
                    hamlib.close_rig()
                        
                    jsondata = json.dumps(response)
                    sock.SOCKET_QUEUE.put(jsondata)
                    
            except Exception as e:
                print(e)



if __name__ == '__main__':
    # we need to run this on windows for multiprocessing support
    multiprocessing.freeze_support()


    # --------------------------------------------GET PARAMETER INPUTS
    PARSER = argparse.ArgumentParser(description='FreeDATA Daemon')
    PARSER.add_argument('--port', dest="socket_port",default=3001, help="Socket port", type=int)   
    ARGS = PARSER.parse_args()
    static.DAEMONPORT = ARGS.socket_port
    
    if sys.platform == 'linux':
        logging_path = os.getenv("HOME") + '/.config/' + 'FreeDATA/' + 'daemon'
        
    if sys.platform == 'darwin':
        logging_path = os.getenv("HOME") + '/.config/' + 'FreeDATA/' + 'daemon' 
           
    if sys.platform == 'win32' || sys.platform == 'win64':
        logging_path = os.getenv('APPDATA') + '/' + 'FreeDATA/' + 'daemon'  
          
    log_handler.setup_logging(logging_path)



    try:
        structlog.get_logger("structlog").info("[DMN] Starting TCP/IP socket", port=static.DAEMONPORT)
        # https://stackoverflow.com/a/16641793
        socketserver.TCPServer.allow_reuse_address = True
        cmdserver = sock.ThreadedTCPServer((static.HOST, static.DAEMONPORT), sock.ThreadedTCPRequestHandler)
        server_thread = threading.Thread(target=cmdserver.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    except Exception as e:
        structlog.get_logger("structlog").error("[DMN] Starting TCP/IP socket failed", port=static.DAEMONPORT, e=e)
        os._exit(1)
    daemon = DAEMON()

    
    while True:
        time.sleep(1)
