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


# ############################################################################################################
# ARQ DATA HANDLER
# ############################################################################################################


def arq_data_received(data_in):
    # define some frame sizes so we can calculate the baud rate e.g.
    if static.ARQ_DATA_CHANNEL_MODE == 10:
        payload_per_frame = 512 - 2
    elif static.ARQ_DATA_CHANNEL_MODE == 11:
        payload_per_frame = 258 - 2
    elif static.ARQ_DATA_CHANNEL_MODE == 12:
        payload_per_frame = 128 - 2
    elif static.ARQ_DATA_CHANNEL_MODE == 14:
        payload_per_frame = 16 - 2
    else:
        payload_per_frame = 16 - 2

    static.ARQ_PAYLOAD_PER_FRAME = payload_per_frame - 8
 
    # 
    static.TNC_STATE = 'BUSY'
    static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time())
       
    
    static.ARQ_N_FRAME = int.from_bytes(bytes(data_in[:1]), "big") - 10  # get number of burst frame
    static.ARQ_N_RX_FRAMES_PER_BURSTS = int.from_bytes(bytes(data_in[1:2]), "big")  # get number of bursts from received frame
    static.ARQ_RX_N_CURRENT_ARQ_FRAME = int.from_bytes(bytes(data_in[2:4]), "big")  # get current number of total frames
    static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME = int.from_bytes(bytes(data_in[4:6]), "big")  # get get total number of frames

    logging.debug("----------------------------------------------------------------")
    logging.debug("ARQ_N_FRAME: " + str(static.ARQ_N_FRAME))
    logging.debug("ARQ_N_RX_FRAMES_PER_BURSTS: " + str(static.ARQ_N_RX_FRAMES_PER_BURSTS))
    logging.debug("ARQ_RX_N_CURRENT_ARQ_FRAME: " + str(static.ARQ_RX_N_CURRENT_ARQ_FRAME))
    logging.debug("ARQ_N_ARQ_FRAMES_PER_DATA_FRAME: " + str(static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME))
    logging.debug("----------------------------------------------------------------")

    arq_percent_burst = int((static.ARQ_N_FRAME / static.ARQ_N_RX_FRAMES_PER_BURSTS) * 100)
    arq_percent_frame = int(((static.ARQ_RX_N_CURRENT_ARQ_FRAME) / static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME) * 100)

    logging.log(24, "ARQ | RX | " + str(static.ARQ_DATA_CHANNEL_MODE) + " | F:[" + str(static.ARQ_N_FRAME) + "/" + str(static.ARQ_N_RX_FRAMES_PER_BURSTS) + "] [" + str(arq_percent_burst).zfill(3) + "%] T:[" + str(static.ARQ_RX_N_CURRENT_ARQ_FRAME) + "/" + str(static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME) + "] [" + str(arq_percent_frame).zfill(3) + "%] [SNR:" + str(static.SNR) + "]")

    # allocate ARQ_RX_FRAME_BUFFER as a list with "None" if not already done. This should be done only once per burst!
    # here we will save the N frame of a data frame to N list position so we can explicit search for it
    # delete frame buffer if first frame to make sure the buffer is cleared and no junks of a old frame is remaining
    if static.ARQ_RX_N_CURRENT_ARQ_FRAME == 1:
        static.ARQ_RX_FRAME_BUFFER = []

    try:
        static.ARQ_RX_FRAME_BUFFER[static.ARQ_RX_N_CURRENT_ARQ_FRAME] = bytes(data_in)

    except IndexError:

        static.ARQ_RX_FRAME_BUFFER = []
        
        #on a new transmission we reset the timer
        static.ARQ_START_OF_TRANSMISSION = int(time.time()) + 4
        
        for i in range(0, static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME + 1):
            static.ARQ_RX_FRAME_BUFFER.insert(i, None)

        static.ARQ_RX_FRAME_BUFFER[static.ARQ_RX_N_CURRENT_ARQ_FRAME] = bytes(data_in)
        static.ARQ_FRAME_BOF_RECEIVED = False
        static.ARQ_FRAME_EOF_RECEIVED = False

    try:
        static.ARQ_RX_BURST_BUFFER[static.ARQ_N_FRAME] = bytes(data_in)

    except IndexError:

        static.ARQ_RX_BURST_BUFFER = []
       
        for i in range(0, static.ARQ_N_RX_FRAMES_PER_BURSTS + 1):
            static.ARQ_RX_BURST_BUFFER.insert(i, None)

        static.ARQ_RX_BURST_BUFFER[static.ARQ_N_FRAME] = bytes(data_in)

