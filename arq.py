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

static.ARQ_PAYLOAD_PER_FRAME = static.FREEDV_DATA_PAYLOAD_PER_FRAME - 3 #6?!
static.ARQ_ACK_PAYLOAD_PER_FRAME = 14 - 2#

def arq_ack_timeout():
    static.ARQ_ACK_TIMEOUT = 1

    
def data_received(data_in):
    
        static.ARQ_N_FRAME = int.from_bytes(bytes(data_in[:1]), "big")  - 10 #get number of frame
        static.ARQ_N_RX_FRAMES_PER_BURSTS = int.from_bytes(bytes(data_in[1:2]), "big") #get number of bursts from received frame
        
        logging.info("ARQ | RX | FRAME [" + str(static.ARQ_N_FRAME) + "/" + str(static.ARQ_N_RX_FRAMES_PER_BURSTS) + "] [" + str((static.ARQ_N_FRAME / static.ARQ_N_RX_FRAMES_PER_BURSTS)*100) + "%]")
    
        #allocate ARQ_RX_BURST_BUFFER list with 0 if not already done
        # here we will save the N frame of a burst to N list position so we can explicit search for it
        if static.ARQ_N_RX_FRAMES_PER_BURSTS != len(static.ARQ_RX_BURST_BUFFER) and static.ARQ_N_FRAME == 1:
            print("LIST ALLOCATION!")
            for i in range(0,static.ARQ_N_RX_FRAMES_PER_BURSTS+1):
                static.ARQ_RX_BURST_BUFFER.insert(i,None)
            print(len(static.ARQ_RX_BURST_BUFFER))     
        # now we add the incoming data to the specified position in our list
        static.ARQ_RX_BURST_BUFFER[static.ARQ_N_FRAME] = bytes(data_in) 

        # run if we recieved all frames
        burst_total_payload = bytearray()
        if static.ARQ_N_FRAME == static.ARQ_N_RX_FRAMES_PER_BURSTS: #if received bursts are equal to burst number in frame
            print("JETZT GEHTS LOS MIT DER SCHLEIFE")
            print(len(static.ARQ_RX_BURST_BUFFER)-1)
            
            for l in range(0,len(static.ARQ_RX_BURST_BUFFER)):
                print(static.ARQ_RX_BURST_BUFFER[l])
            
            
            #here we get the total payload for the frame         
            for n_raw_frame in range(1,len(static.ARQ_RX_BURST_BUFFER)):
                # we need to check if we have a None or received data in list
                if static.ARQ_RX_BURST_BUFFER[n_raw_frame] != None:
                    burst_frame = static.ARQ_RX_BURST_BUFFER[n_raw_frame] #get burst frame
                    burst_payload = burst_frame[4:] #remove frame type and burst CRC     
                    burst_total_payload = burst_total_payload + burst_payload #stick bursts together
                    
            # ------------------ calculate CRC of BURST          
            burst_payload_crc = helpers.get_crc_16(burst_total_payload)
            # IF BURST CRC IS CORRECT, APPEND BURST TO BUFFER AND SEND ACK FRAME
            if burst_payload_crc == data_in[2:4]:

                logging.info("BURST CRC ARE EQUAL!")
                static.ARQ_RX_FRAME_BUFFER.append(burst_total_payload) # IF CRC TRUE APPEND burst_total_payload TO ARQ_RX_FRAME_BUFFER
                             
                #BUILDING ACK FRAME -----------------------------------------------              
                ack_payload = bytes(burst_payload_crc)
                ack_frame = b'<'+ bytes(burst_payload_crc) # < = 60   
                ack_buffer = bytearray(static.ARQ_ACK_PAYLOAD_PER_FRAME) 
                ack_buffer[:len(ack_frame)] = ack_frame # set buffersize to length of data which will be send                 
            
                #TRANSMIT ACK FRAME -----------------------------------------------
                # we need to wait until RX is finished on TX side
                time.sleep(3.8)
                logging.info("ARQ | TX | SENDING ARQ BURST ACK [" + str(data_in[1:3]) +"]")
                modem.transmit_arq_ack(ack_buffer)

                # ----------------------------------------------------------------
                
                static.ARQ_RX_BURST_BUFFER = [] # CLEAR RX BURST BUFFER AFTER SENDING DATA
                
            else: #IF burst payload crc and input crc are NOT equal
                logging.info("CRC NOT EQUAL!!!!![" + str(data_in[2:4]) + "]")
                static.ARQ_RX_BURST_BUFFER = []  #erase ARQ RX Burst buffer

        
        # LOOP THOUGH FRAME BUFFER AND STICK EVERYTHING TOGETHER 
        # WE ALSO CHECK FOR FRAME HEADER AND LAST FRAME
        complete_frame = bytearray()    
        #print(static.ARQ_RX_FRAME_BUFFER)
        for frame in range(len(static.ARQ_RX_FRAME_BUFFER)):
                    complete_frame = complete_frame + static.ARQ_RX_FRAME_BUFFER[frame]
                  
                    # -------- DETECT IF WE ALREADY RECEIVED A FRAME HEADER THEN SAVE DATA TO GLOBALS
                    if complete_frame[4:6].startswith(static.FRAME_BOF) or burst_total_payload[4:6].startswith(static.FRAME_BOF):    #5:7
                        #print("FRAME BOF RECEIVED")
                        static.FRAME_CRC = complete_frame[2:4]
                 
                    # -------- DETECT IF WE HAVE ALREADY RECEIVED THE LAST FRAME
                    if burst_total_payload.rstrip(b'\x00').endswith(static.FRAME_EOF):
                        pass
                        #print("FRAME EOF RECEIVED")

        # NOW WE TRY TO SEPARATE THE FRAME CRC FOR A CRC CALCULATION
        frame_payload = complete_frame.rstrip(b'\x00') #REMOVE x00
        frame_payload = frame_payload[6:-2] #THIS IS THE FRAME PAYLOAD      
        frame_payload_crc = helpers.get_crc_16(frame_payload)        
         
        #IF THE FRAME PAYLOAD CRC IS EQUAL TO THE FRAME CRC WHICH IS KNOWN FROM THE HEADER --> SUCCESS      
        if frame_payload_crc == static.FRAME_CRC:
             logging.info("ARQ | RX | FRAME SUCESSFULLY RECEIVED! - TIME TO PARTY")
             static.RX_BUFFER.append(frame_payload)
             static.ARQ_RX_FRAME_BUFFER = []
             print("----------------------------------------------------------------")
             print(static.RX_BUFFER[-1])
             print("----------------------------------------------------------------")
             # HERE: WE COULD SEND ACK FOR TOTAL FRAME                  
        #else:
            logging.info("ARQ | RX | FRAME NOT SUCESSFULLY RECEIVED!")
            print("FRAME PAYLOAD CRC: " + str(frame_payload_crc))
            print("FRAME PAYLOAD: " + str(frame_payload))
            print("COMPLETE FRAME: " + str(complete_frame))
            #static.ARQ_RX_FRAME_BUFFER = []   # ---> BUFFER ERST LÖSCHEN WENN MINDESTANZAHL AN BURSTS ERHALTEN WORDEN SIND

