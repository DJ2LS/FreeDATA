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
import asyncio
import sys

import static
import modem
import helpers
modem = modem.RF()

'''
Author: DJ2LS
Description:
data_handler is a module like file, which handles all the ARQ related parts.
Because of the fact, that we need to use it from both directions,
socket.py and modem.py ( TX and RX ), I was not able, to move it to a class system, yet.
Global variables are needed, because we need to save our ack state for example, which needs to 
be accessable by several functions.
If we want to use global varialbes within a multithreaded environment,
we need to declare every needed variable in every function, so the threading module can 
detect and use them.

From time to time I try to reduce the amount of application wide variables within static. module
and moving them to module wide globals

'''

# MODULE GLOBALS

DATA_CHANNEL_READY_FOR_DATA     =   False       # Indicator if we are ready for sending or receiving data
DATA_CHANNEL_LAST_RECEIVED      =   0.0         # time of last "live sign" of a frame      
DATA_CHANNEL_MODE               =   0           # mode for data channel

BURST_ACK_RECEIVED              =   False       # if we received an acknowledge frame for a burst
DATA_FRAME_ACK_RECEIVED         =   False       # if we received an acknowledge frame for a data frame
RPT_REQUEST_RECEIVED            =   False       # if we received an request for repeater frames
RPT_REQUEST_BUFFER              =   []          # requested frames, saved in a list
      
RX_START_OF_TRANSMISSION        =   0           # time of transmission start

# ################################################
# ARQ DATA HANDLER
# ################################################    

def arq_data_received(data_in, bytes_per_frame):
    # we neeed to declare our global variables, so the thread has access to them
    global RX_START_OF_TRANSMISSION
    global DATA_CHANNEL_LAST_RECEIVED
    global DATA_CHANNEL_READY_FOR_DATA
    
    # only process data if we are in ARQ and BUSY state else return to quit
    if static.ARQ_STATE != 'DATA' and static.TNC_STATE != 'BUSY':
        return
    
    # these vars will be overwritten during processing data
    RX_FRAME_BOF_RECEIVED = False       # here we save, if we received a "beginn of (data)frame"
    RX_FRAME_EOF_RECEIVED = False       # here we save, if we received a "end of (data)frame"
    DATA_FRAME_BOF                  =   b'\xAA\xAA' # 2 bytes for the BOF End of File indicator in a data frame
    DATA_FRAME_EOF                  =   b'\xFF\xFF' # 2 bytes for the EOF End of File indicator in a data frame

    
    RX_PAYLOAD_PER_MODEM_FRAME = bytes_per_frame - 2    # payload per moden frame
    RX_PAYLOAD_PER_ARQ_FRAME = RX_PAYLOAD_PER_MODEM_FRAME - 8   # payload per arq frame

    static.TNC_STATE = 'BUSY'
    static.ARQ_STATE = 'DATA'
    DATA_CHANNEL_LAST_RECEIVED = int(time.time())
        
    RX_N_FRAME_OF_BURST         = int.from_bytes(bytes(data_in[:1]), "big") - 10  # get number of burst frame
    RX_N_FRAMES_PER_BURST       = int.from_bytes(bytes(data_in[1:2]), "big")  # get number of bursts from received frame
    RX_N_FRAME_OF_DATA_FRAME    = int.from_bytes(bytes(data_in[2:4]), "big")  # get current number of total frames
    RX_N_FRAMES_PER_DATA_FRAME  = int.from_bytes(bytes(data_in[4:6]), "big")  # get total number of frames
    static.TOTAL_BYTES = RX_N_FRAMES_PER_DATA_FRAME * RX_PAYLOAD_PER_ARQ_FRAME # calculate total bytes
   
    arq_percent_burst = int((RX_N_FRAME_OF_BURST / RX_N_FRAMES_PER_BURST) * 100)
    #arq_percent_frame = int(((RX_N_FRAME_OF_DATA_FRAME) / RX_N_FRAMES_PER_DATA_FRAME) * 100)
    calculate_transfer_rate_rx(RX_N_FRAMES_PER_DATA_FRAME, RX_N_FRAME_OF_DATA_FRAME, RX_START_OF_TRANSMISSION, RX_PAYLOAD_PER_ARQ_FRAME)
    
    logging.log(24, "ARQ | RX | " + str(DATA_CHANNEL_MODE) + " | F:[" + str(RX_N_FRAME_OF_BURST) + "/" + str(RX_N_FRAMES_PER_BURST) + "] [" + str(arq_percent_burst).zfill(3) + "%] T:[" + str(RX_N_FRAME_OF_DATA_FRAME) + "/" + str(RX_N_FRAMES_PER_DATA_FRAME) + "] [" + str(int(static.ARQ_TRANSMISSION_PERCENT)).zfill(3) + "%] [SNR:" + str(static.SNR) + "]")

    
    # allocate ARQ_static.RX_FRAME_BUFFER as a list with "None" if not already done. This should be done only once per burst!
    # here we will save the N frame of a data frame to N list position so we can explicit search for it
    
    # delete frame buffer if first frame to make sure the buffer is cleared and no junks of a old frame is remaining
    # normally this shouldn't appear, since we are doing a buffer cleanup after every frame processing
    # but better doing this, to avoid problems caused by old chunks in data
    if RX_N_FRAME_OF_DATA_FRAME == 1:
        static.RX_FRAME_BUFFER = []
    #    
    #    # we set the start of transmission - 7 seconds, which is more or less the transfer time for the first frame
    #    RX_START_OF_TRANSMISSION = time.time() - 7
    #    calculate_transfer_rate()
    
    #try appending data to frame buffer    
    try:
        static.RX_FRAME_BUFFER[RX_N_FRAME_OF_DATA_FRAME] = bytes(data_in)
        
    except IndexError:
        # we are receiving new data, so we are doing a cleanup first
        static.RX_FRAME_BUFFER = []

        # set the start of transmission - 7 seconds,
        # which is more or less the transfer time for the first frame
        RX_START_OF_TRANSMISSION = time.time() - 6
                              
        for i in range(0, RX_N_FRAMES_PER_DATA_FRAME + 1):
            static.RX_FRAME_BUFFER.insert(i, None)

        static.RX_FRAME_BUFFER[RX_N_FRAME_OF_DATA_FRAME] = bytes(data_in)

    #if RX_N_FRAME_OF_BURST == 1:
    #    static.ARQ_START_OF_BURST = time.time() - 6
        
        
    # try appending data to burst buffer
    try:
        static.RX_BURST_BUFFER[RX_N_FRAME_OF_BURST] = bytes(data_in)
        
    except IndexError:

        static.RX_BURST_BUFFER = []
       
        for i in range(0, RX_N_FRAMES_PER_BURST + 1):
            static.RX_BURST_BUFFER.insert(i, None)

        static.RX_BURST_BUFFER[RX_N_FRAME_OF_BURST] = bytes(data_in)

