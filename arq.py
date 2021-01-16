#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 27 20:43:40 2020

@author: DJ2LS
"""

import logging
import threading
import time
from random import randrange

import static
import modem
import helpers

modem = modem.RF()

static.ARQ_PAYLOAD_PER_FRAME = static.FREEDV_PAYLOAD_PER_FRAME - 3 #6?!
static.ARQ_ACK_PAYLOAD_PER_FRAME = 14 - 2# --> 700D


def arq_ack_timeout():
    static.ACK_TIMEOUT = 1

    
def data_received(data_in):
    
        ARQ_N_RX_BURSTS = int.from_bytes(bytes(data_in[:1]), "big")  - 10 #get number of bursts from received frame
        static.ARQ_RX_BURST_BUFFER.append(data_in) #append data to RX BUFFER 
    
        print("WAITING FOR BURSTS: " + str(ARQ_N_RX_BURSTS))
        print("ARQ_RX_BURST_BUFFER: " + str(len(static.ARQ_RX_BURST_BUFFER)))
        
        burst_total_payload = bytearray()

    #while static.ACK_RX_TIMEOUT == 0: #define timeout where data has to be received untl error occurs
    
        if len(static.ARQ_RX_BURST_BUFFER) == ARQ_N_RX_BURSTS: #if received bursts are equal to burst number in frame
            
            for n_raw_frame in range(0,len(static.ARQ_RX_BURST_BUFFER)):
            
                burst_frame = static.ARQ_RX_BURST_BUFFER[n_raw_frame] #get burst frame
                burst_payload = burst_frame[3:] #remove frame type and burst CRC        
                burst_total_payload = burst_total_payload + burst_payload #stick bursts together
            
            # ------------------ caculate CRC of BURST 
            burst_payload_crc = helpers.get_crc_16(burst_total_payload)

            # IF BURST CRC IS CORRECT, APPEND BURST TO BUFFER AND SEND ACK FRAME
            if burst_payload_crc == data_in[1:3]:

                logging.info("BURST CRC ARE EQUAL!")
                static.ARQ_RX_FRAME_BUFFER.append(burst_total_payload) # IF CRC TRUE APPEND burst_total_payload TO ARQ_RX_FRAME_BUFFER
                             
                #BUILDING ACK FRAME -----------------------------------------------
                
                ack_payload = bytes(burst_payload_crc)
                #ack_frame = b'\7'+ bytes(burst_payload_crc)
                ack_frame = b'<'+ bytes(burst_payload_crc) # < = 60
                #ack_frame[1] = b'\7'
                #ack_frame[2] = helpers.get_crc8(data)
                #ack_frame[3:4] = bytes(burst_payload_crc)
                
                frametype = int.from_bytes(bytes(ack_frame[:1]), "big")  
                print("ACK TYPE: " + str(frametype))
                      
                ack_buffer = bytearray(static.ARQ_ACK_PAYLOAD_PER_FRAME) 
                ack_buffer[:len(ack_frame)] = ack_frame # set buffersize to length of data which will be send                 
            
                #TRANSMIT ACK FRAME -----------------------------------------------
                logging.info("TX | SENDING ARQ BURST ACK [" + str(data_in[1:3]) +"]")
                modem.transmit(7,ack_buffer)
                print(ack_buffer)
                
                # ------------------------------------------------------------
                frametype = int.from_bytes(bytes(ack_buffer[:1]), "big")  
                print("ACK TYPE: " + str(frametype))
                
                # ----------------------------------------------------------------
                
                static.ARQ_RX_BURST_BUFFER = [] # CLEAR RX BURST BUFFER
         
            else: #IF burst payload crc and input crc are NOT equal
                print("CRC NOT EQUAL!!!!!")
                print(data_in[1:3])
                static.ARQ_RX_BURST_BUFFER = [] 

        
        # LOOP THOUGH FRAME BUFFER AND STICK EVERYTHING TOGETHER 
        # WE ALSO CHECK FOR FRAME HEADER AND LAST FRAME
        complete_frame = bytearray()    
        print(static.ARQ_RX_FRAME_BUFFER)
        for frame in range(len(static.ARQ_RX_FRAME_BUFFER)):
                    complete_frame = complete_frame + static.ARQ_RX_FRAME_BUFFER[frame]
                    print(complete_frame)
                    print(complete_frame[4:6])
                    # -------- DETECT IF WE ALREADY RECEIVED A FRAME HEADER THEN SAVE DATA TO GLOBALS
                    #if burst_total_payload[4:6].startswith(b'\xAA\xAA'):
                    
                    if complete_frame[4:6].startswith(b'\xAA\xAA') or burst_total_payload[4:6].startswith(b'\xAA\xAA'):    
                        print("FRAME HEADER RECEIVED!")
                        #print("FRAME BURSTS = " + str(complete_frame[:2]))
                        #print("FRAME CRC = " + str(complete_frame[2:4]))
                        static.FRAME_CRC = complete_frame[2:4]
                        static.ARQ_RX_FRAME_N_BURSTS = int.from_bytes(bytes(complete_frame[:2]), "big")  
                 
                    # -------- DETECT IF WE HAVE ALREADY RECEIVED THE LAST FRAME
                    if burst_total_payload.rstrip(b'\x00').endswith(b'\xFF\xFF'):
                        print("DAS IST DER LETZTE BURST MIT EOF!!!")

        print("WEITER GEHTS...")
        # NOW WE TRY TO SEPARATE THE FRAME CRC FOR A CRC CALCULATION
        frame_payload = complete_frame.rstrip(b'\x00') #REMOVE x00
        frame_payload = frame_payload[6:-2] #THIS IS THE FRAME PAYLOAD      
        frame_payload_crc = helpers.get_crc_16(frame_payload)        
                    
        #IF THE FRAME PAYLOAD CRC IS EQUAL TO THE FRAME CRC WHICH IS KNOWN FROM THE HEADER --> SUCCESS      
        if frame_payload_crc == static.FRAME_CRC:
             logging.info("RX | FILE SUCESSFULL RECEIVED! - TIME TO PARTY")
             static.RX_BUFFER.append(frame_payload)
             static.ARQ_RX_FRAME_BUFFER = []
             #print(static.RX_BUFFER[-1])
             # HERE: SEND ACK FOR TOTAL FRAME!!!
                    
        #else:
            #print("CRC FOR FRAME NOT EQUAL!")
           # print("FRAME PAYLOAD CRC: " + str(frame_payload_crc))
           # print("FRAME PAYLOAD: " + str(frame_payload))
            #print("COMPLETE FRAME: " + str(complete_frame))
            #static.ARQ_RX_FRAME_BUFFER = []   # ---> BUFFER ERST LÖSCHEN WENN MINDESTANZAHL AN BURSTS ERHALTEN WORDEN SIND

def ack_received():
    
    logging.info("RX | ACK RCVD!")
    static.ACK_TIMEOUT = 1 #Force timer to stop waiting
    static.ACK_RECEIVED = 1 #Force data loops of TNC to stop and continue with next frame
    # static.ARQ_ACK_WAITING_FOR_ID

def transmit(data_out):
    
            #static.ARQ_PAYLOAD_PER_FRAME = static.FREEDV_PAYLOAD_PER_FRAME - 3
            #----------------------- BUILD A FRAME WITH CRC AND N BURSTS SO THE RECEIVER GETS THIS INFORMATION
            
            frame_BOF = b'\xAA\xAA'
            frame_EOF = b'\xFF\xFF'

            frame_header_length = 8
            
            n_bursts_prediction = (len(data_out)+frame_header_length) // static.ARQ_PAYLOAD_PER_FRAME + ((len(data_out)+frame_header_length) % static.ARQ_PAYLOAD_PER_FRAME > 0) # aufrunden 3.2 = 4
            n_bursts_prediction = n_bursts_prediction.to_bytes(2, byteorder='big') #65535

            frame_payload_crc = helpers.get_crc_16(data_out)
            
            # This is the total frame with frame header, which will be send
            data_out = n_bursts_prediction + frame_payload_crc + frame_BOF + data_out + frame_EOF
            #                  2                   2                 2         N           2
            #print(data_out)
            
            # --------------------------------------------- LETS CREATE A BUFFER BY SPLITTING THE FILES INTO PEACES
            static.TX_BUFFER = [data_out[i:i+static.ARQ_PAYLOAD_PER_FRAME] for i in range(0, len(data_out), static.ARQ_PAYLOAD_PER_FRAME)]
            static.TX_BUFFER_SIZE = len(static.TX_BUFFER)
            
            logging.info("TX | TOTAL PAYLOAD BYTES/FRAMES TO SEND: " + str(len(data_out)) + " / " + str(static.TX_BUFFER_SIZE))
            

            ###static.ACK_RECEIVED = 0 # SET ACK RECEIVED TO 0 IF NOT ALREADY DONE TO BE SURE WE HAVE A NEW CYCLE
                      
            # --------------------------------------------- THIS IS THE MAIN LOOP
            static.ARQ_N_SENT_FRAMES = 0 # SET N SENT FRAMES TO 0 FOR A NEW SENDING CYCLE
            while static.ARQ_N_SENT_FRAMES <= static.TX_BUFFER_SIZE:

                print("static.ARQ_N_SENT_FRAMES: " + str(static.ARQ_N_SENT_FRAMES))
                ############################----------RANDOM FRAMES PER BURST MACHINE --> HELPER FOR SIMULATING DYNAMIC ARQ UNTIL BURST MACHINE IS BUILD
                #static.ARQ_TX_N_FRAMES = get_n_frames_per_burst(len(data_out))
                static.ARQ_TX_N_FRAMES = get_n_frames_per_burst()
                static.ACK_RECEIVED = 0 # SET ACK RECEIVED TO 0 IF NOT ALREADY DONE TO BE SURE WE HAVE A NEW CYCLE
                #################################################################
                
                
                # ----------- SET FRAME PAYLOAD TO BE ABLE TO CREATE CRC
                burst_total_payload = bytearray()
                try: # DETECT IF LAST BURST TO PREVENT INDEX ERROR OF BUFFER
                    for i in range(static.ARQ_TX_N_FRAMES): #bytearray(b'111111111111111111111111222222222222222222222222')
                        
                        # we need to make sure, payload data is always as long as static.ARQ_PAYLOAD_PER_FRAME beacuse of CRC!                      
                        burst_raw_payload = static.TX_BUFFER[static.ARQ_N_SENT_FRAMES + i] 
                        burst_payload = bytearray(static.ARQ_PAYLOAD_PER_FRAME) 
                        burst_payload[:len(burst_raw_payload)] = burst_raw_payload # set buffersize to length of data which will be send        
                        burst_total_payload = burst_total_payload + burst_payload
                 
                except IndexError: # IF LAST BURST DETECTED BUILD CRC WITH LESS FRAMES AND SET static.ARQ_TX_N_FRAMES TO VALUE OF REST!

                     burst_total_payload = bytearray() # reset burst_total_payload because of possible input remaining of detecting loop one step above

                     if static.ARQ_N_SENT_FRAMES == 0  and (static.ARQ_TX_N_FRAMES > static.TX_BUFFER_SIZE): #WE CANT DO MODULO 0 --> CHECK IF FIRST FRAME == LAST FRAME
                          static.ARQ_TX_N_FRAMES = static.TX_BUFFER_SIZE
                     
                     elif static.ARQ_N_SENT_FRAMES == 1 and (static.ARQ_TX_N_FRAMES > static.TX_BUFFER_SIZE): # MODULO 1 WILL ALWAYS BE 0 --> THIS FIXES IT
                            static.ARQ_TX_N_FRAMES = static.TX_BUFFER_SIZE - static.ARQ_N_SENT_FRAMES
                         
                     else:
                         static.ARQ_TX_N_FRAMES = (static.TX_BUFFER_SIZE % static.ARQ_N_SENT_FRAMES)
                         #print("static.TX_BUFFER_SIZE: " + str(static.TX_BUFFER_SIZE))
                         #print("static.ARQ_N_SENT_FRAMES: " + str(static.ARQ_N_SENT_FRAMES))

                     print("ARQ_TX_N_FRAMES OF LAST BURST: " + str(static.ARQ_TX_N_FRAMES))
                     for i in range(static.ARQ_TX_N_FRAMES): #bytearray(b'111111111111111111111111222222222222222222222222')
                        
                        # we need to make sure, payload data is always as long as static.ARQ_PAYLOAD_PER_FRAME beacuse of CRC!
                        burst_raw_payload = static.TX_BUFFER[static.ARQ_N_SENT_FRAMES + i]
                        burst_payload = bytearray(static.ARQ_PAYLOAD_PER_FRAME) 
                        burst_payload[:len(burst_raw_payload)] = burst_raw_payload # set buffersize to length of data which will be send        
                        burst_total_payload = burst_total_payload + burst_payload
                                       
                # ----------- GENERATE PAYLOAD CRC FOR ARQ_TX_N_FRAMES
                
                burst_payload_crc = helpers.get_crc_16(burst_total_payload)
                static.ARQ_ACK_WAITING_FOR_ID = burst_payload_crc #set the global variable so we know for which ACK we are waiting for
              
                #------------------ BUILD ARQBURSTS---------------------------------------------
                arqburst = []
                for i in range(static.ARQ_TX_N_FRAMES):
                    
                        frame_type = 10 + static.ARQ_TX_N_FRAMES
                        frame_type = bytes([frame_type])
                    
                        payload_data = bytes(static.TX_BUFFER[static.ARQ_N_SENT_FRAMES + i])
                    
                        arqframe = frame_type + burst_payload_crc + payload_data
                    
                        buffer = bytearray(static.FREEDV_PAYLOAD_PER_FRAME) # create TX buffer 
                        buffer[:len(arqframe)] = arqframe # set buffersize to length of data which will be send
                          
                        arqburst.append(buffer) #append data to a buffer array, so we can loop through it

                #--------------------------------------------- N ATTEMPTS TO SEND BURSTS IF ACK RECEPTION FAILS
                for static.TX_N_RETRIES in range(static.TX_N_MAX_RETRIES):
                    
                    static.ACK_RECEIVED = 0 #SET AGAIN ACK_RECEIVED TO 0 SO WE CAN BE SURE WE ARE WAITING FOR THE CORRECT ACK
                    
                    # ----------------------- Loop through ARQ FRAMES BUFFER with N = Numbers of frames which will be send at once
                    for n in range(static.ARQ_TX_N_FRAMES):
                        logging.info("TX | SENDING BURST [" + str(n+1) + " / " + str(static.ARQ_TX_N_FRAMES) + "] [" + str(static.ARQ_N_SENT_FRAMES +  n+1) + " / " + str(static.TX_BUFFER_SIZE) + "] [" + str(burst_payload_crc) + "]")
                        modem.transmit(12, arqburst[n])
                        #LETS SLEEP SOME TIME FOR TX COOLDOWN --> CAN BE REMOVED LATER IF SYNC/UNSYNC OF FREEDV IS WORKING BETTER
                        #########################time.sleep(4)

                    # --------------------------- START TIMER FOR WAITING FOR ACK ---> IF TIMEOUT REACHED, ACK_TIMEOUT = 1
                    static.ACK_TIMEOUT = 0
                    timer = threading.Timer(static.ACK_TIMEOUT_SECONDS * static.ARQ_TX_N_FRAMES, arq_ack_timeout)
                    timer.start() 
                    logging.info("TX | WAITING FOR ACK")

                    #static.MODEM_RECEIVE = False

                    # --------------------------- WHILE TIMEOUT NOT REACHED AND NO ACK RECEIVED --> LISTEN
                    while static.ACK_TIMEOUT == 0 and static.ACK_RECEIVED == 0:
                        time.sleep(0.05) # here we reduce CPU load
                        #static.MODEM_RECEIVE = True
                    #else:
                        #logging.info("TX | ACK TIMEOUT - SENDING AGAIN")
                        #pass
                        #static.MODEM_RECEIVE = False
                        #time.sleep(1)

                    
                    #--------------- BREAK LOOP IF ACK HAS BEEN RECEIVED
                    ######if static.ACK_RECEIVED == 1:
                    if static.ACK_RECEIVED == 1:

                        #static.MODEM_RECEIVE = False
                        #time.sleep(1)               
                        
                        #-----------IF ACK RECEIVED, INCREMENT ITERATOR FOR MAIN LOOP TO PROCEED WITH NEXT FRAMES/BURST
                        static.ARQ_N_SENT_FRAMES = static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES
                        break
                 
                # ----------- if no ACK received and out of retries.....stop frame sending
                if static.ACK_RECEIVED == 0:
                    logging.info("TX | NO ACK RECEIVED | FRAME NEEDS TO BE RESEND!")
                    break


                #-------------------------BREAK TX BUFFER LOOP IF ALL PACKETS HAVE BEEN SENT
                if static.ARQ_N_SENT_FRAMES == static.TX_BUFFER_SIZE:    
                    break                
                
                # ------------ TIMER TO WAIT UNTIL NEXT PACKAGE WILL BE SEND TO PREVENT TIME ISSEUS --> NEEDS TO BE IMPROVED LATER
                time.sleep(5)
                        
            # IF TX BUFFER IS EMPTY / ALL FRAMES HAVE BEEN SENT --> HERE WE COULD ADD AN static.VAR for IDLE STATE    
            logging.info("TX | BUFFER EMPTY")
            
           
# BURST MACHINE TO DEFINE N BURSTS PER FRAME    ---> LATER WE CAN USE CHANNEL MESSUREMENT TO SET FRAMES PER BURST         
def get_n_frames_per_burst():
 
    n_frames_per_burst = randrange(1,5)           
    return n_frames_per_burst