def ack_received():
    
    logging.info("ARQ | RX | ACK RCVD!")
    static.ARQ_ACK_TIMEOUT = 1 #Force timer to stop waiting
    static.ARQ_ACK_RECEIVED = 1 #Force data loops of TNC to stop and continue with next frame


def transmit(data_out):

 
            static.ARQ_PAYLOAD_PER_FRAME = static.FREEDV_DATA_PAYLOAD_PER_FRAME - 4 #3 ohne ARQ_TX_N_FRAMES_PER_BURST  
            frame_header_length = 8  
            
            n_bursts_prediction = (len(data_out)+frame_header_length) // static.ARQ_PAYLOAD_PER_FRAME + ((len(data_out)+frame_header_length) % static.ARQ_PAYLOAD_PER_FRAME > 0) # aufrunden 3.2 = 4
            #print(static.FREEDV_DATA_PAYLOAD_PER_FRAME)
            #print(static.ARQ_PAYLOAD_PER_FRAME)
            #print(n_bursts_prediction)
            n_bursts_prediction = n_bursts_prediction.to_bytes(2, byteorder='big') #65535

            frame_payload_crc = helpers.get_crc_16(data_out)
            
            # This is the total frame with frame header, which will be send
            data_out = n_bursts_prediction + frame_payload_crc + static.FRAME_BOF + data_out + static.FRAME_EOF
            #                  2                   2                 2         N           2
            #print(data_out)
            #print(len(data_out))
            #print(static.ARQ_PAYLOAD_PER_FRAME)
            # --------------------------------------------- LETS CREATE A BUFFER BY SPLITTING THE FILES INTO PEACES
            static.TX_BUFFER = [data_out[i:i+static.ARQ_PAYLOAD_PER_FRAME] for i in range(0, len(data_out), static.ARQ_PAYLOAD_PER_FRAME)]
            static.TX_BUFFER_SIZE = len(static.TX_BUFFER)
            #print(static.TX_BUFFER)
            
            logging.info("ARQ | TX | TOTAL PAYLOAD BYTES/FRAMES TO SEND: " + str(len(data_out)) + " / " + str(static.TX_BUFFER_SIZE))
                      
            # --------------------------------------------- THIS IS THE MAIN LOOP-----------------------------------------------------------------
   
            static.ARQ_N_SENT_FRAMES = 0 # SET N SENT FRAMES TO 0 FOR A NEW SENDING CYCLE
            while static.ARQ_N_SENT_FRAMES <= static.TX_BUFFER_SIZE:

                print("static.ARQ_N_SENT_FRAMES: " + str(static.ARQ_N_SENT_FRAMES))
                static.ARQ_TX_N_FRAMES_PER_BURST = get_n_frames_per_burst()
                           
                # ----------- CREATE FRAME TOTAL PAYLOAD TO BE ABLE TO CREATE CRC FOR IT
                burst_total_payload = bytearray()
                try: # DETECT IF LAST BURST TO PREVENT INDEX ERROR OF BUFFER
                    for i in range(static.ARQ_TX_N_FRAMES_PER_BURST): # Loop through TX_BUFFER LIST
                    
                        # make sure we have always a filled buffer with the length of payload per frame
                        burst_raw_payload = static.TX_BUFFER[static.ARQ_N_SENT_FRAMES + i] 
                        burst_payload = bytearray(static.ARQ_PAYLOAD_PER_FRAME) 
                        burst_payload[:len(burst_raw_payload)] = burst_raw_payload # get frame from TX_BUFFER     
                        burst_total_payload = burst_total_payload + burst_payload # append single frame to total payload buffer
                                    
                except IndexError: # IF LAST BURST DETECTED BUILD CRC WITH LESS FRAMES AND SET static.ARQ_TX_N_FRAMES_PER_BURST TO VALUE OF REST!
                     
                     burst_total_payload = bytearray() # reset burst_total_payload because of possible input remaining of detecting loop one step above
                     if static.ARQ_N_SENT_FRAMES == 0  and (static.ARQ_TX_N_FRAMES_PER_BURST > static.TX_BUFFER_SIZE): #WE CANT DO MODULO 0 --> CHECK IF FIRST FRAME == LAST FRAME
                          static.ARQ_TX_N_FRAMES_PER_BURST = static.TX_BUFFER_SIZE
                     
                     elif static.ARQ_N_SENT_FRAMES == 1 and (static.ARQ_TX_N_FRAMES_PER_BURST > static.TX_BUFFER_SIZE): # MODULO 1 WILL ALWAYS BE 0 --> THIS FIXES IT
                            static.ARQ_TX_N_FRAMES_PER_BURST = static.TX_BUFFER_SIZE - static.ARQ_N_SENT_FRAMES
                         
                     else:
                         static.ARQ_TX_N_FRAMES_PER_BURST = (static.TX_BUFFER_SIZE % static.ARQ_N_SENT_FRAMES)

                     print("ARQ_TX_N_FRAMES_PER_BURST OF LAST BURST: " + str(static.ARQ_TX_N_FRAMES_PER_BURST))
                     
                     for i in range(static.ARQ_TX_N_FRAMES_PER_BURST): #bytearray(b'111111111111111111111111222222222222222222222222')
                        
                        # make sure we have always a filled buffer with the length of payload per frame
                        burst_raw_payload = static.TX_BUFFER[static.ARQ_N_SENT_FRAMES + i] 
                        burst_payload = bytearray(static.ARQ_PAYLOAD_PER_FRAME) 
                        burst_payload[:len(burst_raw_payload)] = burst_raw_payload # get frame from TX_BUFFER     
                        burst_total_payload = burst_total_payload + burst_payload # append single frame to total payload buffer
                     #print(burst_total_payload)                  
                # ----------- GENERATE PAYLOAD CRC FOR ARQ_TX_N_FRAMES_PER_BURST
                
                static.ARQ_BURST_PAYLOAD_CRC = helpers.get_crc_16(burst_total_payload)
              
                #--------------------------------------------- N ATTEMPTS TO SEND BURSTS IF ACK RECEPTION FAILS
                for static.TX_N_RETRIES in range(static.TX_N_MAX_RETRIES):
                    print("SENDING")
                    #reset timer and ack state
                    static.ARQ_ACK_RECEIVED = 0
                    static.ARQ_ACK_TIMEOUT = 0
                    # lets start a thread to transmit nonblocking
                    TRANSMIT_ARQ_BURST_THREAD = threading.Thread(target=modem.transmit_arq_burst, name="TRANSMIT_ARQ_BURST")
                    TRANSMIT_ARQ_BURST_THREAD.start()
                    
                    # lets sleep a while during sending. After this we will continue
                    while static.ARQ_STATE == 'SENDING_DATA':
                        time.sleep(0.05)
                        
                        
                    # --------------------------- START TIMER FOR WAITING FOR ACK ---> IF TIMEOUT REACHED, ACK_TIMEOUT = 1
                    logging.info("ARQ | WAITING FOR ACK")
                    static.ARQ_STATE = 'RECEIVING_ACK'
                    
                    timer = threading.Timer(static.ARQ_ACK_TIMEOUT_SECONDS, arq_ack_timeout)
                    timer.start() 
                    
                    # waiting the other way...
                    #starttimer = time.time() + static.ARQ_ACK_TIMEOUT_SECONDS
                    #while starttimer > time.time() and static.ARQ_ACK_RECEIVED == 0:
                    #    #print(str(starttimer - time.time()))
                    #    pass
                    #else:
                    #    static.ARQ_ACK_TIMEOUT = 1

                    #static.MODEM_RECEIVE = False

                    # --------------------------- WHILE TIMEOUT NOT REACHED AND NO ACK RECEIVED --> LISTEN
                    while static.ARQ_ACK_TIMEOUT == 0 and static.ARQ_ACK_RECEIVED == 0:                 
                        time.sleep(0.01) # lets reduce CPU load a little bit
                        
                         
                        #--------------- BREAK LOOP IF ACK HAS BEEN RECEIVED
                    if static.ARQ_ACK_RECEIVED == 1:                        
                        #-----------IF ACK RECEIVED, INCREMENT ITERATOR FOR MAIN LOOP TO PROCEED WITH NEXT FRAMES/BURST
                        static.ARQ_N_SENT_FRAMES = static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST
                        break
                        
                    if static.ARQ_ACK_RECEIVED == 0 and static.ARQ_ACK_TIMEOUT == 1:
                        logging.info("ARQ | ACK TIMEOUT | SENDING BURST AGAIN")
                 
                # ----------- if no ACK received and out of retries.....stop frame sending
                if static.ARQ_ACK_RECEIVED == 0 and static.ARQ_ACK_TIMEOUT == 1:
                        logging.info("ARQ | TX | NO ACK RECEIVED | DATA FRAME NEEDS TO BE RESEND!")
                        break


                #-------------------------BREAK TX BUFFER LOOP IF ALL PACKETS HAVE BEEN SENT
                if static.ARQ_N_SENT_FRAMES == static.TX_BUFFER_SIZE:    
                    break                
                
                # ------------ TIMER TO WAIT UNTIL NEXT PACKAGE WILL BE SEND TO PREVENT TIME ISSEUS --> NEEDS TO BE IMPROVED LATER
                #time.sleep(3)
                        
            # IF TX BUFFER IS EMPTY / ALL FRAMES HAVE BEEN SENT --> HERE WE COULD ADD AN static.VAR for IDLE STATE    
            #logging.info("ARQ | TX | FRAME SUCESSFULLY TRANSMITTED! - TIME TO PARTY")
            logging.info("ARQ | TX | BUFFER EMPTY")
            print(static.ARQ_N_SENT_FRAMES)
            print(static.ARQ_TX_N_FRAMES_PER_BURST)
            # - RESET COUNTERS
            static.ARQ_N_SENT_FRAMES = 0
            static.ARQ_TX_N_FRAMES_PER_BURST = 0
            static.ARQ_ACK_RECEIVED = 0
            
           
# BURST MACHINE TO DEFINE N BURSTS PER FRAME    ---> LATER WE CAN USE CHANNEL MESSUREMENT TO SET FRAMES PER BURST         
def get_n_frames_per_burst():
 
    n_frames_per_burst = randrange(1,5)           
    return n_frames_per_burst