# - ------------------------- ARQ BURST CHECKER
    # run only if we recieved all ARQ FRAMES per ARQ BURST 
    # and we didnt receive the last burst of a data frame
    # if we received the last burst of a data frame, we can directly send a frame ack to 
    # improve transfer rate
    if static.RX_BURST_BUFFER.count(None) == 1 and RX_N_FRAMES_PER_DATA_FRAME != RX_N_FRAME_OF_DATA_FRAME :  # count nones
        logging.info("ARQ | TX | BURST ACK")

        # BUILDING ACK FRAME FOR BURST -----------------------------------------------
        ack_frame = bytearray(14)
        ack_frame[:1] = bytes([60])
        ack_frame[1:2] = static.DXCALLSIGN_CRC8
        ack_frame[2:3] = static.MYCALLSIGN_CRC8


        # TRANSMIT ACK FRAME FOR BURST-----------------------------------------------
        helpers.wait(0.3)
        while not modem.transmit_signalling(ack_frame, 1):
        #while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
            time.sleep(0.01)
            
        static.CHANNEL_STATE = 'RECEIVING_DATA'
        # clear burst buffer
        static.RX_BURST_BUFFER = []

    # if decoded N frames are unequal to expected frames per burst
    elif RX_N_FRAME_OF_BURST == RX_N_FRAMES_PER_BURST and static.RX_BURST_BUFFER.count(None) != 1:

        # --------------- CHECK WHICH BURST FRAMES WE ARE MISSING -------------------------------------------
        missing_frames = b''
        for burstnumber in range(1, len(static.RX_BURST_BUFFER)):

            if static.RX_BURST_BUFFER[burstnumber] == None:
                logging.debug("RX_N_FRAME_OF_DATA_FRAME" + str(RX_N_FRAME_OF_DATA_FRAME))
                logging.debug("ARQ_N_RX_FRAMES_PER_BURSTS" + str(RX_N_FRAMES_PER_BURST))

                frame_number = burstnumber
                frame_number = frame_number.to_bytes(2, byteorder='big')
                missing_frames += frame_number

        logging.warning("ARQ | TX | RPT ARQ FRAMES [" + str(missing_frames) + "] [SNR:" + str(static.SNR) + "]")

        # BUILDING RPT FRAME FOR BURST -----------------------------------------------
        rpt_frame       = bytearray(14)
        rpt_frame[:1]   = bytes([62])
        rpt_frame[1:2]  = static.DXCALLSIGN_CRC8
        rpt_frame[2:3]  = static.MYCALLSIGN_CRC8
        rpt_frame[3:9]  = missing_frames

        # TRANSMIT RPT FRAME FOR BURST-----------------------------------------------
        while not modem.transmit_signalling(rpt_frame, 1):
            time.sleep(0.01)
        static.CHANNEL_STATE = 'RECEIVING_DATA'

