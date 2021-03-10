import socket
import random
import threading
import time
import json


import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk, GObject

def create_string(length):
    random_string = ''
    for _ in range(length):
    # Considering only upper and lowercase letters
        random_integer = random.randint(97, 97 + 26 - 1)
        flip_bit = random.randint(0, 1)
    # Convert to lowercase if the flip bit is on
        random_integer = random_integer - 32 if flip_bit == 1 else random_integer
    # Keep appending random characters using chr(x)
        random_string += (chr(random_integer))
    #print("STR:" + str(random_string))
    
    return random_string
    
    
def send_command(command):
    while True:
        ip, port = builder.get_object('host').get_text(), int(builder.get_object('port').get_text())
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip, port))
                if isinstance(command, str):
                    command = bytes(command, 'utf-8')

                sock.sendall(command + b'\n')
                print("done.....")
                break
            #response = str(sock.recv(1024), 'utf-8')
            #sock.close()
        except:
            pass    
            
         
def get_tnc_state():
    print("starten wir mal....")
    GLib.idle_add(get_tnc_state_worker) 
    #GObject.timeout_add(1000, pulse)   
      
def get_tnc_state_worker():
    
    #while True:
        
        time.sleep(0.05)      
        ip, port = builder.get_object('host').get_text(), int(builder.get_object('port').get_text()) 
        command = bytes('GET:TNC_STATE', 'utf-8')
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip, port))
                sock.sendall(command + b'\n')
                received = str(sock.recv(1024), "utf-8")
                received_json = json.loads(received)
                
                #print(received_json)
                
                builder.get_object('ptt_state').set_text(received_json["PTT_STATE"])
                builder.get_object('channel_state').set_text(received_json["CHANNEL_STATE"])
                builder.get_object('tnc_state').set_text(received_json["TNC_STATE"])
                builder.get_object('arq_state').set_text(received_json["ARQ_STATE"])

                #builder.get_object('levelbar').set_min_value(0.0)
                #builder.get_object('levelbar').set_max_value(10000.0)
                builder.get_object('levelbar').set_value(int(received_json["AUDIO_RMS"]))

                sock.close()            
        except:
            pass   
        #GObject.timeout_add(200, get_tnc_state_worker)
        GLib.timeout_add(200, get_tnc_state_worker) 
def get_data_state():
    GLib.idle_add(get_data_state_worker)


def get_data_state_worker():
    #while True:
        
        ip, port = builder.get_object('host').get_text(), int(builder.get_object('port').get_text()) 
        command = bytes('GET:DATA_STATE', 'utf-8')
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip, port))
                sock.sendall(command + b'\n')
                received = str(sock.recv(1024), "utf-8")
                received_json = json.loads(received)
                #print(received_json)
                #builder.get_object('progressbar_tx').set_fraction(0.2)
                #builder.get_object('progressbar_rx').set_fraction(0.2)
                


                print(received_json["ARQ_TX_N_CURRENT_ARQ_FRAME"])
                print(received_json["ARQ_TX_N_TOTAL_ARQ_FRAMES"])
                print(received_json["ARQ_N_ARQ_FRAMES_PER_DATA_FRAME"])
                print(received_json["ARQ_RX_N_CURRENT_ARQ_FRAME"])
                print("-------")
                if int(received_json["ARQ_TX_N_TOTAL_ARQ_FRAMES"]) > 0:
                    percentage_tx = int(received_json["ARQ_TX_N_CURRENT_ARQ_FRAME"]) / int(received_json["ARQ_TX_N_TOTAL_ARQ_FRAMES"])
                    print(percentage_tx)
                else:
                    #print("0")
                    percentage_tx = 0.0
                print(percentage_tx)
                builder.get_object('progressbar_tx').set_fraction(percentage_tx)
                
                
                if int(received_json["ARQ_N_ARQ_FRAMES_PER_DATA_FRAME"]) > 0:
                    percentage_rx = int(received_json["ARQ_RX_N_CURRENT_ARQ_FRAME"]) / int(received_json["ARQ_N_ARQ_FRAMES_PER_DATA_FRAME"])
                    #print(percentage_rx)
                else:
                    #print("0")
                    percentage_rx = 0.0
                #print(percentage_rx)
                builder.get_object('progressbar_rx').set_fraction(percentage_rx)
                
                
                
                
                 
                #builder.get_object('progressbar').set_text('123')    
                #builder.get_object('progressbar').set_show_text('456')                
                
                sock.close()            
        except:
            pass
#        GObject.timeout_add(200, get_data_state_worker)         
        GLib.timeout_add(200, get_data_state_worker)                     
class Handler:
    def onDestroy(self, *args):
        Gtk.main_quit()

    def setCallsign(self, button):
        call = builder.get_object('callsign').get_text()
        send_command('SET:MYCALLSIGN:' + call)

    def ping(self, button):
        call = builder.get_object('dxcall').get_text()
        send_command('PING:' + call)
        
    def connect(self, button):
        call = builder.get_object('dxcall').get_text()
        send_command('ARQ:CONNECT:' + call)
        
    def disconnect(self, button):
        send_command('ARQ:DISCONNECT')

    def send_arq_data_100(self, button):
        data = create_string(100)
        data = bytes("ARQ:DATA:" + data, 'utf-8')
        send_command(data)

    def send_arq_data_200(self, button):
        data = create_string(200)
        data = bytes("ARQ:DATA:" + data, 'utf-8')
        send_command(data)

    def send_arq_data_400(self, button):
        data = create_string(400)
        data = bytes("ARQ:DATA:" + data, 'utf-8')
        send_command(data)
        
    def send_arq_data_800(self, button):
        data = create_string(800)
        data = bytes("ARQ:DATA:" + data, 'utf-8')
        send_command(data)
        
    def send_cq(self, button):
        send_command('CQCQCQ')

builder = Gtk.Builder()
builder.add_from_file("tnc_gui.glade")
builder.connect_signals(Handler())

window = builder.get_object("main_window")
window.show_all()



GET_TNC_STATE_THREAD = threading.Thread(target=get_tnc_state, args=[], name="TNC STATE")
GET_TNC_STATE_THREAD.start()

GET_DATA_STATE_THREAD = threading.Thread(target=get_data_state, args=[], name="DATA STATE")
GET_DATA_STATE_THREAD.start()


Gtk.main()