# - ------------------------- ARQ BURST CHECKER
    # run only if we recieved all ARQ FRAMES per ARQ BURST
    if static.ARQ_RX_BURST_BUFFER.count(None) == 1:  # count nones
        logging.info("ARQ | TX | BURST ACK")

        # BUILDING ACK FRAME FOR BURST -----------------------------------------------

        ack_frame = bytearray(14)
        ack_frame[:1] = bytes([60])
        ack_frame[1:2] = static.DXCALLSIGN_CRC8
        ack_frame[2:3] = static.MYCALLSIGN_CRC8


        # TRANSMIT ACK FRAME FOR BURST-----------------------------------------------
        modem.transmit_signalling(ack_frame, 1)

        while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
            time.sleep(0.01)
        static.CHANNEL_STATE = 'RECEIVING_DATA'
        # clear burst buffer
        static.ARQ_RX_BURST_BUFFER = []

    # if decoded N frames are unequal to expected frames per burst
    elif static.ARQ_N_FRAME == static.ARQ_N_RX_FRAMES_PER_BURSTS and static.ARQ_RX_BURST_BUFFER.count(None) != 1:

        # --------------- CHECK WHICH BURST FRAMES WE ARE MISSING -------------------------------------------
        missing_frames = b''
        for burstnumber in range(1, len(static.ARQ_RX_BURST_BUFFER)):

            if static.ARQ_RX_BURST_BUFFER[burstnumber] == None:
                # frame_number = static.ARQ_RX_N_CURRENT_ARQ_FRAME - static.ARQ_N_RX_FRAMES_PER_BURSTS + burstnumber
                # logging.debug("frame_number" + str(frame_number))
                logging.debug("static.ARQ_RX_N_CURRENT_ARQ_FRAME" + str(static.ARQ_RX_N_CURRENT_ARQ_FRAME))
                logging.debug("ARQ_N_RX_FRAMES_PER_BURSTS" + str(static.ARQ_N_RX_FRAMES_PER_BURSTS))

                frame_number = burstnumber
                frame_number = frame_number.to_bytes(2, byteorder='big')
                missing_frames += frame_number

        logging.warning("ARQ | TX | RPT ARQ FRAMES [" + str(missing_frames) + "] [SNR:" + str(static.SNR) + "]")

        # BUILDING RPT FRAME FOR BURST -----------------------------------------------
        rpt_frame = bytearray(14)
        rpt_frame[:1] = bytes([62])
        rpt_frame[1:2] = static.DXCALLSIGN_CRC8
        rpt_frame[2:3] = static.MYCALLSIGN_CRC8
        rpt_frame[3:9] = missing_frames

        # TRANSMIT RPT FRAME FOR BURST-----------------------------------------------
        modem.transmit_signalling(rpt_frame, 1)
        while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
            time.sleep(0.01)
        static.CHANNEL_STATE = 'RECEIVING_DATA'

