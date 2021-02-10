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

#def arq_ack_timeout():
#    static.ARQ_ACK_TIMEOUT = 1

#def arq_rpt_timeout():
#    static.ARQ_RPT_TIMEOUT = True
    
def data_received(data_in):
    
    
#            arqframe = frame_type + \                                    # 1 [:1]  # frame type and current number of arq frame of (current) burst 
#                       bytes([static.ARQ_TX_N_FRAMES_PER_BURST]) + \     # 1 [1:2] # total number of arq frames per (current) burst 
#                       static.ARQ_N_CURRENT_ARQ_FRAME + \                # 2 [2:4] # current arq frame number 
#                       static.ARQ_N_TOTAL_ARQ_FRAMES + \                 # 2 [4:6] # total number arq frames 
#                       static.ARQ_BURST_PAYLOAD_CRC + \                  # 2 [6:8] # arq crc 
#                       payload_data                                      # N [8:N] # payload data 



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

        try:       
            static.ARQ_RX_FRAME_BUFFER[static.ARQ_RX_N_CURRENT_ARQ_FRAME] = bytes(data_in)                                       

        except IndexError:

            static.ARQ_RX_FRAME_BUFFER = []
            for i in range(0,static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME+1):
                static.ARQ_RX_FRAME_BUFFER.insert(i,None)
        
            static.ARQ_RX_FRAME_BUFFER[static.ARQ_RX_N_CURRENT_ARQ_FRAME] = bytes(data_in) 
            static.ARQ_FRAME_BOF_RECEIVED = False
            static.ARQ_FRAME_EOF_RECEIVED = False       

                        
        try:       
            static.ARQ_RX_BURST_BUFFER[static.ARQ_N_FRAME] = bytes(data_in)                              
                
        except IndexError:
            
            static.ARQ_RX_BURST_BUFFER = []
            for i in range(0,static.ARQ_N_RX_FRAMES_PER_BURSTS+1):
                static.ARQ_RX_BURST_BUFFER.insert(i,None)
                
            static.ARQ_RX_BURST_BUFFER[static.ARQ_N_FRAME] = bytes(data_in) 
                     
        #for i in range(len(static.ARQ_RX_BURST_BUFFER)):
        #    print(static.ARQ_RX_BURST_BUFFER[i])
              
# - ------------------------- ARQ BURST CHECKER
               
        # run only if we recieved all ARQ FRAMES per ARQ BURST
        if static.ARQ_RX_BURST_BUFFER.count(None) == 1: #count nones
            logging.info("ARQ | TX | BURST ACK")
            
            #BUILDING ACK FRAME FOR BURST ----------------------------------------------- 
            ack_payload = b'BURST_ACK'
            ack_frame = b'<' + ack_payload # < = 60   

            #TRANSMIT ACK FRAME FOR BURST-----------------------------------------------
            modem.transmit_arq_ack(ack_frame)
            
            #clear burst buffer
            static.ARQ_RX_BURST_BUFFER = []
        
        #if decoded N frames are unequal to expected frames per burst
        elif static.ARQ_N_FRAME == static.ARQ_N_RX_FRAMES_PER_BURSTS and static.ARQ_RX_BURST_BUFFER.count(None) != 1:
            
            # --------------- CHECK WHICH BURST FRAMES WE ARE MISSING -------------------------------------------
            
            missing_frames = b''
            for burstnumber in range(1,len(static.ARQ_RX_BURST_BUFFER)):
                
                if static.ARQ_RX_BURST_BUFFER[burstnumber] == None:
                    frame_number = burstnumber.to_bytes(2, byteorder='big')      
                    missing_frames += frame_number
                                
            logging.info("ARQ | TX | RPT ARQ FRAMES [" + str(missing_frames) + "]") 
            
            #BUILDING RPT FRAME FOR BURST -----------------------------------------------
            rpt_payload = missing_frames       
            rpt_frame = b'>' + rpt_payload #> = 63
        
            #TRANSMIT RPT FRAME FOR BURST-----------------------------------------------
            modem.transmit_arq_ack(rpt_frame)
            
         
            
