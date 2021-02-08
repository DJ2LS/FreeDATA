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
import main


modem = modem.RF()

static.ARQ_PAYLOAD_PER_FRAME = static.FREEDV_DATA_PAYLOAD_PER_FRAME - 3 #6?!
static.ARQ_ACK_PAYLOAD_PER_FRAME = 14 - 2#

def arq_ack_timeout():
    static.ARQ_ACK_TIMEOUT = 1

def arq_rpt_timeout():
    static.ARQ_RPT_TIMEOUT = True
    
def data_received(data_in):
    
    
#            arqframe = frame_type + \                                    # 1 [:1]  # frame type and current number of arq frame of (current) burst 
#                       bytes([static.ARQ_TX_N_FRAMES_PER_BURST]) + \     # 1 [1:2] # total number of arq frames per (current) burst 
#                       static.ARQ_N_CURRENT_ARQ_FRAME + \                # 2 [2:4] # current arq frame number 
#                       static.ARQ_N_TOTAL_ARQ_FRAMES + \                 # 2 [4:6] # total number arq frames 
#                       static.ARQ_BURST_PAYLOAD_CRC + \                  # 2 [6:8] # arq crc 
#                       payload_data                                      # N [8:N] # payload data 


        # detect if we got a RPT frame
        if int.from_bytes(bytes(data_in[:1]), "big") == 51:
            frame_type = int.from_bytes(bytes(data_in[:1]), "big")
        else:
            frame_type = 10
            static.ARQ_N_FRAME = int.from_bytes(bytes(data_in[:1]), "big")  - 10 #get number of burst frame
         
        static.ARQ_N_RX_FRAMES_PER_BURSTS = int.from_bytes(bytes(data_in[1:2]), "big") #get number of bursts from received frame
        static.ARQ_RX_N_CURRENT_ARQ_FRAME = int.from_bytes(bytes(data_in[2:4]), "big") #get current number of total frames
        static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME = int.from_bytes(bytes(data_in[4:6]), "big") # get get total number of frames
        static.ARQ_BURST_PAYLOAD_CRC = data_in[6:8]
        
        
        logging.debug("----------------------------------------------------------------")
        logging.debug("ARQ_N_FRAME: " + str(static.ARQ_N_FRAME))
        logging.debug("ARQ_N_RX_FRAMES_PER_BURSTS: " + str(static.ARQ_N_RX_FRAMES_PER_BURSTS))
        logging.debug("ARQ_RX_N_CURRENT_ARQ_FRAME: " + str(static.ARQ_RX_N_CURRENT_ARQ_FRAME))
        logging.debug("ARQ_N_ARQ_FRAMES_PER_DATA_FRAME: " + str(static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME))
        logging.debug("static.ARQ_BURST_PAYLOAD_CRC: " + str(static.ARQ_BURST_PAYLOAD_CRC))
        logging.debug("----------------------------------------------------------------")

        
        arq_percent_burst = int((static.ARQ_N_FRAME / static.ARQ_N_RX_FRAMES_PER_BURSTS)*100)
        arq_percent_frame = int(((static.ARQ_RX_N_CURRENT_ARQ_FRAME)/static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME)*100)      
        
        logging.info("ARQ | RX | ARQ FRAME [" + str(static.ARQ_N_FRAME) + "/" + str(static.ARQ_N_RX_FRAMES_PER_BURSTS) + "] [" + str(arq_percent_burst).zfill(3) + "%] --- TOTAL [" + str(static.ARQ_RX_N_CURRENT_ARQ_FRAME) + "/" + str(static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME) + "] [" + str(arq_percent_frame).zfill(3) + "%]" )
    

    
        #allocate ARQ_RX_FRAME_BUFFER as a list with "None" if not already done. This should be done only once per burst!
        # here we will save the N frame of a data frame to N list position so we can explicit search for it
        if static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME != len(static.ARQ_RX_FRAME_BUFFER) and static.ARQ_RX_N_CURRENT_ARQ_FRAME == 1:
            static.ARQ_RX_FRAME_BUFFER = []
            for i in range(0,static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME+1):
                static.ARQ_RX_FRAME_BUFFER.insert(i,None)
                
        #allocate ARQ_RX_BURST_BUFFER as a list with "None" if not already done. This should be done only once per burst!
        # here we will save the N frame of a burst to N list position so we can explicit search for it
        print(len(static.ARQ_RX_BURST_BUFFER))
        print(static.ARQ_N_FRAME)
        
        
        if static.ARQ_N_RX_FRAMES_PER_BURSTS != len(static.ARQ_RX_BURST_BUFFER) and static.ARQ_N_FRAME == 1 and frame_type != 51:
            static.ARQ_RX_BURST_BUFFER = []
            print("ITERATOR!!!!!!!!!!!!!!")
            for i in range(0,static.ARQ_N_RX_FRAMES_PER_BURSTS+1):
                static.ARQ_RX_BURST_BUFFER.insert(i,None)
            
 
        # now we add the incoming data to the specified position in our lists
        static.ARQ_RX_BURST_BUFFER[static.ARQ_N_FRAME] = bytes(data_in) 
        static.ARQ_RX_FRAME_BUFFER[static.ARQ_RX_N_CURRENT_ARQ_FRAME] = bytes(data_in)  
    
        for i in range(len(static.ARQ_RX_BURST_BUFFER)):
            print(static.ARQ_RX_BURST_BUFFER[i])
        
        
        
              
