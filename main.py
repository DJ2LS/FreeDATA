#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:58:45 2020

@author: DJ2LS

"""

import socketserver
import threading


import tnc
import static
import modem

modem = modem.RF()


static.MODEM_RECEIVE = True    
audio_receiver_thread = threading.Thread(target=modem.Receive, name="Audio Listener")
audio_receiver_thread.start()



try:
    server = socketserver.TCPServer((static.HOST, static.PORT), tnc.TCPRequestHandler)
    server.serve_forever()
finally:
    server.server_close()