# ---------------------------- FRAME MACHINE
       
        # ---------------  IF LIST NOT CONTAINS "None" stick everything together 
        complete_data_frame = bytearray()   
        #print("static.ARQ_RX_FRAME_BUFFER.count(None)" + str(static.ARQ_RX_FRAME_BUFFER.count(None)))
        if static.ARQ_RX_FRAME_BUFFER.count(None) == 1: ## 1 because position 0 of list will alaways be None in our case
            #print("DECODING FRAME!")
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
                 ack_payload = b'FRAME_ACK'
                 ack_frame = b'='+ ack_payload + bytes(static.FRAME_CRC) # < = 61                   
            
                #TRANSMIT ACK FRAME FOR BURST-----------------------------------------------
                 time.sleep(3) #0.5
                 logging.info("ARQ | TX | ARQ DATA FRAME ACK [" + str(static.FRAME_CRC.hex()) +"]")
                 
                 modem.transmit_arq_ack(ack_frame)

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
                

                
                
                    if static.ARQ_N_SENT_FRAMES + 1 <= static.TX_BUFFER_SIZE:
                        logging.info("ARQ | TX | F:[" + str(static.ARQ_N_SENT_FRAMES+1) + "-" + str(static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST) + "] | T:[" + str(static.ARQ_N_SENT_FRAMES) + "/" + str(static.TX_BUFFER_SIZE) + "] [" + str(int(static.ARQ_N_SENT_FRAMES/(static.TX_BUFFER_SIZE)*100)).zfill(3) + "%] | A:[" + str(static.TX_N_RETRIES+1) + "/" + str(static.TX_N_MAX_RETRIES) + "]")
                    
                                        
                    # lets start a thread to transmit nonblocking
                    TRANSMIT_ARQ_BURST_THREAD = threading.Thread(target=modem.transmit_arq_burst, name="TRANSMIT_ARQ_BURST")
                    TRANSMIT_ARQ_BURST_THREAD.start()
                    
                    # lets wait during sending. After sending is finished we will continue
                    while static.ARQ_STATE == 'SENDING_DATA':
                        time.sleep(0.01)
                        #print("sending.....")
                        
                    
                    # --------------------------- START TIMER FOR WAITING FOR ACK ---> IF TIMEOUT REACHED, ACK_TIMEOUT = 1
                                        #reset timer and ack state
                    #static.ARQ_FRAME_ACK_RECEIVED = False
                    #static.ARQ_ACK_RECEIVED = False
                    #static.ARQ_RX_ACK_TIMEOUT = False
                    
                    
                    logging.info("ARQ | RX | WAITING FOR BURST ACK")
                    static.ARQ_STATE = 'RECEIVING_SIGNALLING'
                       
                    helpers.arq_reset_timeout(False)
                    helpers.arq_reset_ack(False)
                            
                    acktimer = threading.Timer(static.ARQ_RX_ACK_TIMEOUT_SECONDS, helpers.arq_ack_timeout)
                    acktimer.start() 
                    
                    print(".............................")
                    print("static.ARQ_STATE " + str(static.ARQ_STATE))
                    print("static.ARQ_FRAME_ACK_RECEIVED " + str(static.ARQ_FRAME_ACK_RECEIVED))
                    print("static.ARQ_ACK_RECEIVED " + str(static.ARQ_ACK_RECEIVED))
                    print("static.ARQ_RX_ACK_TIMEOUT " + str(static.ARQ_RX_ACK_TIMEOUT))
                    print("static.ARQ_RPT_RECEIVED " + str(static.ARQ_RPT_RECEIVED))
                    print(".............................")

                    # --------------------------- WHILE TIMEOUT NOT REACHED AND NO ACK RECEIVED --> LISTEN
                    while static.ARQ_ACK_RECEIVED != True and static.ARQ_RPT_RECEIVED != True and static.ARQ_FRAME_ACK_RECEIVED != True and static.ARQ_RX_FRAME_TIMEOUT != True and static.ARQ_RX_ACK_TIMEOUT != True:
                        time.sleep(0.01) # lets reduce CPU load a little bit
                        print(static.ARQ_STATE)
                                            
                    if static.ARQ_RPT_RECEIVED == True:
                    
                        logging.info("ARQ | RX | REQUEST  FOR REPEATING FRAMES: " + str(static.ARQ_RPT_FRAMES))
                        logging.info("ARQ | TX | SENDING REQUESTED FRAMES: " + str(static.ARQ_RPT_FRAMES))                  
                        
                        TRANSMIT_ARQ_BURST_THREAD = threading.Thread(target=modem.transmit_arq_burst, name="TRANSMIT_ARQ_BURST")
                        TRANSMIT_ARQ_BURST_THREAD.start()
                        
                        # lets wait during sending. After sending is finished we will continue
                        while static.ARQ_STATE == 'SENDING_DATA':
                            time.sleep(0.01)
            
            
                        static.ARQ_STATE = 'RECEIVING_SIGNALLING'
             
                        helpers.arq_reset_timeout(False)
                        helpers.arq_reset_ack(False)
                    
                        rpttimer = threading.Timer(static.ARQ_RX_RPT_TIMEOUT_SECONDS, helpers.arq_rpt_timeout)
                        rpttimer.start() 
                    
                        while static.ARQ_ACK_RECEIVED == False and static.ARQ_FRAME_ACK_RECEIVED == False and static.ARQ_RX_RPT_TIMEOUT == False:                 
                            time.sleep(0.01) # lets reduce CPU load a little bit
                            print(static.ARQ_STATE)
                            
                            if static.ARQ_ACK_RECEIVED == True:
                            
                                logging.info("ARQ | RX | ACK RECEIVED AFTER FRAME REPEAT")
                                
                                helpers.arq_reset_ack(True)
                                static.ARQ_RPT_FRAMES = []

                        if static.ARQ_RX_RPT_TIMEOUT == True and static.ARQ_ACK_RECEIVED == False:
                            print("Burst lost....")
                            
                            helpers.arq_reset_ack(False)
                            static.ARQ_RPT_FRAMES = []
                   
                   #--------------------------------------------------------------------------------------------------------------
                   
                    elif static.ARQ_ACK_RECEIVED == 0 and static.ARQ_RX_ACK_TIMEOUT == 1:
                        logging.info("ARQ | RX | ACK TIMEOUT - AND NO ACK!")
                        pass #no break here so we can continue with the next try of repeating the burst
                 
                    #--------------- BREAK LOOP IF ACK HAS BEEN RECEIVED
                    elif static.ARQ_ACK_RECEIVED == True:
                        logging.info("ARQ | RX | ACK RECEIVED")      
                        #-----------IF ACK RECEIVED, INCREMENT ITERATOR FOR MAIN LOOP TO PROCEED WITH NEXT FRAMES/BURST
                        static.ARQ_N_SENT_FRAMES = static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST
                        break
                        
                    #--------------- BREAK LOOP IF FRAME ACK HAS BEEN RECEIVED EARLIER AS EXPECTED
                    elif static.ARQ_FRAME_ACK_RECEIVED == True:
                        print("----------------------------------------------------------")
                        logging.info("ARQ | RX | EARLY FRAME ACK RECEIVED - STOPPING TX")
                        #static.ARQ_N_SENT_FRAMES = #static.TX_BUFFER_SIZE
                        static.ARQ_N_SENT_FRAMES = static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST
                        break
                        
                    else:
                        print("------------------------------->NO RULE MATCHED!")
                        break            
                        
                        
                #--------------------------------WAITING AREA FOR FRAME ACKs        
                
                print("static.ARQ_N_SENT_FRAMES " + str(static.ARQ_N_SENT_FRAMES))
                print("static.TX_BUFFER_SIZE    " + str(static.TX_BUFFER_SIZE))
                print("static.TX_N_RETRIES      " + str(static.TX_N_RETRIES))
                print("static.TX_N_MAX_RETRIES  " + str(static.TX_N_MAX_RETRIES))
                          
                print("static.ARQ_STATE " + str(static.ARQ_STATE))
                print("static.ARQ_FRAME_ACK_RECEIVED " + str(static.ARQ_FRAME_ACK_RECEIVED))
                print("static.ARQ_RX_FRAME_TIMEOUT " + str(static.ARQ_RX_FRAME_TIMEOUT))
                print("static.ARQ_ACK_RECEIVED " + str(static.ARQ_ACK_RECEIVED))
                print("static.ARQ_RX_ACK_TIMEOUT " + str(static.ARQ_RX_ACK_TIMEOUT))
                print("static.ARQ_RPT_RECEIVED " + str(static.ARQ_RPT_RECEIVED))     
                
                
                frametimer = threading.Timer(static.ARQ_RX_FRAME_TIMEOUT_SECONDS, helpers.arq_frame_timeout)
                frametimer.start()
                static.ARQ_STATE = 'RECEIVING_SIGNALLING'
                
                # wait for frame ACK if we processed the last frame/burst
                while static.ARQ_FRAME_ACK_RECEIVED == False and static.ARQ_RX_FRAME_TIMEOUT == False and static.ARQ_N_SENT_FRAMES == static.TX_BUFFER_SIZE:                 
                        time.sleep(0.01) # lets reduce CPU load a little bit
                        #print(static.ARQ_STATE) 
                        print("WAITING FOR FRAME ACK")

              
                             
                # ----------- if no ACK received and out of retries.....stop frame sending
                if static.ARQ_ACK_RECEIVED == False and static.ARQ_FRAME_ACK_RECEIVED == False and static.ARQ_RX_ACK_TIMEOUT == True:
                        logging.info("ARQ | TX | NO BURST OR FRAME ACK RECEIVED | DATA SHOULD BE RESEND!")
                        break

                #-------------------------BREAK TX BUFFER LOOP IF ALL PACKETS HAVE BEEN SENT AND WE GOT A FRAME ACK
                elif static.ARQ_N_SENT_FRAMES == static.TX_BUFFER_SIZE and static.ARQ_FRAME_ACK_RECEIVED == True:
                    logging.info("ARQ | RX | REGULAR FRAME ACK RECEIVED - DATA TRANSMITTED!")
                    break 
 
                else:
                    print("NO MATCHING RULE AT THE END")
                    
                        
            # IF TX BUFFER IS EMPTY / ALL FRAMES HAVE BEEN SENT --> HERE WE COULD ADD AN static.VAR for IDLE STATE    
            
            logging.info("ARQ | TX | BUFFER EMPTY")
            helpers.arq_reset_frame_machine()





           