# ---------------------------- FRAME MACHINE
    # ---------------  IF LIST NOT CONTAINS "None" stick everything together
    complete_data_frame = bytearray()
    # print("static.ARQ_RX_FRAME_BUFFER.count(None)" + str(static.ARQ_RX_FRAME_BUFFER.count(None)))
    if static.ARQ_RX_FRAME_BUFFER.count(None) == 1:  # 1 because position 0 of list will alaways be None in our case
        logging.debug("DECODING FRAME!")
        for frame in range(1, len(static.ARQ_RX_FRAME_BUFFER)):
            raw_arq_frame = static.ARQ_RX_FRAME_BUFFER[frame]
            arq_frame_payload = raw_arq_frame[8:]

            # -------- DETECT IF WE RECEIVED A FRAME HEADER THEN SAVE DATA TO GLOBALS
            if arq_frame_payload[2:4].startswith(static.FRAME_BOF):
                static.FRAME_CRC = arq_frame_payload[:2]
                static.ARQ_FRAME_BOF_RECEIVED = True

                arq_frame_payload = arq_frame_payload.split(static.FRAME_BOF)
                arq_frame_payload = arq_frame_payload[1]
                logging.debug("BOF")

            # -------- DETECT IF WE RECEIVED A FRAME FOOTER THEN SAVE DATA TO GLOBALS
            # we need to check for at least one xFF. Sometimes we have only one xFF, because the second one is in the next frame
            if arq_frame_payload.rstrip(b'\x00').endswith(static.FRAME_EOF) or arq_frame_payload.rstrip(b'\x00').endswith(static.FRAME_EOF[:-1]):
                static.ARQ_FRAME_EOF_RECEIVED = True
                if arq_frame_payload.rstrip(b'\x00').endswith(static.FRAME_EOF[:-1]):
                    arq_frame_payload = arq_frame_payload.split(static.FRAME_EOF[:-1])
                    arq_frame_payload = arq_frame_payload[0]
                else:
                    arq_frame_payload = arq_frame_payload.split(static.FRAME_EOF)
                    arq_frame_payload = arq_frame_payload[0]
                logging.debug("EOF")

            # --------- AFTER WE SEPARATED BOF AND EOF, STICK EVERYTHING TOGETHER
            complete_data_frame = complete_data_frame + arq_frame_payload
            logging.debug(complete_data_frame)

    # check if Begin of Frame BOF and End of Frame EOF are received, then start calculating CRC and sticking everything together
    if static.ARQ_FRAME_BOF_RECEIVED and static.ARQ_FRAME_EOF_RECEIVED:

        frame_payload_crc = helpers.get_crc_16(complete_data_frame)

        # IF THE FRAME PAYLOAD CRC IS EQUAL TO THE FRAME CRC WHICH IS KNOWN FROM THE HEADER --> SUCCESS
        if frame_payload_crc == static.FRAME_CRC:
            logging.log(25, "ARQ | RX | DATA FRAME SUCESSFULLY RECEIVED! :-) ")

            
            # append received frame to RX_BUFFER
            static.RX_BUFFER.append(complete_data_frame)

            # BUILDING ACK FRAME FOR DATA FRAME -----------------------------------------------
            ack_frame = bytearray(14)
            ack_frame[:1] = bytes([61])
            ack_frame[1:2] = static.DXCALLSIGN_CRC8
            ack_frame[2:3] = static.MYCALLSIGN_CRC8

            # TRANSMIT ACK FRAME FOR BURST-----------------------------------------------
            #time.sleep(0.5)  # 0.5
            logging.info("ARQ | TX | ARQ DATA FRAME ACK [" + str(static.FRAME_CRC.hex()) + "] [SNR:" + str(static.SNR) + "]")

            modem.transmit_signalling(ack_frame, 1)

            while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
                time.sleep(0.01)
            
            helpers.arq_reset_frame_machine()

            logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]<< >>[" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")
            
        else:
            print("ARQ_FRAME_BOF_RECEIVED " + str(static.ARQ_FRAME_BOF_RECEIVED))
            print("ARQ_FRAME_EOF_RECEIVED " + str(static.ARQ_FRAME_EOF_RECEIVED))
            print(static.ARQ_RX_FRAME_BUFFER)
            logging.error("ARQ | RX | DATA FRAME NOT SUCESSFULLY RECEIVED!")

            # BUILDING ACK FRAME FOR DATA FRAME -----------------------------------------------
            nak_frame = bytearray(14)
            nak_frame[:1] = bytes([63])
            nak_frame[1:2] = static.DXCALLSIGN_CRC8
            nak_frame[2:3] = static.MYCALLSIGN_CRC8

            # TRANSMIT ACK FRAME FOR BURST-----------------------------------------------
            #time.sleep(0.5)  # 0.5
            logging.info("ARQ | TX | NAK")

            modem.transmit_signalling(nak_frame, 1)
            while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
                time.sleep(0.01)

            
            helpers.arq_reset_frame_machine()
            
            logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]<<X>>[" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")

