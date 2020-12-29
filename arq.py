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
import time

import static
import modem
import other


modem = modem.RF()

crc_algorithm = crcengine.new('crc16-ccitt-false') #load crc16 library 

static.ARQ_PAYLOAD_PER_FRAME = static.FREEDV_PAYLOAD_PER_FRAME - 6



def data_received(data_in):
    
        ARQ_N_RX_BURSTS = int.from_bytes(bytes(data_in[:1]), "big")  - 10
        static.ARQ_RX_BUFFER.append(data_in) #append data to RX BUFFER 
    
        print(ARQ_N_RX_BURSTS)
    
    
    
    
    #while static.ACK_RX_TIMEOUT == 0: #define timeout where data has to be received untl error occurs
    
        if len(static.ARQ_RX_BUFFER) == ARQ_N_RX_BURSTS: #if received bursts are equal to burst number in frame
        
            burst_total_payload = bytearray()
            for n_raw_frame in range(0,len(static.ARQ_RX_BUFFER)):
            
                burst_frame = static.ARQ_RX_BUFFER[n_raw_frame] #get burst frame
                burst_payload = burst_frame[3:] #remove frame type and burst CRC        
                burst_total_payload = burst_total_payload + burst_payload #stick bursts together
            
            print(burst_total_payload)    
            burst_payload_crc = crc_algorithm(burst_total_payload)
            burst_payload_crc = burst_payload_crc.to_bytes(2, byteorder='big')    
            print(burst_payload_crc)     
        
        
            if burst_payload_crc == data_in[1:3]: #IF burst payload crc and input crc are equal
        
                print(data_in[1:3])
                print("CRC EQUAL")
                logging.info("TX | SENDING ACK [" + str(data_in[1:3]) +"]")
            
            #BUILDING ACK FRAME -----------------------------------------------
            
                ack_frame = b'\7' + bytes(burst_payload_crc)
                ack_buffer = bytearray(static.ARQ_PAYLOAD_PER_FRAME) 
                ack_buffer[:len(ack_frame)] = ack_frame # set buffersize to length of data which will be send                 
            
            #TRANSMIT ACK FRAME -----------------------------------------------
                time.sleep(2)
                modem.Transmit(ack_buffer)
                static.ARQ_RX_BUFFER = []
            
            else: #IF burst payload crc and input crc are NOT equal
                print("CRC NOT EQUAL!!!!!")
                print(data_in[1:3])
                static.ARQ_RX_BUFFER = [] 


def ack_received():
    
    logging.info("TX | ACK RCVD!")
    static.ACK_TIMEOUT = 1 #Force timer to stop waiting
    static.ACK_RECEIVED = 1 #Force data loops of TNC to stop and continue with next frame
    # static.ARQ_ACK_WAITING_FOR_ID
    
  