# - ------------------------- ARQ BURST CHECKER
               
        # run only if we recieved all ARQ FRAMES per ARQ BURST
        #if static.ARQ_N_FRAME == static.ARQ_N_RX_FRAMES_PER_BURSTS and static.ARQ_RX_BURST_BUFFER.count(None) == 1: #if received bursts are equal to burst number in frame
        if static.ARQ_RX_BURST_BUFFER.count(None) == 1: #count nones
            logging.info("ARQ | TX | BURST ACK")
            
            #BUILDING ACK FRAME FOR BURST ----------------------------------------------- 
            ack_payload = b'ACK FRAME'
            ack_frame = b'<' + ack_payload # < = 60   
            ack_buffer = bytearray(static.ARQ_ACK_PAYLOAD_PER_FRAME) 
            ack_buffer[:len(ack_frame)] = ack_frame # set buffersize to length of data which will be send        
            
            #TRANSMIT ACK FRAME FOR BURST-----------------------------------------------
            modem.transmit_arq_ack(ack_buffer)
            
            #clear burst buffer
            static.ARQ_RX_BURST_BUFFER = []
        
        #if decoded N frames are unequal to expected frames per burst
        elif static.ARQ_N_FRAME == static.ARQ_N_RX_FRAMES_PER_BURSTS and static.ARQ_RX_BURST_BUFFER.count(None) != 1:
            print("RPT FRAME NEEDS TO BE SEND!!!!")
            # --------------- CHECK WHICH BURST FRAMES WE ARE MISSING -------------------------------------------
            
            missing_frames = b''
            for burst in range(1,len(static.ARQ_RX_BURST_BUFFER)):
                
                if static.ARQ_RX_BURST_BUFFER[burst] == None:
                    print(burst)
                    burst = burst.to_bytes(2, byteorder='big')      
                    missing_frames += burst
                    
            
            print("MISSING FRAMES: " + str(missing_frames)) 
            
            rpt_payload = missing_frames       
            rpt_frame = b'>' + rpt_payload #> = 63
            rpt_buffer = bytearray(static.ARQ_ACK_PAYLOAD_PER_FRAME) 
            rpt_buffer[:len(rpt_frame)] = rpt_frame # set buffersize to length of data which will be send      
        
            modem.transmit_arq_ack(rpt_buffer)
            
            
            
            
            
            
            
            
            
            
            
