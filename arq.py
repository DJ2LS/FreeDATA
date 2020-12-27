#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 27 20:43:40 2020

@author: DJ2LS
"""
# CRC aller payloads via XOR scrambeln und dann eine CRC8 mitsenden


import logging
import crcengine
import threading

import static
import modem
import other



modem = modem.RF()
crc_algorithm = crcengine.new('crc16-ccitt-false') #load crc16 library 

static.ARQ_PAYLOAD_PER_FRAME = static.FREEDV_PAYLOAD_PER_FRAME - 6

#class ARQ():
#    
#    def receive(bytes_in):
#        
#        print("TEST")


def receive(data_in):
    print(data_in[:1])


def transmit(data_out):
        
            static.ARQ_PAYLOAD_PER_FRAME = static.FREEDV_PAYLOAD_PER_FRAME - 6
        
            static.TX_BUFFER = [data_out[i:i+static.ARQ_PAYLOAD_PER_FRAME] for i in range(0, len(data_out), static.ARQ_PAYLOAD_PER_FRAME)] # split incomming bytes to size of 30bytes, create a list and loop through it  
            static.TX_BUFFER_SIZE = len(static.TX_BUFFER)
            logging.info("TX | TOTAL PAYLOAD BYTES/FRAMES TO SEND: " + str(len(data_out)) + " / " + str(static.TX_BUFFER_SIZE))
            
            for n_raw_frame in range(0, static.TX_BUFFER_SIZE, static.ARQ_TX_N_FRAMES): # LOOP THROUGH DATA LIST with steps = ARQ_TX_N_FRAMES
                print("N_RAW_FRAME: " + str(n_raw_frame)) 
      
                # ----------- GENERATE PAYLOAD CRC FOR ARQ_TX_N_FRAMES
                burst_total_payload = bytearray()
                
                for i in range(static.ARQ_TX_N_FRAMES): #bytearray(b'111111111111111111111111222222222222222222222222')
                    burst_total_payload = burst_total_payload + static.TX_BUFFER[n_raw_frame + i]
 
                burst_payload_crc = crc_algorithm(burst_total_payload)
                burst_payload_crc = burst_payload_crc.to_bytes(2, byteorder='big') #b'\xa7\xd6'
                print(burst_payload_crc)
                
                #-------------------- BUILD ARQBURSTS
                arqburst = []
                for i in range(static.ARQ_TX_N_FRAMES):
                        
                    #print(n_raw_frame)
                    #print(i)
                    #print(n_raw_frame + i)
                    #print(static.TX_BUFFER[n_raw_frame + i])
                     
                    frame_type = 10 + static.ARQ_TX_N_FRAMES
                    frame_type = bytes([frame_type])
                    
                    payload_data = bytes(static.TX_BUFFER[n_raw_frame + i])
                    
                    arqframe = frame_type + burst_payload_crc + payload_data
                    
                    arqburst.append(arqframe)


                #--------------------------------------------- N ATTEMPTS TO SEND BURSTS IF ACK FAILS
                for static.TX_N_RETRIES in range(static.TX_N_MAX_RETRIES):
                    
                    static.ACK_RECEIVED = 0
                    
                    # ----------------------- Loop through ARQ FRAMES BUFFER with N = Numbers of frames which will be send at once
                    for n in range(static.ARQ_TX_N_FRAMES):
                        logging.info("TX | SENDING BURST " + str(n+1) + " / " + str(static.ARQ_TX_N_FRAMES))
                        modem.Transmit(arqburst[n])
                        #modem.RF.Transmit(arqburst[n])
                        print(arqburst[n])
                        
                    # --------------------------- START TIMER ---> IF TIMEOUT REACHED, ACK_TIMEOUT = 1
                    static.ACK_TIMEOUT = 0
                    timer = threading.Timer(static.ACK_TIMEOUT_SECONDS * static.ARQ_TX_N_FRAMES, other.timeout)
                    timer.start() 

                    # --------------------------- WHILE TIMEOUT NOT REACHED AND NO ACK RECEIVED --> LISTEN
                    logging.info("TX | WAITING FOR ACK")

                    while static.ACK_TIMEOUT == 0 and static.ACK_RECEIVED == 0:
                        static.MODEM_RECEIVE = True
                    else:
                        logging.info("TX | ACK TIMEOUT - SENDING AGAIN")
                    
                    #--------------- BREAK LOOP IF ACK HAS BEEN RECEIVED
                    if static.ACK_RECEIVED == 1:
                        #static.TX_N_RETRIES = 3
                        break
                 
                # ----------- if no ACK received and out of retries.....stop frame sending
                if static.ACK_RECEIVED == 0:
                    logging.info("TX | NO ACK RECEIVED | FRAME NEEDS TO BE RESEND!")
                    break


                #-------------------------BREAK TX BUFFER LOOP IF ALL PACKETS HAVE BEEN SENT
                if n_raw_frame == static.TX_BUFFER_SIZE:
                    break
                        
            logging.info("TX | BUFFER EMPTY")