def arq_transmit(data_out):
    # we need to set payload per frame manually at this point. maybe we can do this more dynmic.
    if static.ARQ_DATA_CHANNEL_MODE == 10:
        payload_per_frame = 512 - 2
    elif static.ARQ_DATA_CHANNEL_MODE == 11:
        payload_per_frame = 258 - 2
    elif static.ARQ_DATA_CHANNEL_MODE == 12:
        payload_per_frame = 128 - 2
    elif static.ARQ_DATA_CHANNEL_MODE == 14:
        payload_per_frame = 16 - 2
    else:
        payload_per_frame = 16 - 2

    static.ARQ_PAYLOAD_PER_FRAME = payload_per_frame - 8

    # print("static.ARQ_DATA_PAYLOAD_PER_FRAME " + str(static.FREEDV_DATA_PAYLOAD_PER_FRAME))
    # print("static.ARQ_PAYLOAD_PER_FRAME " + str(static.ARQ_PAYLOAD_PER_FRAME))

    frame_header_length = 6  # 4

    n_arq_frames_per_data_frame = (len(data_out) + frame_header_length) // static.ARQ_PAYLOAD_PER_FRAME + ((len(data_out) + frame_header_length) % static.ARQ_PAYLOAD_PER_FRAME > 0)

    frame_payload_crc = helpers.get_crc_16(data_out)

    # This is the total frame with frame header, which will be send
    data_out = frame_payload_crc + static.FRAME_BOF + data_out + static.FRAME_EOF
    #                     2                 2              N           2

    # --------------------------------------------- LETS CREATE A BUFFER BY SPLITTING THE FILES INTO PEACES
    static.TX_BUFFER = [data_out[i:i + static.ARQ_PAYLOAD_PER_FRAME] for i in range(0, len(data_out), static.ARQ_PAYLOAD_PER_FRAME)]
    static.TX_BUFFER_SIZE = len(static.TX_BUFFER)

    logging.info("ARQ | TX | M:" + str(static.ARQ_DATA_CHANNEL_MODE) + " | DATA FRAME --- BYTES: " + str(len(data_out)) + " ARQ FRAMES: " + str(static.TX_BUFFER_SIZE))

    # --------------------------------------------- THIS IS THE MAIN LOOP-----------------------------------------------------------------
    static.ARQ_N_SENT_FRAMES = 0  # SET N SENT FRAMES TO 0 FOR A NEW SENDING CYCLE
    while static.ARQ_N_SENT_FRAMES <= static.TX_BUFFER_SIZE:

        #static.ARQ_TX_N_FRAMES_PER_BURST = get_n_frames_per_burst()

        # ----------- CREATE FRAME TOTAL PAYLOAD TO BE ABLE TO CREATE CRC FOR IT
        try:  # DETECT IF LAST BURST TO PREVENT INDEX ERROR OF BUFFER

            for i in range(static.ARQ_TX_N_FRAMES_PER_BURST):  # Loop through TX_BUFFER LIST
                len(static.TX_BUFFER[static.ARQ_N_SENT_FRAMES + i])  # we calculate the length to trigger a list index error

        except IndexError:  # IF LAST BURST DETECTED BUILD CRC WITH LESS FRAMES AND SET static.ARQ_TX_N_FRAMES_PER_BURST TO VALUE OF REST!

            if static.ARQ_N_SENT_FRAMES == 0 and (static.ARQ_TX_N_FRAMES_PER_BURST > static.TX_BUFFER_SIZE):  # WE CANT DO MODULO 0 --> CHECK IF FIRST FRAME == LAST FRAME
                static.ARQ_TX_N_FRAMES_PER_BURST = static.TX_BUFFER_SIZE

            elif static.ARQ_N_SENT_FRAMES == 1 and (static.ARQ_TX_N_FRAMES_PER_BURST > static.TX_BUFFER_SIZE):  # MODULO 1 WILL ALWAYS BE 0 --> THIS FIXES IT
                static.ARQ_TX_N_FRAMES_PER_BURST = static.TX_BUFFER_SIZE - static.ARQ_N_SENT_FRAMES

            else:
                static.ARQ_TX_N_FRAMES_PER_BURST = (static.TX_BUFFER_SIZE % static.ARQ_N_SENT_FRAMES)

        # --------------------------------------------- N ATTEMPTS TO SEND BURSTS IF ACK RECEPTION FAILS
        for static.TX_N_RETRIES in range(static.TX_N_MAX_RETRIES):

            if static.ARQ_N_SENT_FRAMES + 1 <= static.TX_BUFFER_SIZE:
                logging.log(24, "ARQ | TX | M:" + str(static.ARQ_DATA_CHANNEL_MODE) + " | F:[" + str(static.ARQ_N_SENT_FRAMES + 1) + "-" + str(static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST) + "] | T:[" + str(static.ARQ_N_SENT_FRAMES) + "/" + str(static.TX_BUFFER_SIZE) + "] [" + str(int(static.ARQ_N_SENT_FRAMES / (static.TX_BUFFER_SIZE) * 100)).zfill(3) + "%] | A:[" + str(static.TX_N_RETRIES + 1) + "/" + str(static.TX_N_MAX_RETRIES) + "]")

            # lets refresh all timers and ack states before sending a new frame
            helpers.arq_reset_ack(False)
            helpers.arq_reset_timeout(False)
            
            modem.transmit_arq_burst()
            # lets wait during sending. After sending is finished we will continue
            while static.CHANNEL_STATE == 'SENDING_DATA':
                time.sleep(0.01)

            # --------------------------- START TIMER FOR WAITING FOR ACK ---> IF TIMEOUT REACHED, ACK_TIMEOUT = 1

            logging.debug("ARQ | RX | WAITING FOR BURST ACK")
            static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'

            #helpers.arq_reset_timeout(False)
            #helpers.arq_reset_ack(False)

            logging.debug(".............................")
            logging.debug("static.ARQ_STATE " + str(static.ARQ_STATE))
            logging.debug("static.ARQ_FRAME_ACK_RECEIVED " + str(static.ARQ_FRAME_ACK_RECEIVED))
            logging.debug("static.ARQ_ACK_RECEIVED " + str(static.ARQ_ACK_RECEIVED))
            logging.debug("static.ARQ_RX_ACK_TIMEOUT " + str(static.ARQ_RX_ACK_TIMEOUT))
            logging.debug("static.ARQ_RPT_RECEIVED " + str(static.ARQ_RPT_RECEIVED))
            logging.debug(".............................")
            
            burstacktimeout = time.time() + static.ARQ_RX_ACK_TIMEOUT_SECONDS
            # --------------------------- WHILE TIMEOUT NOT REACHED AND NO ACK RECEIVED --> LISTEN
            while not static.ARQ_ACK_RECEIVED and not static.ARQ_RPT_RECEIVED and not static.ARQ_FRAME_ACK_RECEIVED and time.time() < burstacktimeout:# and static.ARQ_RX_FRAME_TIMEOUT != True and static.ARQ_RX_ACK_TIMEOUT != True:
                time.sleep(0.01)  # lets reduce CPU load a little bit
                logging.debug(static.CHANNEL_STATE)

            if static.ARQ_RPT_RECEIVED:
                logging.warning("ARQ | RX | REQUEST FOR REPEATING FRAMES: " + str(static.ARQ_RPT_FRAMES))
                logging.warning("ARQ | TX | SENDING REQUESTED FRAMES: " + str(static.ARQ_RPT_FRAMES))

                modem.transmit_arq_burst()
                # lets wait during sending. After sending is finished we will continue
                while static.ARQ_STATE == 'SENDING_DATA':
                    time.sleep(0.01)
                static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'

                helpers.arq_reset_timeout(False)
                helpers.arq_reset_ack(False)

                rpttimeout = time.time() + static.ARQ_RX_RPT_TIMEOUT_SECONDS

                while not static.ARQ_ACK_RECEIVED and not static.ARQ_FRAME_ACK_RECEIVED and time.time() < rpttimeout: #static.ARQ_RX_RPT_TIMEOUT == False:
                    time.sleep(0.01)  # lets reduce CPU load a little bit
                    #logging.info(static.ARQ_STATE)

                    if static.ARQ_ACK_RECEIVED:
                        logging.info("ARQ | RX | ACK AFTER RPT")
                        helpers.arq_reset_ack(True)
                        static.ARQ_RPT_FRAMES = []
                        static.ARQ_N_SENT_FRAMES = static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST
                        


                if static.ARQ_RX_RPT_TIMEOUT and not static.ARQ_ACK_RECEIVED:
                    logging.error("ARQ | Burst lost....")

                    helpers.arq_reset_ack(False)
                    static.ARQ_RPT_FRAMES = []
                
                #break    
                    
            # the order of ACK check is important! speciall the FRAME ACK after RPT needs to be checked really early!


            # --------------- BREAK LOOP IF FRAME ACK HAS BEEN RECEIVED EARLIER AS EXPECTED
            elif static.ARQ_FRAME_ACK_RECEIVED:
                logging.info("ARQ | RX | EARLY FRAME ACK RECEIVED #2")

                static.ARQ_N_SENT_FRAMES = static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST
                break

           # --------------------------------------------------------------------------------------------------------------
            elif not static.ARQ_ACK_RECEIVED: # and static.ARQ_RX_ACK_TIMEOUT == True:
                logging.warning("ARQ | RX | ACK TIMEOUT!")
                pass  # no break here so we can continue with the next try of repeating the burst


            # --------------- BREAK LOOP IF ACK HAS BEEN RECEIVED
            elif static.ARQ_ACK_RECEIVED:
                transfer_rates = helpers.calculate_transfer_rate()
                logging.info("ARQ | RX | ACK [" + str(transfer_rates[2]) + " bit/s | " + str(transfer_rates[3]) + " B/min]")
                
                # -----------IF ACK RECEIVED, INCREMENT ITERATOR FOR MAIN LOOP TO PROCEED WITH NEXT FRAMES/BURST
                static.ARQ_N_SENT_FRAMES = static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST
                break


                

            else:
                logging.info("------------------------------->NO RULE MATCHED!")
                print("ARQ_ACK_RECEIVED " + str(static.ARQ_ACK_RECEIVED))
                print("ARQ_RX_ACK_TIMEOUT " + str(static.ARQ_RX_ACK_TIMEOUT))
                break
                
            
        # --------------------------------WAITING AREA FOR FRAME ACKs

        logging.debug("static.ARQ_N_SENT_FRAMES         " + str(static.ARQ_N_SENT_FRAMES))
        logging.debug("static.TX_BUFFER_SIZE            " + str(static.TX_BUFFER_SIZE))
        logging.debug("static.TX_N_RETRIES              " + str(static.TX_N_RETRIES))
        logging.debug("static.TX_N_MAX_RETRIES          " + str(static.TX_N_MAX_RETRIES))
        logging.debug("static.ARQ_STATE                 " + str(static.ARQ_STATE))
        logging.debug("static.ARQ_FRAME_ACK_RECEIVED    " + str(static.ARQ_FRAME_ACK_RECEIVED))
        logging.debug("static.ARQ_RX_FRAME_TIMEOUT      " + str(static.ARQ_RX_FRAME_TIMEOUT))
        logging.debug("static.ARQ_ACK_RECEIVED          " + str(static.ARQ_ACK_RECEIVED))
        logging.debug("static.ARQ_RX_ACK_TIMEOUT        " + str(static.ARQ_RX_ACK_TIMEOUT))
        logging.debug("static.ARQ_RPT_RECEIVED          " + str(static.ARQ_RPT_RECEIVED))
        logging.debug("static.ARQ_TX_N_FRAMES_PER_BURST " + str(static.ARQ_TX_N_FRAMES_PER_BURST))

        static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'

        frameacktimeout = time.time() + static.ARQ_RX_FRAME_TIMEOUT_SECONDS
        # wait for frame ACK if we processed the last frame/burst
        while not static.ARQ_FRAME_ACK_RECEIVED and time.time() < frameacktimeout and static.ARQ_N_SENT_FRAMES == static.TX_BUFFER_SIZE:
            time.sleep(0.01)  # lets reduce CPU load a little bit
            logging.debug("WAITING FOR FRAME ACK")

        # ----------- if no ACK received and out of retries.....stop frame sending
        if not static.ARQ_ACK_RECEIVED and not static.ARQ_FRAME_ACK_RECEIVED: # and static.ARQ_RX_ACK_TIMEOUT == True:
            logging.error("ARQ | TX | NO ACK RECEIVED | DATA SHOULD BE RESEND!")
            break

        # -------------------------BREAK TX BUFFER LOOP IF ALL PACKETS HAVE BEEN SENT AND WE GOT A FRAME ACK
        elif static.ARQ_N_SENT_FRAMES == static.TX_BUFFER_SIZE and static.ARQ_FRAME_ACK_RECEIVED:
            logging.log(25, "ARQ | RX | FRAME ACK! - DATA TRANSMITTED! :-)")
            break
            
        elif not static.ARQ_FRAME_ACK_RECEIVED and time.time() > frameacktimeout: # == False and static.ARQ_RX_FRAME_TIMEOUT == True:
            logging.error("ARQ | TX | NO FRAME ACK RECEIVED")
            break

        else:
            logging.debug("NO MATCHING RULE AT THE END")

    # IF TX BUFFER IS EMPTY / ALL FRAMES HAVE BEEN SENT --> HERE WE COULD ADD AN static.VAR for IDLE STATE
    transfer_rates = helpers.calculate_transfer_rate()
    logging.info("RATE (DATA/ACK) :[" + str(transfer_rates[0]) + " bit/s | " + str(transfer_rates[1]) + " B/min]")

    logging.info("ARQ | TX | BUFFER EMPTY")
    helpers.arq_reset_frame_machine()
    # await asyncio.sleep(2)
    #time.sleep(2)
    logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]<< >>[" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")
    

    # this should close our thread so we are saving memory...
    # https://stackoverflow.com/questions/905189/why-does-sys-exit-not-exit-when-called-inside-a-thread-in-python
    sys.exit()