# ---------------------------- FRAME MACHINE
    # ---------------  IF LIST NOT CONTAINS "None" stick everything together
    complete_data_frame = bytearray()
    if static.RX_FRAME_BUFFER.count(None) == 1:  # 1 because position 0 of list will alaways be None in our case
        logging.debug("DECODING FRAME!")
        for frame in range(1, len(static.RX_FRAME_BUFFER)):
            raw_arq_frame = static.RX_FRAME_BUFFER[frame]
            arq_frame_payload = raw_arq_frame[8:]

            # -------- DETECT IF WE RECEIVED A FRAME HEADER THEN SAVE DATA TO GLOBALS
            if arq_frame_payload[2:4].startswith(DATA_FRAME_BOF):
                data_frame_crc = arq_frame_payload[:2]
                RX_FRAME_BOF_RECEIVED = True

                arq_frame_payload = arq_frame_payload.split(DATA_FRAME_BOF)
                arq_frame_payload = arq_frame_payload[1]
                logging.debug("BOF")


            # -------- DETECT IF WE RECEIVED A FRAME FOOTER THEN SAVE DATA TO GLOBALS
            # we need to check for at least one xFF. Sometimes we have only one xFF, because the second one is in the next frame
            if arq_frame_payload.rstrip(b'\x00').endswith(DATA_FRAME_EOF) or arq_frame_payload.rstrip(b'\x00').endswith(DATA_FRAME_EOF[:-1]):
                RX_FRAME_EOF_RECEIVED = True
                if arq_frame_payload.rstrip(b'\x00').endswith(DATA_FRAME_EOF[:-1]):
                    arq_frame_payload = arq_frame_payload.split(DATA_FRAME_EOF[:-1])
                    arq_frame_payload = arq_frame_payload[0]
                else:
                    arq_frame_payload = arq_frame_payload.split(DATA_FRAME_EOF)
                    arq_frame_payload = arq_frame_payload[0]
                logging.debug("EOF")

            # --------- AFTER WE SEPARATED BOF AND EOF, STICK EVERYTHING TOGETHER
            complete_data_frame = complete_data_frame + arq_frame_payload
            logging.debug(complete_data_frame)

    # check if Begin of Frame BOF and End of Frame EOF are received, then start calculating CRC and sticking everything together
    if RX_FRAME_BOF_RECEIVED and RX_FRAME_EOF_RECEIVED:

        frame_payload_crc = helpers.get_crc_16(complete_data_frame)

        # IF THE FRAME PAYLOAD CRC IS EQUAL TO THE FRAME CRC WHICH IS KNOWN FROM THE HEADER --> SUCCESS
        if frame_payload_crc == data_frame_crc:
            logging.log(25, "ARQ | RX | DATA FRAME SUCESSFULLY RECEIVED! :-) ")
            calculate_transfer_rate_rx(RX_N_FRAMES_PER_DATA_FRAME, RX_N_FRAME_OF_DATA_FRAME, RX_START_OF_TRANSMISSION, RX_PAYLOAD_PER_ARQ_FRAME)
            # append received frame to RX_BUFFER
            static.RX_BUFFER.append([static.DXCALLSIGN,static.DXGRID,int(time.time()), complete_data_frame.decode("utf-8")])

            # BUILDING ACK FRAME FOR DATA FRAME -----------------------------------------------
            ack_frame       = bytearray(14)
            ack_frame[:1]   = bytes([61])
            ack_frame[1:2]  = static.DXCALLSIGN_CRC8
            ack_frame[2:3]  = static.MYCALLSIGN_CRC8

            # TRANSMIT ACK FRAME FOR BURST-----------------------------------------------
            logging.info("ARQ | TX | ARQ DATA FRAME ACK [" + str(data_frame_crc.hex()) + "] [SNR:" + str(static.SNR) + "]")

            # since simultaneous decoding it seems, we don't have to wait anymore
            # however, we will wait a little bit for easier ptt debugging
            # possibly we can remove this later
            helpers.wait(0.5)

            
            while not modem.transmit_signalling(ack_frame, 2):
                time.sleep(0.01)

            calculate_transfer_rate_rx(RX_N_FRAMES_PER_DATA_FRAME, RX_N_FRAME_OF_DATA_FRAME, RX_START_OF_TRANSMISSION, RX_PAYLOAD_PER_ARQ_FRAME)            
            
            #arq_reset_frame_machine()
            static.TNC_STATE = 'IDLE'
            static.ARQ_STATE = 'IDLE'
            DATA_CHANNEL_READY_FOR_DATA = False
            static.RX_BURST_BUFFER = []
            static.RX_FRAME_BUFFER = []
            
            logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]<< >>[" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")
            
        else:
            print("ARQ_FRAME_BOF_RECEIVED " + str(RX_FRAME_BOF_RECEIVED))
            print("ARQ_FRAME_EOF_RECEIVED " + str(RX_FRAME_EOF_RECEIVED))
            print(static.RX_FRAME_BUFFER)
            calculate_transfer_rate_rx(RX_N_FRAMES_PER_DATA_FRAME, RX_N_FRAME_OF_DATA_FRAME, RX_START_OF_TRANSMISSION, RX_PAYLOAD_PER_ARQ_FRAME)
            logging.error("ARQ | RX | DATA FRAME NOT SUCESSFULLY RECEIVED!")
            
            
            # STATE CLEANUP
            #arq_reset_frame_machine()
            static.TNC_STATE = 'IDLE'
            static.ARQ_STATE = 'IDLE'
            DATA_CHANNEL_READY_FOR_DATA = False
            static.RX_BURST_BUFFER = []
            static.RX_FRAME_BUFFER = []
            
            logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]<<X>>[" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")
    

