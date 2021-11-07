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
import pyaudio
import static
import crcengine

# sys.path.append("hamlib/linux")
try:
    import Hamlib
    print("running Hamlib {0} from Sys Path".format(Hamlib.cvar.hamlib_version))

except ImportError:
    from hamlib.linux import Hamlib
    print("running Hamlib {0} from precompiled bundle".format(Hamlib.cvar.hamlib_version)))

else:
    # place for rigctld
    pass
    
    
    
crc_algorithm = crcengine.new('crc16-ccitt-false')  # load crc8 library


def start_daemon():

    try:
        print("SRV | STARTING TCP/IP SOCKET FOR CMD ON PORT: " + str(PORT))
        # https://stackoverflow.com/a/16641793
        socketserver.TCPServer.allow_reuse_address = True
        daemon = socketserver.TCPServer(
            ('0.0.0.0', PORT), CMDTCPRequestHandler)
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
                    deviceid = str(received_json["parameter"][0]["deviceid"])
                    deviceport = str(received_json["parameter"][0]["deviceport"])
                    serialspeed = str(received_json["parameter"][0]["serialspeed"])
                    pttprotocol = str(received_json["parameter"][0]["pttprotocol"])
                    pttport = str(received_json["parameter"][0]["pttport"])
                    print("---- STARTING TNC !")
                    print(received_json["parameter"][0])

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
                        command = []
                        command.append('./tnc')
                        command += options
                        p = subprocess.Popen(command)
                        print("running TNC from binary...")
                    except Exception as e:
                        print(e)
                        command = []
                        command.append('python3')
                        command.append('main.py')
                        command += options
                        p = subprocess.Popen(command)
                        print("running TNC from source...")

                    static.TNCPROCESS = p  # .pid
                    static.TNCSTARTED = True

                if received_json["type"] == 'SET' and received_json["command"] == 'STOPTNC':
                    static.TNCPROCESS.kill()
                    print("KILLING PROCESS ------------")
                    #os.kill(static.TNCPROCESS, signal.SIGKILL)
                    static.TNCSTARTED = False

                if received_json["type"] == 'GET' and received_json["command"] == 'DAEMON_STATE':

                    data = {'COMMAND': 'DAEMON_STATE', 'DAEMON_STATE': [], 'INPUT_DEVICES': [], 'OUTPUT_DEVICES': [], 'SERIAL_DEVICES': [
                    ], "CPU": str(psutil.cpu_percent()), "RAM": str(psutil.virtual_memory().percent), "VERSION": "0.1-prototype"}

                    if static.TNCSTARTED:
                        data["DAEMON_STATE"].append({"STATUS": "running"})
                    else:
                        data["DAEMON_STATE"].append({"STATUS": "stopped"})

                        # UPDATE LIST OF AUDIO DEVICES
                        p = pyaudio.PyAudio()
                        for i in range(0, p.get_device_count()):

                            maxInputChannels = p.get_device_info_by_host_api_device_index(
                                0, i).get('maxInputChannels')
                            maxOutputChannels = p.get_device_info_by_host_api_device_index(
                                0, i).get('maxOutputChannels')
                            name = p.get_device_info_by_host_api_device_index(
                                0, i).get('name')

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

                    print(received_json["parameter"])

                    deviceid = str(received_json["parameter"][0]["deviceid"])
                    deviceport = str(received_json["parameter"][0]["deviceport"])
                    serialspeed = str(received_json["parameter"][0]["serialspeed"])
                    pttprotocol = str(received_json["parameter"][0]["pttprotocol"])
                    pttport = str(received_json["parameter"][0]["pttport"])

                    pttspeed = str(received_json["parameter"][0]["pttspeed"])
                    data_bits = str(received_json["parameter"][0]["data_bits"])
                    stop_bits = str(received_json["parameter"][0]["stop_bits"])
                    handshake = str(received_json["parameter"][0]["handshake"])
                  
                    
                    print(deviceid)
                    print(deviceport)
                    print(serialspeed)
                    print(pttprotocol)
                    print(pttport)
                    print(pttspeed)
                    print(data_bits)
                    print(stop_bits)
                    print(handshake)
                    
                    # try to init hamlib
                    try:
                        Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)
                        my_rig = Hamlib.Rig(int(deviceid))
                        my_rig.set_conf("rig_pathname", deviceport)
                        my_rig.set_conf("retry", "1")
                        my_rig.set_conf("serial_speed", serialspeed)
                        my_rig.set_conf("serial_handshake", handshake)
                        my_rig.set_conf("stop_bits", stop_bits)
                        my_rig.set_conf("data_bits", data_bits)
                        
                        if pttprotocol == 'RIG':
                            hamlib_ptt_type = Hamlib.RIG_PTT_RIG

                        elif pttprotocol == 'DTR-H':
                            hamlib_ptt_type = Hamlib.RIG_PTT_SERIAL_DTR
                            my_rig.set_conf("dtr_state", "HIGH")
                            my_rig.set_conf("ptt_type", "DTR")

                        elif pttprotocol == 'DTR-L':
                            hamlib_ptt_type = Hamlib.RIG_PTT_SERIAL_DTR
                            my_rig.set_conf("dtr_state", "LOW")
                            my_rig.set_conf("ptt_type", "DTR")

                        elif pttprotocol == 'RTS':
                            hamlib_ptt_type = Hamlib.RIG_PTT_SERIAL_RTS
                            my_rig.set_conf("dtr_state", "OFF")
                            my_rig.set_conf("ptt_type", "RTS")

                        elif pttprotocol == 'PARALLEL':
                            hamlib_ptt_type = Hamlib.RIG_PTT_PARALLEL

                        elif pttprotocol == 'MICDATA':
                            hamlib_ptt_type = Hamlib.RIG_PTT_RIG_MICDATA

                        elif pttprotocol == 'CM108':
                            hamlib_ptt_type = Hamlib.RIG_PTT_CM108

                        else:  # static.HAMLIB_PTT_TYPE == 'RIG_PTT_NONE':
                            hamlib_ptt_type = Hamlib.RIG_PTT_NONE
                        
                      
                        my_rig.open()

                        my_rig.set_ptt(hamlib_ptt_type, 1)
                        pttstate = my_rig.get_ptt()
                        if pttstate == 1:
                            print("PTT SUCCESS")
                            data = {'COMMAND': 'TEST_HAMLIB', 'RESULT': 'SUCCESS'}
                        elif pttstate == 0:
                            print("PTT NO SUCCESS")
                            data = {'COMMAND': 'TEST_HAMLIB', 'RESULT': 'NOSUCCESS'}
                        else:
                            print("HAMLIB FAILED")
                            data = {'COMMAND': 'TEST_HAMLIB', 'RESULT': 'FAILED'}
                        
                        my_rig.set_ptt(hamlib_ptt_type, 0)                        
                        my_rig.close
                        
                        jsondata = json.dumps(data)
                        self.request.sendall(bytes(jsondata, encoding))
                        
                    except:
                        print("Unexpected error:", sys.exc_info()[0])
                        print("can't open rig")
                        #sys.exit("hamlib error")





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

        print("Client disconnected...")


if __name__ == '__main__':

    # --------------------------------------------GET PARAMETER INPUTS
    PARSER = argparse.ArgumentParser(description='Simons TEST TNC')
    PARSER.add_argument('--port', dest="socket_port",
                        default=3001, help="Socket port", type=int)

    ARGS = PARSER.parse_args()
    PORT = ARGS.socket_port

    # --------------------------------------------START CMD SERVER

    DAEMON_THREAD = threading.Thread(target=start_daemon, name="daemon")
    DAEMON_THREAD.start()
