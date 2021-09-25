#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:58:45 2020

@author: DJ2LS

"""


import argparse
import threading
import socketserver
import pyaudio
import time
import ujson as json
import subprocess
import os
import static
import psutil
import sys
import serial.tools.list_ports

def start_daemon():

    try:
        print("SRV | STARTING TCP/IP SOCKET FOR CMD ON PORT: " + str(PORT))
        socketserver.TCPServer.allow_reuse_address = True  # https://stackoverflow.com/a/16641793
        daemon = socketserver.TCPServer(('0.0.0.0', PORT), CMDTCPRequestHandler)
        daemon.serve_forever()

    finally:
        daemon.server_close()
        
        
class CMDTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        print("Client connected...")    
        
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
                if chunk.endswith(b'}\n') or chunk.endswith(b'}'): # or chunk.endswith(b'\n'):
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
            #print(received_json["type"])
            #print(received_json["command"]) 
            #try:

                if received_json["type"] == 'SET' and received_json["command"] == 'STARTTNC' and not static.TNCSTARTED:
                    rx_audio = str(received_json["parameter"][0]["rx_audio"])
                    tx_audio = str(received_json["parameter"][0]["tx_audio"])
                    deviceid = str(received_json["parameter"][0]["deviceid"])
                    deviceport = str(received_json["parameter"][0]["deviceport"])
                    serialspeed = str(received_json["parameter"][0]["serialspeed"])
                    pttprotocol = str(received_json["parameter"][0]["pttprotocol"])
                    pttport = str(received_json["parameter"][0]["pttport"])
                    print("---- STARTING TNC !")
                    print(received_json["parameter"][0])

                    #command = "--rx "+ rx_audio +" \
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
                    options.append('--deviceid')
                    options.append(deviceid)
                    options.append('--serialspeed')
                    options.append(serialspeed)
                    options.append('--pttprotocol')
                    options.append(pttprotocol)
                    options.append('--pttport')
                    options.append(pttport)
                    
                    # try running tnc from binary, else run from source
                    # this helps running the tnc in a developer environment
                    try:
                        # subprocess.check_call("exec ./tnc " + command)
                        subprocess.check_call("exec ./tnc ")
                        command = []
                        command.append('tnc')
                        command += options
                        p = subprocess.Popen(command)
                        print("running TNC from binary...")
                    except:
                        command = []
                        command.append('python3')
                        command.append('main.py')
                        command += options
                        p = subprocess.Popen(command)
                        print("running TNC from source...")
                                               
                    static.TNCPROCESS = p#.pid
                    static.TNCSTARTED = True

                if received_json["type"] == 'SET' and received_json["command"] == 'STOPTNC':
                    parameter = received_json["parameter"]
                    static.TNCPROCESS.kill()
                    print("KILLING PROCESS ------------")
                    #os.kill(static.TNCPROCESS, signal.SIGKILL)
                    static.TNCSTARTED = False
                    
                if received_json["type"] == 'GET' and received_json["command"] == 'DAEMON_STATE':

                    data = {'COMMAND' : 'DAEMON_STATE', 'DAEMON_STATE' : [], 'INPUT_DEVICES': [], 'OUTPUT_DEVICES': [], 'SERIAL_DEVICES': [], "CPU": str(psutil.cpu_percent()),"RAM": str(psutil.virtual_memory().percent), "VERSION": "0.1-prototype"}

                    if static.TNCSTARTED:
                        data["DAEMON_STATE"].append({"STATUS": "running"})
                    else:
                        data["DAEMON_STATE"].append({"STATUS": "stopped"})

                    # UPDATE LIST OF AUDIO DEVICES
                    p = pyaudio.PyAudio()
                    for i in range(0, p.get_device_count()):
                        
                        maxInputChannels = p.get_device_info_by_host_api_device_index(0,i).get('maxInputChannels')
                        maxOutputChannels = p.get_device_info_by_host_api_device_index(0,i).get('maxOutputChannels')
                        name = p.get_device_info_by_host_api_device_index(0,i).get('name')  
                        
                        if maxInputChannels > 0:                        
                            data["INPUT_DEVICES"].append({"ID": i, "NAME" : str(name)})  
                        if maxOutputChannels > 0:                        
                            data["OUTPUT_DEVICES"].append({"ID": i, "NAME" : str(name)})  
                          
                    # UPDATE LIST OF SERIAL DEVICES
                    ports = serial.tools.list_ports.comports()
                    for port, desc, hwid in ports:
                        data["SERIAL_DEVICES"].append({"PORT": str(port), "DESCRIPTION" : str(desc)}) 

                    #print(data)
                    jsondata = json.dumps(data)
                    self.request.sendall(bytes(jsondata, encoding))
                
              
            
            #exception, if JSON cant be decoded
            #except Exception as e:
            except ValueError as e:
                print("############ START OF ERROR #####################")
                print('DAEMON PROGRAM ERROR: %s' %str(e))
                print("Wrong command")
                print(data)
                print(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                print("############ END OF ERROR #######################")

        print("Client disconnected...")


if __name__ == '__main__':


    # --------------------------------------------GET PARAMETER INPUTS
    PARSER = argparse.ArgumentParser(description='Simons TEST TNC')
    PARSER.add_argument('--port', dest="socket_port", default=3001, help="Socket port", type=int)

    
    
    ARGS = PARSER.parse_args()
    PORT = ARGS.socket_port

    # --------------------------------------------START CMD SERVER

    DAEMON_THREAD = threading.Thread(target=start_daemon, name="daemon")
    DAEMON_THREAD.start()
    
    
    
    
    