def arq_transmit(data_out, mode, n_frames_per_burst):

    global RPT_REQUEST_BUFFER
    global DATA_FRAME_ACK_RECEIVED
    global RPT_REQUEST_RECEIVED
    global BURST_ACK_RECEIVED
    #global TX_START_OF_TRANSMISSION
    global DATA_CHANNEL_READY_FOR_DATA
    
    DATA_CHANNEL_MODE = mode
    
    DATA_FRAME_BOF                  =   b'\xAA\xAA' # 2 bytes for the BOF End of File indicator in a data frame
    DATA_FRAME_EOF                  =   b'\xFF\xFF' # 2 bytes for the EOF End of File indicator in a data frame

    TX_N_SENT_FRAMES                = 0                     # already sent frames per data frame
    TX_N_RETRIES_PER_BURST          = 0                     # retries we already sent data
    TX_N_MAX_RETRIES_PER_BURST      = 5                     # max amount of retries we sent before frame is lost
    TX_N_FRAMES_PER_BURST           = n_frames_per_burst    # amount of n frames per burst    
    TX_BUFFER = []  # our buffer for appending new data
    
    BURST_ACK_TIMEOUT_SECONDS       =   7.0         # timeout for burst  acknowledges
    DATA_FRAME_ACK_TIMEOUT_SECONDS  =   10.0        # timeout for data frame acknowledges
    RPT_ACK_TIMEOUT_SECONDS         =   10.0        # timeout for rpt frame acknowledges


    # we need to set payload per frame manually at this point. maybe we can do this more dynmic.
    if DATA_CHANNEL_MODE == 10:
        payload_per_frame = 512 - 2
    #elif DATA_CHANNEL_MODE == 11:
    #    payload_per_frame = 258 - 2
    elif DATA_CHANNEL_MODE == 12:
        payload_per_frame = 128 - 2
    elif DATA_CHANNEL_MODE == 14:
        payload_per_frame = 16 - 2
    else:
        payload_per_frame = 16 - 2

    
    TX_START_OF_TRANSMISSION = time.time()

    TX_PAYLOAD_PER_ARQ_FRAME = payload_per_frame - 8
    frame_header_length = 6

    #n_arq_frames_per_data_frame = (len(data_out) + frame_header_length) // TX_PAYLOAD_PER_ARQ_FRAME + ((len(data_out) + frame_header_length) % TX_PAYLOAD_PER_ARQ_FRAME > 0)

    frame_payload_crc = helpers.get_crc_16(data_out)

    # This is the total frame with frame header, which will be send
    data_out = frame_payload_crc + DATA_FRAME_BOF + data_out + DATA_FRAME_EOF
    #                     2                 2              N           2
    # save len of data_out to TOTAL_BYTES for our statistics
    static.TOTAL_BYTES = len(data_out)
    # --------------------------------------------- LETS CREATE A BUFFER BY SPLITTING THE FILES INTO PEACES
    TX_BUFFER = [data_out[i:i + TX_PAYLOAD_PER_ARQ_FRAME] for i in range(0, len(data_out), TX_PAYLOAD_PER_ARQ_FRAME)]
    TX_BUFFER_SIZE = len(TX_BUFFER)

    logging.info("ARQ | TX | M:" + str(DATA_CHANNEL_MODE) + " | DATA FRAME --- BYTES: " + str(len(data_out)) + " ARQ FRAMES: " + str(TX_BUFFER_SIZE))

    # ----------------------- THIS IS THE MAIN LOOP-----------------------------------------------------------------
    TX_N_SENT_FRAMES = 0  # SET N SENT FRAMES TO 0 FOR A NEW SENDING CYCLE
    while TX_N_SENT_FRAMES <= TX_BUFFER_SIZE and static.ARQ_STATE == 'DATA':

        # ----------- CREATE FRAME TOTAL PAYLOAD TO BE ABLE TO CREATE CRC FOR IT
        try:  # DETECT IF LAST BURST TO PREVENT INDEX ERROR OF BUFFER

            for i in range(TX_N_FRAMES_PER_BURST):  # Loop through TX_BUFFER LIST
                len(TX_BUFFER[TX_N_SENT_FRAMES + i])  # we calculate the length to trigger a list index error

        except IndexError:  # IF LAST BURST DETECTED BUILD CRC WITH LESS FRAMES AND SET TX_N_FRAMES_PER_BURST TO VALUE OF REST!

            if TX_N_SENT_FRAMES == 0 and (TX_N_FRAMES_PER_BURST > TX_BUFFER_SIZE):  # WE CANT DO MODULO 0 > CHECK IF FIRST FRAME == LAST FRAME
                TX_N_FRAMES_PER_BURST = TX_BUFFER_SIZE

            elif TX_N_SENT_FRAMES == 1 and (TX_N_FRAMES_PER_BURST > TX_BUFFER_SIZE):  # MODULO 1 WILL ALWAYS BE 0 --> THIS FIXES IT
                TX_N_FRAMES_PER_BURST = TX_BUFFER_SIZE - TX_N_SENT_FRAMES

            else:
                TX_N_FRAMES_PER_BURST = (TX_BUFFER_SIZE % TX_N_SENT_FRAMES)

        # --------------------------------------------- N ATTEMPTS TO SEND BURSTS IF ACK RECEPTION FAILS
        for TX_N_RETRIES_PER_BURST in range(TX_N_MAX_RETRIES_PER_BURST):

            if TX_N_SENT_FRAMES + 1 <= TX_BUFFER_SIZE:
                calculate_transfer_rate_tx(TX_N_SENT_FRAMES, TX_PAYLOAD_PER_ARQ_FRAME, TX_START_OF_TRANSMISSION, TX_BUFFER_SIZE) 
                logging.log(24, "ARQ | TX | M:" + str(DATA_CHANNEL_MODE) + " | F:[" + str(TX_N_SENT_FRAMES + 1) + "-" + str(TX_N_SENT_FRAMES + TX_N_FRAMES_PER_BURST) + "] | T:[" + str(TX_N_SENT_FRAMES) + "/" + str(TX_BUFFER_SIZE) + "] [" + str(int(static.ARQ_TRANSMISSION_PERCENT)).zfill(3) + "%] | A:[" + str(TX_N_RETRIES_PER_BURST + 1) + "/" + str(TX_N_MAX_RETRIES_PER_BURST) + "]")

            # lets refresh all timers and ack states before sending a new frame
            arq_reset_ack(False)

            
            # ---------------------------BUILD ARQ BURST ---------------------------------------------------------------------
            tempbuffer = []

            # we need to optimize this and doing frame building like the other frames with explicit possition
            # instead of just appending byte data
            for n in range(0, TX_N_FRAMES_PER_BURST):
                frame_type = 10 + n + 1
                frame_type = bytes([frame_type])
                payload_data = bytes(TX_BUFFER[TX_N_SENT_FRAMES + n])
                n_current_arq_frame = TX_N_SENT_FRAMES + n + 1
                n_current_arq_frame = n_current_arq_frame.to_bytes(2, byteorder='big')
                n_total_arq_frame = len(TX_BUFFER)
                #static.ARQ_TX_N_TOTAL_ARQ_FRAMES = n_total_arq_frame

                arqframe = frame_type + \
                    bytes([TX_N_FRAMES_PER_BURST]) + \
                    n_current_arq_frame + \
                    n_total_arq_frame.to_bytes(2, byteorder='big') + \
                    static.DXCALLSIGN_CRC8 + \
                    static.MYCALLSIGN_CRC8 + \
                    payload_data
            
                tempbuffer.append(arqframe)

            while not modem.transmit_arq_burst(DATA_CHANNEL_MODE, tempbuffer):
                time.sleep(0.01)
           
            ## lets wait during sending. After sending is finished we will continue
            #while static.CHANNEL_STATE == 'SENDING_DATA':
            #    time.sleep(0.01)

            # --------------------------- START TIMER FOR WAITING FOR ACK ---> IF TIMEOUT REACHED, ACK_TIMEOUT = 1

            logging.debug("ARQ | RX | WAITING FOR BURST ACK")
            static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'

            burstacktimeout = time.time() + BURST_ACK_TIMEOUT_SECONDS
            # --------------------------- WHILE TIMEOUT NOT REACHED AND NO ACK RECEIVED AND IN ARQ STATE--> LISTEN
            while not BURST_ACK_RECEIVED and not RPT_REQUEST_RECEIVED and not DATA_FRAME_ACK_RECEIVED and time.time() < burstacktimeout  and static.ARQ_STATE == 'DATA':
                time.sleep(0.01)  # lets reduce CPU load a little bit
                logging.debug(static.CHANNEL_STATE)

            # HERE WE PROCESS DATA IF WE RECEIVED ACK/RPT FRAMES OR NOT WHILE WE ARE IN ARQ STATE
            # IF WE ARE NOT IN ARQ STATE, WE STOPPED THE TRANSMISSION 
            if RPT_REQUEST_RECEIVED and static.ARQ_STATE == 'DATA':
                logging.warning("ARQ | RX | REQUEST FOR REPEATING FRAMES: " + str(RPT_REQUEST_BUFFER))
                logging.warning("ARQ | TX | SENDING REQUESTED FRAMES: " + str(RPT_REQUEST_BUFFER))

                # --------- BUILD RPT FRAME --------------
                tempbuffer = []
                for n in range(0, len(RPT_REQUEST_BUFFER)):
                    # we need to optimize this and doing frame building like the other frames with explicit possition
                    # instead of just appending byte data
                    missing_frame = int.from_bytes(RPT_REQUEST_BUFFER[n], "big")

                    frame_type = 10 + missing_frame  # static.ARQ_TX_N_FRAMES_PER_BURST
                    frame_type = bytes([frame_type])

                    try:
                        payload_data = bytes(TX_BUFFER[TX_N_SENT_FRAMES + missing_frame - 1])
                    except:
                        print("modem buffer selection problem with ARQ RPT frames")

                    n_current_arq_frame = TX_N_SENT_FRAMES + missing_frame
                    n_current_arq_frame = n_current_arq_frame.to_bytes(2, byteorder='big')

                    n_total_arq_frame = len(TX_BUFFER)


                    arqframe = frame_type + \
                        bytes([TX_N_FRAMES_PER_BURST]) + \
                        n_current_arq_frame + \
                        n_total_arq_frame.to_bytes(2, byteorder='big') + \
                        static.DXCALLSIGN_CRC8 + \
                        static.MYCALLSIGN_CRC8 + \
                        payload_data

                    tempbuffer.append(arqframe)
                
                while not modem.transmit_arq_burst(DATA_CHANNEL_MODE, tempbuffer):
                    time.sleep(0.01)
                
                # lets wait during sending. After sending is finished we will continue
                #while static.ARQ_STATE == 'SENDING_DATA':
                #    time.sleep(0.01)
                #static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'

                arq_reset_ack(False)

                rpttimeout = time.time() + RPT_ACK_TIMEOUT_SECONDS

                while not BURST_ACK_RECEIVED and not DATA_FRAME_ACK_RECEIVED and static.ARQ_STATE == 'DATA' and time.time() < rpttimeout:
                    time.sleep(0.01)  # lets reduce CPU load a little bit

                    if BURST_ACK_RECEIVED:
                        
                        logging.info("ARQ | RX | ACK AFTER RPT")
                        arq_reset_ack(True)
                        RPT_REQUEST_BUFFER = []
                        TX_N_SENT_FRAMES = TX_N_SENT_FRAMES + TX_N_FRAMES_PER_BURST

                if static.ARQ_RX_RPT_TIMEOUT and not BURST_ACK_RECEIVED:
                    logging.error("ARQ | Burst lost....")
                    arq_reset_ack(False)
                    RPT_REQUEST_BUFFER = []
 
            # the order of ACK check is important! speciall the FRAME ACK after RPT needs to be checked really early!

            # --------------- BREAK LOOP IF FRAME ACK HAS BEEN RECEIVED EARLIER AS EXPECTED
            elif DATA_FRAME_ACK_RECEIVED and static.ARQ_STATE == 'DATA':
                logging.info("ARQ | RX | EARLY FRAME ACK RECEIVED #2")

                TX_N_SENT_FRAMES = TX_N_SENT_FRAMES + TX_N_FRAMES_PER_BURST
                break

           # --------------------------------------------------------------------------------------------------------------
            elif not BURST_ACK_RECEIVED and static.ARQ_STATE == 'DATA':
                logging.warning("ARQ | RX | ACK TIMEOUT!")
                pass  # no break here so we can continue with the next try of repeating the burst


            # --------------- BREAK LOOP IF ACK HAS BEEN RECEIVED
            elif BURST_ACK_RECEIVED and static.ARQ_STATE == 'DATA':                
                # -----------IF ACK RECEIVED, INCREMENT ITERATOR FOR MAIN LOOP TO PROCEED WITH NEXT FRAMES/BURST
                TX_N_SENT_FRAMES = TX_N_SENT_FRAMES + TX_N_FRAMES_PER_BURST
                calculate_transfer_rate_tx(TX_N_SENT_FRAMES, TX_PAYLOAD_PER_ARQ_FRAME, TX_START_OF_TRANSMISSION, TX_BUFFER_SIZE)
                logging.info("ARQ | RX | ACK [" + str(static.ARQ_BITS_PER_SECOND) + " bit/s | " + str(static.ARQ_BYTES_PER_MINUTE) + " B/min]")
                # lets wait a little bit before we are processing the next frame
                helpers.wait(0.3)
                
                
                break

            else:
                logging.info("--->NO RULE MATCHED OR TRANSMISSION STOPPED!")
                print("ARQ_ACK_RECEIVED " + str(BURST_ACK_RECEIVED))
                break
                           
        # --------------------------------WAITING AREA FOR FRAME ACKs

        static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'

        frameacktimeout = time.time() + DATA_FRAME_ACK_TIMEOUT_SECONDS
        # wait for frame ACK if we processed the last frame/burst
        while not DATA_FRAME_ACK_RECEIVED and time.time() < frameacktimeout and TX_N_SENT_FRAMES == TX_BUFFER_SIZE:
            time.sleep(0.01)  # lets reduce CPU load a little bit
            logging.debug("WAITING FOR FRAME ACK")

        # ----------- if no ACK received and out of retries.....stop frame sending
        if not BURST_ACK_RECEIVED and not DATA_FRAME_ACK_RECEIVED:
            logging.error("ARQ | TX | NO ACK RECEIVED | DATA SHOULD BE RESEND!")
            break

        # -------------------------BREAK TX BUFFER LOOP IF ALL PACKETS HAVE BEEN SENT AND WE GOT A FRAME ACK
        elif TX_N_SENT_FRAMES == TX_BUFFER_SIZE and DATA_FRAME_ACK_RECEIVED:
            print(TX_N_SENT_FRAMES)
            calculate_transfer_rate_tx(TX_N_SENT_FRAMES, TX_PAYLOAD_PER_ARQ_FRAME, TX_START_OF_TRANSMISSION, TX_BUFFER_SIZE)
            logging.log(25, "ARQ | RX | FRAME ACK! - DATA TRANSMITTED! [" + str(static.ARQ_BITS_PER_SECOND) + " bit/s | " + str(static.ARQ_BYTES_PER_MINUTE) + " B/min]")
            break
            
        elif not DATA_FRAME_ACK_RECEIVED and time.time() > frameacktimeout:
            logging.error("ARQ | TX | NO FRAME ACK RECEIVED")
            break

        else:
            logging.debug("NO MATCHING RULE AT THE END")

    # IF TX BUFFER IS EMPTY / ALL FRAMES HAVE BEEN SENT --> HERE WE COULD ADD AN static.VAR for IDLE STATE
    #transfer_rates = calculate_transfer_rate()
    #logging.info("RATE (DATA/ACK) :[" + str(transfer_rates[0]) + " bit/s | " + str(transfer_rates[1]) + " B/min]")

    logging.info("ARQ | TX | BUFFER EMPTY")
    # we are doing some cleanup here
    static.TNC_STATE = 'IDLE'
    static.ARQ_STATE = 'IDLE'
    DATA_CHANNEL_READY_FOR_DATA = False
    #DATA_CHANNEL_LAST_RECEIVED = 0
    #BURST_ACK_RECEIVED = False
    #DATA_FRAME_ACK_RECEIVED = False
    
    logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]<< >>[" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")
    
    # this should close our thread so we are saving memory...
    # https://stackoverflow.com/questions/905189/why-does-sys-exit-not-exit-when-called-inside-a-thread-in-python
    sys.exit()