# BURST MACHINE TO DEFINE N BURSTS PER FRAME    ---> LATER WE CAN USE CHANNEL MESSUREMENT TO SET FRAMES PER BURST
def get_n_frames_per_burst():
    #n_frames_per_burst = randrange(1,10)
    n_frames_per_burst = 2
    return n_frames_per_burst


def get_best_mode_for_transmission():    
    mode = 14
    return mode



def burst_ack_received():
    static.ARQ_ACK_RECEIVED = True  # Force data loops of TNC to stop and continue with next frame
    static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time()) # we need to update our timeout timestamp


def frame_ack_received():
    static.ARQ_FRAME_ACK_RECEIVED = True  # Force data loops of TNC to stop and continue with next frame
    static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time()) # we need to update our timeout timestamp


def burst_rpt_received(data_in):
    static.ARQ_RPT_RECEIVED = True
    static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time()) # we need to update our timeout timestamp
    static.ARQ_RPT_FRAMES = []

    missing_area = bytes(data_in[3:12])  # 1:9

    for i in range(0, 6, 2):
        if not missing_area[i:i + 2].endswith(b'\x00\x00'):
            missing = missing_area[i:i + 2]
            static.ARQ_RPT_FRAMES.insert(0, missing)

def frame_nack_received():
    print("NAK RECEIVED :-/")