# ---------------------------- FRAME MACHINE
        
        # --------------- CHECK IF WE ARE MISSING FRAMES -------------------------------------------
        #for frame in range(1,len(static.ARQ_RX_FRAME_BUFFER)):
        #    if static.ARQ_RX_FRAME_BUFFER[frame] == None:
        #        print("Missing frames:" + str(frame))
        
        # ---------------  IF LIST NOT CONTAINS "None" stick everything together 
        complete_data_frame = bytearray()   
        print("static.ARQ_RX_FRAME_BUFFER.count(None)" + str(static.ARQ_RX_FRAME_BUFFER.count(None)))
        if static.ARQ_RX_FRAME_BUFFER.count(None) == 1: ## 1 because position 0 of list will alaways be None in our case
            print("DECODING FRAME!")
            for frame in range(1,len(static.ARQ_RX_FRAME_BUFFER)):
                raw_arq_frame = static.ARQ_RX_FRAME_BUFFER[frame]
                arq_frame_payload = raw_arq_frame[8:]
                
                # -------- DETECT IF WE RECEIVED A FRAME HEADER THEN SAVE DATA TO GLOBALS
                if arq_frame_payload[2:4].startswith(static.FRAME_BOF):
                    static.FRAME_CRC = arq_frame_payload[:2]
                    static.ARQ_FRAME_BOF_RECEIVED = True
                    
                    arq_frame_payload = arq_frame_payload.split(static.FRAME_BOF)
                    arq_frame_payload = arq_frame_payload[1]
                    
                # -------- DETECT IF WE RECEIVED A FRAME FOOTER THEN SAVE DATA TO GLOBALS    
                if arq_frame_payload.rstrip(b'\x00').endswith(static.FRAME_EOF):
                    static.ARQ_FRAME_EOF_RECEIVED = True
                    
                    arq_frame_payload = arq_frame_payload.split(static.FRAME_EOF)
                    arq_frame_payload = arq_frame_payload[0]
                    

                # --------- AFTER WE SEPARATED BOF AND EOF, STICK EVERYTHING TOGETHER  
                complete_data_frame = complete_data_frame + arq_frame_payload

            
        #check if Begin of Frame BOF and End of Frame EOF are received, then start calculating CRC and sticking everything together
        if static.ARQ_FRAME_BOF_RECEIVED == True and static.ARQ_FRAME_EOF_RECEIVED == True:
        
            frame_payload_crc = helpers.get_crc_16(complete_data_frame)
          
            #IF THE FRAME PAYLOAD CRC IS EQUAL TO THE FRAME CRC WHICH IS KNOWN FROM THE HEADER --> SUCCESS      
            if frame_payload_crc == static.FRAME_CRC:
                 logging.info("ARQ | RX | DATA FRAME SUCESSFULLY RECEIVED! - TIME TO PARTY")
                 #append received frame to RX_BUFFER
                 static.RX_BUFFER.append(complete_data_frame)
          
                #BUILDING ACK FRAME FOR DATA FRAME -----------------------------------------------              
                
                 ack_frame = b'='+ bytes(static.FRAME_CRC) # < = 61   
                 ack_buffer = bytearray(static.ARQ_ACK_PAYLOAD_PER_FRAME) 
                 ack_buffer[:len(ack_frame)] = ack_frame # set buffersize to length of data which will be send                 
            
                #TRANSMIT ACK FRAME FOR BURST-----------------------------------------------
                 logging.info("ARQ | TX | ARQ DATA FRAME ACK [" + str(static.FRAME_CRC.hex()) +"]")
                 modem.transmit_arq_ack(ack_buffer)

                 # clearing buffers and resetting counters
                 static.ARQ_RX_BURST_BUFFER = []
                 static.ARQ_RX_FRAME_BUFFER = []
                 static.ARQ_FRAME_BOF_RECEIVED = False
                 static.ARQ_FRAME_EOF_RECEIVED = False
                 static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME = 0
                 
                 #print("----------------------------------------------------------------")
                 #print(static.RX_BUFFER[-1])                 
                 #print("----------------------------------------------------------------")
                 
            else:
                logging.info("ARQ | RX | DATA FRAME NOT SUCESSFULLY RECEIVED!")
    
        #break