def burst_ack_received():
    global BURST_ACK_RECEIVED
    global DATA_CHANNEL_LAST_RECEIVED
    
    # only process data if we are in ARQ and BUSY state
    if static.ARQ_STATE == 'DATA' and static.TNC_STATE == 'BUSY':
        BURST_ACK_RECEIVED = True  # Force data loops of TNC to stop and continue with next frame
        DATA_CHANNEL_LAST_RECEIVED = int(time.time()) # we need to update our timeout timestamp


def frame_ack_received():
    global DATA_FRAME_ACK_RECEIVED
    global DATA_CHANNEL_LAST_RECEIVED

    # only process data if we are in ARQ and BUSY state
    if static.ARQ_STATE == 'DATA' and static.TNC_STATE == 'BUSY':
        
        DATA_FRAME_ACK_RECEIVED = True  # Force data loops of TNC to stop and continue with next frame
        DATA_CHANNEL_LAST_RECEIVED = int(time.time()) # we need to update our timeout timestamp


def burst_rpt_received(data_in):
    global RPT_REQUEST_RECEIVED
    global RPT_REQUEST_BUFFER
    global DATA_CHANNEL_LAST_RECEIVED
 
 
    # only process data if we are in ARQ and BUSY state
    if static.ARQ_STATE == 'DATA' and static.TNC_STATE == 'BUSY':
           
        RPT_REQUEST_RECEIVED = True
        DATA_CHANNEL_LAST_RECEIVED = int(time.time()) # we need to update our timeout timestamp
        RPT_REQUEST_BUFFER = []

        missing_area = bytes(data_in[3:12])  # 1:9

        for i in range(0, 6, 2):
            if not missing_area[i:i + 2].endswith(b'\x00\x00'):
                missing = missing_area[i:i + 2]
                RPT_REQUEST_BUFFER.insert(0, missing)