# ############################################################################################################
# ARQ DATA CHANNEL HANDLER
# ############################################################################################################


def open_dc_and_transmit(data_out, mode, n_frames):
    if not static.ARQ_READY_FOR_DATA:


        if n_frames != 0:
            static.ARQ_TX_N_FRAMES_PER_BURST = int(n_frames)

        else:
            static.ARQ_TX_N_FRAMES_PER_BURST = get_n_frames_per_burst()


        asyncio.run(arq_open_data_channel(mode))
    # wait until data channel is open
    while not static.ARQ_READY_FOR_DATA:
        time.sleep(0.01)
        
    #on a new transmission we reset the timer
    static.ARQ_START_OF_TRANSMISSION = int(time.time())

    # lets wait a little bit so RX station is ready for receiving
    wait_before_data_timer = time.time() + 0.5
    while time.time() < wait_before_data_timer:
        pass    
    
    # lets wait a little bit
    #time.sleep(5)
               
    # transmit data    
    arq_transmit(data_out)
    



async def arq_open_data_channel(mode):

    if mode == 0:
        static.ARQ_DATA_CHANNEL_MODE = get_best_mode_for_transmission()
        print(static.ARQ_DATA_CHANNEL_MODE)
    else:
        static.ARQ_DATA_CHANNEL_MODE = int(mode)
    
    static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time())
    
    while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
        time.sleep(0.01)

    connection_frame = bytearray(14)
    connection_frame[:1] = bytes([225])
    connection_frame[1:2] = static.DXCALLSIGN_CRC8
    connection_frame[2:3] = static.MYCALLSIGN_CRC8
    connection_frame[3:9] = static.MYCALLSIGN
    connection_frame[12:13] = bytes([static.ARQ_DATA_CHANNEL_MODE])

    while not static.ARQ_READY_FOR_DATA:
        for attempt in range(0,static.ARQ_OPEN_DATA_CHANNEL_RETRIES):
            logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>> <<[" + str(static.DXCALLSIGN, 'utf-8') + "] A:[" + str(attempt + 1) + "/" + str(static.ARQ_OPEN_DATA_CHANNEL_RETRIES) + "]")
            modem.transmit_signalling(connection_frame, 1)
            while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
                time.sleep(0.01)
        
            timeout = time.time() + 5    
            while time.time() < timeout:    
                # break if data channel is openend    
                if static.ARQ_READY_FOR_DATA:
                    break
            if static.ARQ_READY_FOR_DATA:
                break
            
            if not static.ARQ_READY_FOR_DATA and attempt + 1 == static.ARQ_OPEN_DATA_CHANNEL_RETRIES:
                logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>>X<<[" + str(static.DXCALLSIGN, 'utf-8') + "]")
                helpers.arq_reset_frame_machine()
                sys.exit()