def burst_ack_received():
    
    logging.info("ARQ | RX | BURST ACK RCVD!")
    static.ARQ_ACK_TIMEOUT = 1 #Force timer to stop waiting
    static.ARQ_ACK_RECEIVED = 1 #Force data loops of TNC to stop and continue with next frame
    static.RPT_ACK_RECEIVED = False
    
def burst_rpt_received(data_in):
    
    logging.info("ARQ | RX | BURST RPT RCVD!")
    static.ARQ_ACK_TIMEOUT = 0 #Force timer to stop waiting
    static.ARQ_ACK_RECEIVED = 0 #Force data loops of TNC to stop and continue with next frame
    static.ARQ_RPT_RECEIVED = True
    #static.ARQ_RPT_FRAMES = b'123'
    missing = 3
    missing = missing.to_bytes(2, byteorder='big')
    static.ARQ_RPT_FRAMES.insert(0,missing)
    
    print(bytes(data_in))


def frame_ack_received():
    
    logging.info("ARQ | RX | FRAME ACK RCVD!")
    static.ARQ_ACK_TIMEOUT = 1 #Force timer to stop waiting
    static.ARQ_FRAME_ACK_RECEIVED = 1 #Force data loops of TNC to stop and continue with next frame


def transmit(data_out):

            static.ARQ_PAYLOAD_PER_FRAME = static.FREEDV_DATA_PAYLOAD_PER_FRAME - 8 #3 ohne ARQ_TX_N_FRAMES_PER_BURST  
            frame_header_length = 4
                        
            n_arq_frames_per_data_frame = (len(data_out)+frame_header_length) // static.ARQ_PAYLOAD_PER_FRAME + ((len(data_out)+frame_header_length) % static.ARQ_PAYLOAD_PER_FRAME > 0) 
            
            frame_payload_crc = helpers.get_crc_16(data_out)

            # This is the total frame with frame header, which will be send
            data_out =  frame_payload_crc + static.FRAME_BOF + data_out + static.FRAME_EOF
            #                     2                 2              N           2
            
            # --------------------------------------------- LETS CREATE A BUFFER BY SPLITTING THE FILES INTO PEACES
            static.TX_BUFFER = [data_out[i:i+static.ARQ_PAYLOAD_PER_FRAME] for i in range(0, len(data_out), static.ARQ_PAYLOAD_PER_FRAME)]
            static.TX_BUFFER_SIZE = len(static.TX_BUFFER)
            
            logging.info("ARQ | TX | DATA FRAME --- BYTES: " + str(len(data_out)) + " ARQ FRAMES: " + str(static.TX_BUFFER_SIZE))
                      
            # --------------------------------------------- THIS IS THE MAIN LOOP-----------------------------------------------------------------
   
            static.ARQ_N_SENT_FRAMES = 0 # SET N SENT FRAMES TO 0 FOR A NEW SENDING CYCLE
            while static.ARQ_N_SENT_FRAMES <= static.TX_BUFFER_SIZE:

                static.ARQ_TX_N_FRAMES_PER_BURST = get_n_frames_per_burst()
                           
                # ----------- CREATE FRAME TOTAL PAYLOAD TO BE ABLE TO CREATE CRC FOR IT
                
                try: # DETECT IF LAST BURST TO PREVENT INDEX ERROR OF BUFFER
                    
                    for i in range(static.ARQ_TX_N_FRAMES_PER_BURST): # Loop through TX_BUFFER LIST
                        len(static.TX_BUFFER[static.ARQ_N_SENT_FRAMES + i]) #we calculate the length to trigger a list index error                                    
                
                except IndexError: # IF LAST BURST DETECTED BUILD CRC WITH LESS FRAMES AND SET static.ARQ_TX_N_FRAMES_PER_BURST TO VALUE OF REST!
                     
                     if static.ARQ_N_SENT_FRAMES == 0  and (static.ARQ_TX_N_FRAMES_PER_BURST > static.TX_BUFFER_SIZE): #WE CANT DO MODULO 0 --> CHECK IF FIRST FRAME == LAST FRAME
                          static.ARQ_TX_N_FRAMES_PER_BURST = static.TX_BUFFER_SIZE
                     
                     elif static.ARQ_N_SENT_FRAMES == 1 and (static.ARQ_TX_N_FRAMES_PER_BURST > static.TX_BUFFER_SIZE): # MODULO 1 WILL ALWAYS BE 0 --> THIS FIXES IT
                            static.ARQ_TX_N_FRAMES_PER_BURST = static.TX_BUFFER_SIZE - static.ARQ_N_SENT_FRAMES  
                     
                     else:
                         static.ARQ_TX_N_FRAMES_PER_BURST = (static.TX_BUFFER_SIZE % static.ARQ_N_SENT_FRAMES)
                
                
                #--------------------------------------------- N ATTEMPTS TO SEND BURSTS IF ACK RECEPTION FAILS
                for static.TX_N_RETRIES in range(static.TX_N_MAX_RETRIES):
                
                    if static.ARQ_N_SENT_FRAMES+1 <= static.TX_BUFFER_SIZE:
                        logging.info("ARQ | TX | F:[" + str(static.ARQ_N_SENT_FRAMES+1) + "-" + str(static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST) + "] | T:[" + str(static.ARQ_N_SENT_FRAMES) + "/" + str(static.TX_BUFFER_SIZE) + "] [" + str(int(static.ARQ_N_SENT_FRAMES/(static.TX_BUFFER_SIZE)*100)).zfill(3) + "%] | A:[" + str(static.TX_N_RETRIES+1) + "/" + str(static.TX_N_MAX_RETRIES) + "]")
                    
                                        
                    # lets start a thread to transmit nonblocking
                    TRANSMIT_ARQ_BURST_THREAD = threading.Thread(target=modem.transmit_arq_burst, name="TRANSMIT_ARQ_BURST")
                    TRANSMIT_ARQ_BURST_THREAD.start()
                    
                    # lets wait during sending. After sending is finished we will continue
                    while static.ARQ_STATE == 'SENDING_DATA':
                        time.sleep(0.05)
                        
                        
                    # --------------------------- START TIMER FOR WAITING FOR ACK ---> IF TIMEOUT REACHED, ACK_TIMEOUT = 1
                                        #reset timer and ack state
                    static.ARQ_FRAME_ACK_RECEIVED = 0
                    static.ARQ_ACK_RECEIVED = 0
                    static.ARQ_ACK_TIMEOUT = 0
                    
                    logging.debug("ARQ | RX | WAITING FOR BURST ACK")
                    static.ARQ_STATE = 'RECEIVING_ACK'
                            
                    timer = threading.Timer(static.ARQ_ACK_TIMEOUT_SECONDS, arq_ack_timeout)
                    timer.start() 

                    # --------------------------- WHILE TIMEOUT NOT REACHED AND NO ACK RECEIVED --> LISTEN
                    while static.ARQ_ACK_TIMEOUT == 0 and static.ARQ_RPT_RECEIVED == False and static.ARQ_ACK_RECEIVED == 0:                 
                        time.sleep(0.01) # lets reduce CPU load a little bit
                        #print(static.ARQ_STATE)
                                        
                    #--------------------------------------------------------------------------------------------------------------
                                           
                    if static.ARQ_RPT_RECEIVED == True:
                        print("lets send a rpt packet")                       
                        TRANSMIT_ARQ_BURST_THREAD = threading.Thread(target=modem.transmit_arq_burst, name="TRANSMIT_ARQ_BURST")
                        TRANSMIT_ARQ_BURST_THREAD.start()
                        # lets wait during sending. After sending is finished we will continue
                        while static.ARQ_STATE == 'SENDING_DATA':
                            time.sleep(0.05)
            
                        static.ARQ_FRAME_ACK_RECEIVED = 0
                        static.ARQ_ACK_RECEIVED = 0
                        static.ARQ_ACK_TIMEOUT = 0
                    
                        static.ARQ_STATE = 'RECEIVING_ACK'
                  
                        timer = threading.Timer(static.ARQ_RPT_TIMEOUT_SECONDS, arq_rpt_timeout)
                        timer.start() 
                        print("kommen wir hier überhaupt an?") 
                        while static.ARQ_ACK_TIMEOUT == 0 and static.ARQ_ACK_RECEIVED == 0  and static.ARQ_RPT_TIMEOUT == False:                 
                            time.sleep(0.01) # lets reduce CPU load a little bit
                            print("waiting for ack while rpt")
                            if static.ARQ_ACK_RECEIVED == 1:
                            
                                print("ACK WHILE RPT")
                                time.sleep(1)
                                static.ARQ_ACK_TIMEOUT = 1
                                static.ARQ_RPT_RECEIVED = False
                                static.ARQ_RPT_TIMEOUT == False
                                
                                break                   
                   
                   #--------------------------------------------------------------------------------------------------------------
                   
                    if static.ARQ_ACK_RECEIVED == 0 and static.ARQ_ACK_TIMEOUT == 1 and static.ARQ_RPT_TIMEOUT == True:
                        #logging.info("ARQ | RX | ACK TIMEOUT | SENDING ARQ BURST AGAIN")
                        pass
                 
                    #--------------- BREAK LOOP IF ACK HAS BEEN RECEIVED OR FRAME ACK HAS BEEN RECEIVED
                    if static.ARQ_ACK_RECEIVED == 1:
                        print("der interator increment ist wichtig!")                     
                        #-----------IF ACK RECEIVED, INCREMENT ITERATOR FOR MAIN LOOP TO PROCEED WITH NEXT FRAMES/BURST
                        static.ARQ_N_SENT_FRAMES = static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST
                        break
                        
                    #--------------- BREAK LOOP IF FRAME ACK HAS BEEN RECEIVED EARLIER AS EXPECTED
                    if static.ARQ_FRAME_ACK_RECEIVED == 1:
                        logging.info("ARQ | RX | EARLY FRAME ACK RECEIVED - STOPPING TX")
                        #static.ARQ_N_SENT_FRAMES = #static.TX_BUFFER_SIZE
                        static.ARQ_N_SENT_FRAMES = static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST
                        break
                 
                # ----------- if no ACK received and out of retries.....stop frame sending
                if static.ARQ_ACK_RECEIVED == 0 and static.ARQ_FRAME_ACK_RECEIVED == 0 and static.ARQ_ACK_TIMEOUT == 1:
                        logging.info("ARQ | TX | NO BURST OR FRAME ACK RECEIVED | DATA SHOULD BE RESEND!")
                        
                        break

                #-------------------------BREAK TX BUFFER LOOP IF ALL PACKETS HAVE BEEN SENT AND WE GOT A FRAME ACK
                if static.ARQ_N_SENT_FRAMES == static.TX_BUFFER_SIZE and static.ARQ_FRAME_ACK_RECEIVED == 1:
                    logging.info("ARQ | RX | REGULAR FRAME ACK RECEIVED - DATA TRANSMITTED!")
                    break 

                        
            # IF TX BUFFER IS EMPTY / ALL FRAMES HAVE BEEN SENT --> HERE WE COULD ADD AN static.VAR for IDLE STATE    
            
            logging.info("ARQ | TX | BUFFER EMPTY")
            # - RESET COUNTERS
            static.ARQ_N_SENT_FRAMES = 0
            static.ARQ_TX_N_FRAMES_PER_BURST = 0
            static.ARQ_ACK_RECEIVED = 0
            static.ARQ_FRAME_ACK_RECEIVED = 0
           
# BURST MACHINE TO DEFINE N BURSTS PER FRAME    ---> LATER WE CAN USE CHANNEL MESSUREMENT TO SET FRAMES PER BURST         
def get_n_frames_per_burst():
 
    #n_frames_per_burst = randrange(1,10)
    n_frames_per_burst = 4          
    return n_frames_per_burst