# ############################################################################################################
# ARQ DATA CHANNEL HANDLER
# ############################################################################################################


def open_dc_and_transmit(data_out, mode, n_frames_per_burst):
    global DATA_CHANNEL_READY_FOR_DATA
       
    asyncio.run(arq_open_data_channel(mode))
    # wait until data channel is open
    while not DATA_CHANNEL_READY_FOR_DATA:
        time.sleep(0.01)

    # lets wait a little bit so RX station is ready for receiving
    #wait_before_data_timer = time.time() + 0.8
    #while time.time() < wait_before_data_timer:
    #    pass    
    helpers.wait(0.8)
    
               
    # transmit data    
    arq_transmit(data_out, mode, n_frames_per_burst)
    

async def arq_open_data_channel(mode):

    global DATA_CHANNEL_READY_FOR_DATA
    global DATA_CHANNEL_LAST_RECEIVED
    
    DATA_CHANNEL_MAX_RETRIES        =   3           # N attempts for connecting to another station
    
    DATA_CHANNEL_MODE = int(mode)    
    DATA_CHANNEL_LAST_RECEIVED = int(time.time())

    connection_frame        = bytearray(14)
    connection_frame[:1]    = bytes([225])
    connection_frame[1:2]   = static.DXCALLSIGN_CRC8
    connection_frame[2:3]   = static.MYCALLSIGN_CRC8
    connection_frame[3:9]   = static.MYCALLSIGN
    connection_frame[12:13] = bytes([DATA_CHANNEL_MODE])

    while not DATA_CHANNEL_READY_FOR_DATA:
        time.sleep(0.01)
        for attempt in range(1,DATA_CHANNEL_MAX_RETRIES+1):
            logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>> <<[" + str(static.DXCALLSIGN, 'utf-8') + "] A:[" + str(attempt) + "/" + str(DATA_CHANNEL_MAX_RETRIES) + "]")
            while not modem.transmit_signalling(connection_frame, 1):
                time.sleep(0.01)
                   
            timeout = time.time() + 3    
            while time.time() < timeout:    
                time.sleep(0.01)
                # break if data channel is openend    
                if DATA_CHANNEL_READY_FOR_DATA:
                    break
            if DATA_CHANNEL_READY_FOR_DATA:
                break
            print("attempt:" + str(attempt) + "/" + str(DATA_CHANNEL_MAX_RETRIES))
            
            if not DATA_CHANNEL_READY_FOR_DATA and attempt == DATA_CHANNEL_MAX_RETRIES:
                logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>>X<<[" + str(static.DXCALLSIGN, 'utf-8') + "]")
                static.TNC_STATE = 'IDLE'
                static.ARQ_STATE = 'IDLE'
                sys.exit() # close thread and so connection attempts