def arq_received_data_channel_opener(data_in):

    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')
    helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'DATA-CHANNEL', static.SNR)
        
    logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>> <<[" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")
    
    static.ARQ_STATE = 'DATA'
    static.TNC_STATE = 'BUSY'

    static.ARQ_DATA_CHANNEL_MODE = int.from_bytes(bytes(data_in[12:13]), "big")
    static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time())    

    connection_frame = bytearray(14)
    connection_frame[:1] = bytes([226])
    connection_frame[1:2] = static.DXCALLSIGN_CRC8
    connection_frame[2:3] = static.MYCALLSIGN_CRC8
    connection_frame[3:9] = static.MYCALLSIGN
    connection_frame[12:13] = bytes([static.ARQ_DATA_CHANNEL_MODE])


    modem.transmit_signalling(connection_frame, 2)

    while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
        time.sleep(0.01)

    logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")
    
    #time.sleep(1)
    
    wait_until_receive_data = time.time() + 1
    while time.time() < wait_until_receive_data:
        pass
    static.CHANNEL_STATE = 'RECEIVING_DATA'
    # and now we are going to "RECEIVING_DATA" mode....


def arq_received_channel_is_open(data_in):

    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')
    helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'DATA-CHANNEL', static.SNR)
    
    static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time())


    if static.ARQ_DATA_CHANNEL_MODE == int.from_bytes(bytes(data_in[12:13]), "big"):
        logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")
        
        
        helpers.wait(1)
        
        static.ARQ_STATE = 'DATA'
        static.ARQ_READY_FOR_DATA = True
        static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time())
    else:
        print("wrong mode received...")