# BURST MACHINE TO DEFINE N BURSTS PER FRAME    ---> LATER WE CAN USE CHANNEL MESSUREMENT TO SET FRAMES PER BURST         
def get_n_frames_per_burst():
 
    #n_frames_per_burst = randrange(1,10)
    n_frames_per_burst = 4          
    return n_frames_per_burst
    
    
    
def burst_ack_received():
    
    logging.info("ARQ | RX | BURST ACK RCVD!")
    #static.ARQ_RX_ACK_TIMEOUT = True #Force timer to stop waiting
    static.ARQ_ACK_RECEIVED = True #Force data loops of TNC to stop and continue with next frame
    
    #static.ARQ_RX_RPT_TIMEOUT = True #Force timer to stop waiting
    #static.ARQ_RPT_RECEIVED = False
    #static.ARQ_RPT_FRAMES = []
    

def frame_ack_received():
    
    logging.info("ARQ | RX | FRAME ACK RCVD!")
    #static.ARQ_RX_ACK_TIMEOUT = True #Force timer to stop waiting
    static.ARQ_FRAME_ACK_RECEIVED = True #Force data loops of TNC to stop and continue with next frame
    
    #static.ARQ_RX_RPT_TIMEOUT = True #Force timer to stop waiting
    #static.ARQ_RPT_RECEIVED = False
    #static.ARQ_RPT_FRAMES = []   
    

def burst_rpt_received(data_in):
    
    logging.info("ARQ | RX | BURST RPT RCVD!")
    #static.ARQ_RX_ACK_TIMEOUT = False #Force timer to stop waiting
    #static.ARQ_ACK_RECEIVED = False #Force data loops of TNC to stop and continue with next frame

    #static.ARQ_RX_RPT_TIMEOUT = True
    static.ARQ_RPT_RECEIVED = True
    static.ARQ_RPT_FRAMES = []
    
    missing_area = bytes(data_in[1:9])
    
    for i in range(0,6,2):     
        if not missing_area[i:i+2].endswith(b'\x00\x00'):
            missing = missing_area[i:i+2]
            static.ARQ_RPT_FRAMES.insert(0,missing)
    