def transmit(data_out):
        
            static.ARQ_PAYLOAD_PER_FRAME = static.FREEDV_PAYLOAD_PER_FRAME - 3
        
            static.TX_BUFFER = [data_out[i:i+static.ARQ_PAYLOAD_PER_FRAME] for i in range(0, len(data_out), static.ARQ_PAYLOAD_PER_FRAME)] # split incomming bytes to size of 30bytes - arq payload
            static.TX_BUFFER_SIZE = len(static.TX_BUFFER)
            
            static.ARQ_TX_N_FRAMES = n_frames_per_burst(len(data_out)) # DEFINE NUMBER OF FRAMES PER BURSTS
            
            logging.info("TX | TOTAL PAYLOAD BYTES/FRAMES TO SEND: " + str(len(data_out)) + " / " + str(static.TX_BUFFER_SIZE))
            
            #print(static.TX_BUFFER[2])
            
            for n_raw_frame in range(0, static.TX_BUFFER_SIZE, static.ARQ_TX_N_FRAMES): # LOOP THROUGH DATA LIST with steps = ARQ_TX_N_FRAMES
                print("N_RAW_FRAME: " + str(n_raw_frame))           
                
                ## check, if we have to adjust burst frames
                #if (n_raw_frame % static.TX_BUFFER_SIZE) != 0:
                #    static.ARQ_TX_N_FRAMES = (n_raw_frame % static.TX_BUFFER_SIZE)
                #    print(static.ARQ_TX_N_FRAMES)
      
        
      
                # ----------- GENERATE PAYLOAD CRC FOR ARQ_TX_N_FRAMES
                burst_total_payload = bytearray()
                

                #----------------------------------------------------------------------------------------------------------
                try: # DETECT IF LAST BURST
                    for i in range(static.ARQ_TX_N_FRAMES): #bytearray(b'111111111111111111111111222222222222222222222222')

                # we need to make sure, payload data is always as long as static.ARQ_PAYLOAD_PER_FRAME beacuse of CRC!                      

                        burst_raw_payload = static.TX_BUFFER[n_raw_frame + i]                   
                        burst_payload = bytearray(static.ARQ_PAYLOAD_PER_FRAME) 
                        burst_payload[:len(burst_raw_payload)] = burst_raw_payload # set buffersize to length of data which will be send        
                        burst_total_payload = burst_total_payload + burst_payload
                 
                except IndexError: # IF LAST BURST DETECTED BUILD CRC WITH LESS FRAMES AND SET static.ARQ_TX_N_FRAMES TO VALUE OF REST!
                     print("LAST BURST!!!")
                     burst_total_payload = bytearray() # reset burst_total_payload because of possible input remaining of detecting loop one step above
                     n_last_burst = (static.TX_BUFFER_SIZE % n_raw_frame)
                     print(n_last_burst)
                     static.ARQ_TX_N_FRAMES = n_last_burst
                     
                     for i in range(n_last_burst): #bytearray(b'111111111111111111111111222222222222222222222222')
                     
                        burst_raw_payload = static.TX_BUFFER[n_raw_frame + i]                   
                        burst_payload = bytearray(static.ARQ_PAYLOAD_PER_FRAME) 
                        burst_payload[:len(burst_raw_payload)] = burst_raw_payload # set buffersize to length of data which will be send        
                        burst_total_payload = burst_total_payload + burst_payload
                     
                 #----------------------------------------------------------------------------------------------------------    
                     
                print(burst_total_payload)
                
                burst_payload_crc = crc_algorithm(burst_total_payload)
                burst_payload_crc = burst_payload_crc.to_bytes(2, byteorder='big')
                
                print(burst_payload_crc)
                static.ARQ_ACK_WAITING_FOR_ID = burst_payload_crc #set the global variable so we know for which ACK we are waiting for
                
                
                
                
                #----------------------------------------------------------------------------------------------------------
                #-------------------- BUILD ARQBURSTS

                arqburst = []
                for i in range(static.ARQ_TX_N_FRAMES):
                    

                        frame_type = 10 + static.ARQ_TX_N_FRAMES
                        frame_type = bytes([frame_type])
                    
                        payload_data = bytes(static.TX_BUFFER[n_raw_frame + i])
                    
                        arqframe = frame_type + burst_payload_crc + payload_data
                    
                        buffer = bytearray(static.FREEDV_PAYLOAD_PER_FRAME) # create TX buffer 
                        buffer[:len(arqframe)] = arqframe # set buffersize to length of data which will be send
                          
                        arqburst.append(buffer)

                #----------------------------------------------------------------------------------------------------------


                #--------------------------------------------- N ATTEMPTS TO SEND BURSTS IF ACK FAILS
                for static.TX_N_RETRIES in range(static.TX_N_MAX_RETRIES):
                    
                    static.ACK_RECEIVED = 0
                    
                    # ----------------------- Loop through ARQ FRAMES BUFFER with N = Numbers of frames which will be send at once
                    
                    for n in range(static.ARQ_TX_N_FRAMES):
                        logging.info("TX | SENDING BURST " + str(n+1) + " / " + str(static.ARQ_TX_N_FRAMES))
                        modem.Transmit(arqburst[n])
                        time.sleep(2)
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
                
                # ------------ TIMER TO WAIT UNTIL NEXT PACKAGE WILL BE SEND TO PREVENT TIME ISSEUS
                time.sleep(5)
                        
            logging.info("TX | BUFFER EMPTY")
            
            
            
            
# BURST MACHINE TO DEFINE N BURSTS PER FRAME            
def n_frames_per_burst(len_data):
    
    if len_data <= static.ARQ_PAYLOAD_PER_FRAME:
        n_frames_per_burst = 1
    else:
        n_frames_per_burst = 3
    
    
    return n_frames_per_burst 