# ############################################################################################################
# PING HANDLER
# ############################################################################################################

#async def transmit_ping(callsign):
def transmit_ping(callsign):
    static.DXCALLSIGN = bytes(callsign, 'utf-8').rstrip(b'\x00')
    static.DXCALLSIGN_CRC8 = helpers.get_crc_8(static.DXCALLSIGN)
    logging.info("PING [" + str(static.MYCALLSIGN, 'utf-8') + "] >>> [" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")

    ping_frame = bytearray(14)
    ping_frame[:1] = bytes([210])
    ping_frame[1:2] = static.DXCALLSIGN_CRC8
    ping_frame[2:3] = static.MYCALLSIGN_CRC8
    ping_frame[3:9] = static.MYCALLSIGN

    # wait while sending....
    modem.transmit_signalling(ping_frame, 1)
    print("ping=?")
    while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
        print("PING....")
        time.sleep(0.01)


def received_ping(data_in):

    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')
    helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'PING', static.SNR)
    logging.info("PING [" + str(static.MYCALLSIGN, 'utf-8') + "] <<< [" + str(static.DXCALLSIGN, 'utf-8') + "] [SNR:" + str(static.SNR) + "]")

    ping_frame = bytearray(14)
    ping_frame[:1] = bytes([211])
    ping_frame[1:2] = static.DXCALLSIGN_CRC8
    ping_frame[2:3] = static.MYCALLSIGN_CRC8
    ping_frame[3:9] = static.MYGRID

    # wait while sending....
    modem.transmit_signalling(ping_frame, 1)

    while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
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


#async def transmit_cq():
def transmit_cq():
    logging.info("CQ CQ CQ")

    cq_frame = bytearray(14)
    cq_frame[:1] = bytes([200])
    cq_frame[1:2] = b'\x01'
    #cq_frame[2:3] = static.MYCALLSIGN_CRC8
    #cq_frame[3:9] = static.MYCALLSIGN
    cq_frame[2:8] = static.MYCALLSIGN
    cq_frame[8:14] = static.MYGRID
    #print(cq_frame)
    
    modem.transmit_signalling(cq_frame, 3)
    #for i in range(0, 3):
    #    
    #    modem.transmit_signalling(cq_frame, 1)
    #    while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
    #        time.sleep(0.01)
    #    
    #    time_between_cq = time.time() + 1    
    #    while time.time() < time_between_cq:
    #        pass
            

def received_cq(data_in):
    # here we add the received station to the heard stations buffer
    dxcallsign = bytes(data_in[2:8]).rstrip(b'\x00')
    dxgrid = bytes(data_in[8:14]).rstrip(b'\x00')
    
    logging.info("CQ RCVD [" + str(dxcallsign, 'utf-8') + "]["+ str(dxgrid, 'utf-8') +"] [SNR" + str(static.SNR) + "]")
    helpers.add_to_heard_stations(dxcallsign,dxgrid, 'CQ CQ CQ', static.SNR)




async def transmit_beacon():
    logging.info("BEACON")
    beacon_frame[:1] = bytes([230])
    beacon_frame[1:2] = b'\x01'
    beacon_frame[2:8] = static.MYCALLSIGN
    beacon_frame[8:14] = static.MYGRID

    while static.TNC_STATE == 'BEACON':
        await asyncio.sleep(60)
        modem.transmit_signalling(beacon_frame,1)
        while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
            time.sleep(0.01)


def received_beacon():
    # here we add the received station to the heard stations buffer
    dxcallsign = bytes(data_in[2:8]).rstrip(b'\x00')
    dxgrid = bytes(data_in[8:14]).rstrip(b'\x00')
    
    logging.info("BEACON RCVD [" + str(dxcallsign, 'utf-8') + "]["+ str(dxgrid, 'utf-8') +"] [SNR" + str(static.SNR) + "]")
    helpers.add_to_heard_stations(dxcallsign,dxgrid, 'BEACON', static.SNR)