def arq_received_data_channel_opener(data_in):
    
    #global DATA_CHANNEL_MODE
    global DATA_CHANNEL_LAST_RECEIVED
    
    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')
    helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'DATA-CHANNEL', static.SNR)
        
    logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>> <<[" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")
    
    static.ARQ_STATE = 'DATA'
    static.TNC_STATE = 'BUSY'

    mode = int.from_bytes(bytes(data_in[12:13]), "big")
    DATA_CHANNEL_LAST_RECEIVED = int(time.time())

    connection_frame = bytearray(14)
    connection_frame[:1] = bytes([226])
    connection_frame[1:2] = static.DXCALLSIGN_CRC8
    connection_frame[2:3] = static.MYCALLSIGN_CRC8
    connection_frame[3:9] = static.MYCALLSIGN
    connection_frame[12:13] = bytes([mode])

    while not modem.transmit_signalling(connection_frame, 1):
        time.sleep(0.01)

    logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "] [M:"+str(mode)+"] SNR:" + str(static.SNR) + "]")

    static.CHANNEL_STATE = 'RECEIVING_DATA'
    # and now we are going to "RECEIVING_DATA" mode....


def arq_received_channel_is_open(data_in):

    global DATA_CHANNEL_LAST_RECEIVED
    global DATA_CHANNEL_READY_FOR_DATA
    global DATA_CHANNEL_MODE
    
    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')
    helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'DATA-CHANNEL', static.SNR)
    
    DATA_CHANNEL_LAST_RECEIVED = int(time.time())

    # we are doing a mode check here, but this doesn't seem to be necessary since we have simultaneous decoding
    # we are forcing doing a transmission at the moment --> see else statement
    if DATA_CHANNEL_MODE == int.from_bytes(bytes(data_in[12:13]), "big"):
        logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")
        
        # wait a little bit so other station is ready ( PTT toggle )
        print("wait.....")
        print(time.time())
        helpers.wait(0.5)
        print(time.time())
        # as soon as we set ARQ_STATE to DATA, transmission starts   
        static.ARQ_STATE = 'DATA'
        DATA_CHANNEL_READY_FOR_DATA = True
        DATA_CHANNEL_LAST_RECEIVED = int(time.time())
    else:
        print("wrong mode received...")
        helpers.wait(0.5)
        # as soon as we set ARQ_STATE to DATA, transmission starts
        static.ARQ_STATE = 'DATA'
        DATA_CHANNEL_READY_FOR_DATA = True
        DATA_CHANNEL_LAST_RECEIVED = int(time.time())

# ############################################################################################################
# PING HANDLER
# ############################################################################################################

def transmit_ping(callsign):
    static.DXCALLSIGN = bytes(callsign, 'utf-8').rstrip(b'\x00')
    static.DXCALLSIGN_CRC8 = helpers.get_crc_8(static.DXCALLSIGN)
    logging.info("PING [" + str(static.MYCALLSIGN, 'utf-8') + "] >>> [" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")

    ping_frame      = bytearray(14)
    ping_frame[:1]  = bytes([210])
    ping_frame[1:2] = static.DXCALLSIGN_CRC8
    ping_frame[2:3] = static.MYCALLSIGN_CRC8
    ping_frame[3:9] = static.MYCALLSIGN

    # wait while sending....
    while not modem.transmit_signalling(ping_frame, 1):
        time.sleep(0.01)


def received_ping(data_in):

    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')
    helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'PING', static.SNR)
    logging.info("PING [" + str(static.MYCALLSIGN, 'utf-8') + "] <<< [" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")

    ping_frame      = bytearray(14)
    ping_frame[:1]  = bytes([211])
    ping_frame[1:2] = static.DXCALLSIGN_CRC8
    ping_frame[2:3] = static.MYCALLSIGN_CRC8
    ping_frame[3:9] = static.MYGRID

    # wait while sending....
    while not modem.transmit_signalling(ping_frame, 1):
        time.sleep(0.01)


def received_ping_ack(data_in):

    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXGRID = bytes(data_in[3:9]).rstrip(b'\x00')
       
    helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'PING-ACK', static.SNR)
    
    logging.info("PING [" + str(static.MYCALLSIGN, 'utf-8') + "] >|< [" + str(static.DXCALLSIGN, 'utf-8') + "]["+ str(static.DXGRID, 'utf-8') +"] [SNR:" + str(static.SNR) + "]")
    static.TNC_STATE = 'IDLE'

