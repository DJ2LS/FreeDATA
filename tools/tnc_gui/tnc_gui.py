import socket
import random
import threading
import time
import json
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

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
    
    ip, port = builder.get_object('host').get_text(), int(builder.get_object('port').get_text())
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ip, port))
            if isinstance(command, str):
                 command = bytes(command, 'utf-8')

            sock.sendall(command + b'\n')
            #response = str(sock.recv(1024), 'utf-8')
            sock.close()
    except:
        pass    
            
         
            
def get_tnc_state():
    while True:
        time.sleep(0.05)      
        ip, port = builder.get_object('host').get_text(), int(builder.get_object('port').get_text()) 
        command = bytes('GET:TNC_STATE', 'utf-8')
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip, port))
                sock.sendall(command + b'\n')
                received = str(sock.recv(1024), "utf-8")
                received_json = json.loads(received)
                
                builder.get_object('ptt_state').set_text(received_json["PTT_STATE"])
                builder.get_object('channel_state').set_text(received_json["CHANNEL_STATE"])
                builder.get_object('tnc_state').set_text(received_json["TNC_STATE"])
                builder.get_object('arq_state').set_text(received_json["ARQ_STATE"])
                
                sock.close()            
        except:
            pass    
            
class Handler:
    def onDestroy(self, *args):
        Gtk.main_quit()

    def setCallsign(self, button):
        call = builder.get_object('callsign').get_text()
        send_command('SET:MYCALLSIGN:' + call)

    def ping(self, button):
        call = builder.get_object('callsign').get_text()
        send_command('PING:' + call)
        
    def connect(self, button):
        call = builder.get_object('callsign').get_text()
        send_command('ARQ:CONNECT:' + call)
        
    def disconnect(self, button):
        send_command('ARQ:DISCONNECT')

    def send_arq_data(self, button):
        datalength = int(builder.get_object('arqbytes').get_text())
        data = create_string(datalength)
        data = bytes("ARQ:DATA:" + data, 'utf-8')
        send_command(data)

    def send_cq(self, button):
        send_command('CQCQCQ')

builder = Gtk.Builder()
builder.add_from_file("tnc_gui.glade")
builder.connect_signals(Handler())

window = builder.get_object("main_window")
window.show_all()

#ip, port = builder.get_object('host').get_text(), int(builder.get_object('port').get_text())

GET_TNC_STATE_THREAD = threading.Thread(target=get_tnc_state, args=[], name="FREEDV_DECODER_THREAD")
GET_TNC_STATE_THREAD.start()

#GET_CHANNEL_STATE_THREAD = threading.Thread(target=get_channel_state, name="FREEDV_DECODER_THREAD")
#GET_CHANNEL_STATE_THREAD.start()


Gtk.main()