# ############################################################################################################
# BROADCAST HANDLER
# ############################################################################################################

def transmit_cq():
    logging.info("CQ CQ CQ")

    cq_frame       = bytearray(14)
    cq_frame[:1]   = bytes([200])
    cq_frame[1:2]  = b'\x01'
    #cq_frame[2:3] = static.MYCALLSIGN_CRC8
    #cq_frame[3:9] = static.MYCALLSIGN
    cq_frame[2:8]  = static.MYCALLSIGN
    cq_frame[8:14] = static.MYGRID
    
    while not modem.transmit_signalling(cq_frame, 3):
        time.sleep(0.01)


def received_cq(data_in):
    # here we add the received station to the heard stations buffer
    dxcallsign = bytes(data_in[2:8]).rstrip(b'\x00')
    dxgrid = bytes(data_in[8:14]).rstrip(b'\x00')
    
    logging.info("CQ RCVD [" + str(dxcallsign, 'utf-8') + "]["+ str(dxgrid, 'utf-8') +"] [SNR" + str(static.SNR) + "]")
    helpers.add_to_heard_stations(dxcallsign,dxgrid, 'CQ CQ CQ', static.SNR)


def arq_reset_ack(state):
    """
    Author: DJ2LS
    """
    global BURST_ACK_RECEIVED
    global RPT_REQUEST_RECEIVED
    global DATA_FRAME_ACK_RECEIVED
    
    BURST_ACK_RECEIVED = state
    RPT_REQUEST_RECEIVED = state
    DATA_FRAME_ACK_RECEIVED = state


def calculate_transfer_rate_rx(rx_n_frames_per_data_frame, rx_n_frame_of_data_frame, rx_start_of_transmission, rx_payload_per_arq_frame):
    try:      
        static.ARQ_TRANSMISSION_PERCENT = int((rx_n_frame_of_data_frame / rx_n_frames_per_data_frame) * 100)
        
        transmissiontime = time.time() - rx_start_of_transmission
        receivedbytes = rx_n_frame_of_data_frame * (rx_payload_per_arq_frame-6) # 6 = length of ARQ header
        
        static.ARQ_BITS_PER_SECOND = int((receivedbytes*8) / transmissiontime)
        static.ARQ_BYTES_PER_MINUTE = int((receivedbytes) / (transmissiontime/60))
    
    except:
        static.ARQ_TRANSMISSION_PERCENT = 0.0
        static.ARQ_BITS_PER_SECOND = 0
        static.ARQ_BYTES_PER_MINUTE = 0

    return [static.ARQ_BITS_PER_SECOND, \
        static.ARQ_BYTES_PER_MINUTE, \
        static.ARQ_TRANSMISSION_PERCENT]




def calculate_transfer_rate_tx(tx_n_sent_frames, tx_payload_per_arq_frame, tx_start_of_transmission, tx_buffer_length):
    try:
        static.ARQ_TRANSMISSION_PERCENT = int((tx_n_sent_frames / tx_buffer_length) * 100)
        
        transmissiontime = time.time() - tx_start_of_transmission
        if tx_n_sent_frames > 0:
            sendbytes = tx_n_sent_frames * (tx_payload_per_arq_frame-6) #6 = length of ARQ header
            
            static.ARQ_BITS_PER_SECOND = int((sendbytes*8) / transmissiontime)
            static.ARQ_BYTES_PER_MINUTE = int((sendbytes) / (transmissiontime/60))

        else:
            static.ARQ_BITS_PER_SECOND = 0
            static.ARQ_BYTES_PER_MINUTE = 0            
           
    except:
        static.ARQ_TRANSMISSION_PERCENT = 0.0
        static.ARQ_BITS_PER_SECOND = 0
        static.ARQ_BYTES_PER_MINUTE = 0

       
    return [static.ARQ_BITS_PER_SECOND, \
        static.ARQ_BYTES_PER_MINUTE, \
        static.ARQ_TRANSMISSION_PERCENT]



































# WATCHDOG FUNCTIONS
def watchdog():
    """
    Author: DJ2LS

    watchdog master function. Frome here we call the watchdogs
    """
    while True:
        time.sleep(0.01)
        data_channel_keep_alive_watchdog()


def data_channel_keep_alive_watchdog():
    """
    Author: DJ2LS

    """
    global DATA_CHANNEL_LAST_RECEIVED

    # and not static.ARQ_SEND_KEEP_ALIVE:
    if static.ARQ_STATE == 'DATA' and static.TNC_STATE == 'BUSY':
        time.sleep(0.01)
        if DATA_CHANNEL_LAST_RECEIVED + 30 > time.time():
            time.sleep(0.01)
            #pass
        else:
            DATA_CHANNEL_LAST_RECEIVED = 0
            logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]<<T>>[" + str(static.DXCALLSIGN, 'utf-8') + "] [BER." + str(static.BER) + "]")
            #arq_reset_frame_machine()  
            static.TNC_STATE = 'IDLE'
            static.ARQ_STATE = 'IDLE'

# START THE THREAD FOR THE TIMEOUT WATCHDOG
WATCHDOG_SERVER_THREAD = threading.Thread(target=watchdog, name="watchdog")
WATCHDOG_SERVER_THREAD.start()  





              

