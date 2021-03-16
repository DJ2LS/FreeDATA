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

    logging.log(24, "ARQ | RX | " + str(static.ARQ_DATA_CHANNEL_MODE) + " | F:[" + str(static.ARQ_N_FRAME) + "/" + str(static.ARQ_N_RX_FRAMES_PER_BURSTS) + "] [" + str(arq_percent_burst).zfill(3) + "%] T:[" + str(static.ARQ_RX_N_CURRENT_ARQ_FRAME) + "/" + str(static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME) + "] [" + str(arq_percent_frame).zfill(3) + "%] [BER." + str(static.BER) + "]")

    # allocate ARQ_RX_FRAME_BUFFER as a list with "None" if not already done. This should be done only once per burst!
    # here we will save the N frame of a data frame to N list position so we can explicit search for it
    # delete frame buffer if first frame to make sure the buffer is cleared and no junks of a old frame is remaining
    if static.ARQ_RX_N_CURRENT_ARQ_FRAME == 1:
        static.ARQ_RX_FRAME_BUFFER = []

    try:
        static.ARQ_RX_FRAME_BUFFER[static.ARQ_RX_N_CURRENT_ARQ_FRAME] = bytes(data_in)

    except IndexError:

        static.ARQ_RX_FRAME_BUFFER = []
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
        modem.transmit_signalling(ack_frame)
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

        logging.warning("ARQ | TX | RPT ARQ FRAMES [" + str(missing_frames) + "] [BER." + str(static.BER) + "]")

        # BUILDING RPT FRAME FOR BURST -----------------------------------------------
        rpt_frame = bytearray(14)
        rpt_frame[:1] = bytes([63])
        rpt_frame[1:2] = static.DXCALLSIGN_CRC8
        rpt_frame[2:3] = static.MYCALLSIGN_CRC8
        rpt_frame[3:9] = missing_frames

        # TRANSMIT RPT FRAME FOR BURST-----------------------------------------------
        modem.transmit_signalling(rpt_frame)
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
    if static.ARQ_FRAME_BOF_RECEIVED == True and static.ARQ_FRAME_EOF_RECEIVED == True:

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
            time.sleep(1)  # 0.5
            logging.info("ARQ | TX | ARQ DATA FRAME ACK [" + str(static.FRAME_CRC.hex()) + "] [BER." + str(static.BER) + "]")

            modem.transmit_signalling(ack_frame)
            while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
                time.sleep(0.01)
            
            helpers.arq_reset_frame_machine()

            logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]<< >>[" + str(static.DXCALLSIGN, 'utf-8') + "] [BER." + str(static.BER) + "]")
            
        else:
            print("ARQ_FRAME_BOF_RECEIVED " + str(static.ARQ_FRAME_BOF_RECEIVED))
            print("ARQ_FRAME_EOF_RECEIVED " + str(static.ARQ_FRAME_EOF_RECEIVED))
            logging.error("ARQ | RX | DATA FRAME NOT SUCESSFULLY RECEIVED!")
            
            helpers.arq_reset_frame_machine()
            
            logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]<<X>>[" + str(static.DXCALLSIGN, 'utf-8') + "] [BER." + str(static.BER) + "]")

def arq_transmit(data_out):
    # we need to set payload per frame manually at this point. maybe we can do this more dynmic.
    if static.ARQ_DATA_CHANNEL_MODE == 10:
        payload_per_frame = 512 - 2
    elif static.ARQ_DATA_CHANNEL_MODE == 11:
        payload_per_frame = 256 - 2
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

        static.ARQ_TX_N_FRAMES_PER_BURST = get_n_frames_per_burst()

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
                logging.log(24, "ARQ | TX | M:" + str(static.ARQ_DATA_CHANNEL_MODE) + " | F:[" + str(static.ARQ_N_SENT_FRAMES + 1) + "-" + str(static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST) + "] | T:[" + str(static.ARQ_N_SENT_FRAMES) + "/" + str(static.TX_BUFFER_SIZE) + "] [" + str(int(static.ARQ_N_SENT_FRAMES / (static.TX_BUFFER_SIZE) * 100)).zfill(3) + "%] | A:[" + str(static.TX_N_RETRIES + 1) + "/" + str(static.TX_N_MAX_RETRIES) + "] [BER." + str(static.BER) + "]")


            modem.transmit_arq_burst()
            # lets wait during sending. After sending is finished we will continue
            while static.CHANNEL_STATE == 'SENDING_DATA':
                time.sleep(0.01)

            # --------------------------- START TIMER FOR WAITING FOR ACK ---> IF TIMEOUT REACHED, ACK_TIMEOUT = 1

            logging.info("ARQ | RX | WAITING FOR BURST ACK")
            static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'

            helpers.arq_reset_timeout(False)
            helpers.arq_reset_ack(False)

            acktimer = threading.Timer(static.ARQ_RX_ACK_TIMEOUT_SECONDS, helpers.arq_ack_timeout)
            acktimer.start()

            logging.debug(".............................")
            logging.debug("static.ARQ_STATE " + str(static.ARQ_STATE))
            logging.debug("static.ARQ_FRAME_ACK_RECEIVED " + str(static.ARQ_FRAME_ACK_RECEIVED))
            logging.debug("static.ARQ_ACK_RECEIVED " + str(static.ARQ_ACK_RECEIVED))
            logging.debug("static.ARQ_RX_ACK_TIMEOUT " + str(static.ARQ_RX_ACK_TIMEOUT))
            logging.debug("static.ARQ_RPT_RECEIVED " + str(static.ARQ_RPT_RECEIVED))
            logging.debug(".............................")

            # --------------------------- WHILE TIMEOUT NOT REACHED AND NO ACK RECEIVED --> LISTEN
            while static.ARQ_ACK_RECEIVED != True and static.ARQ_RPT_RECEIVED != True and static.ARQ_FRAME_ACK_RECEIVED != True and static.ARQ_RX_FRAME_TIMEOUT != True and static.ARQ_RX_ACK_TIMEOUT != True:
                time.sleep(0.01)  # lets reduce CPU load a little bit
                logging.debug(static.CHANNEL_STATE)

            if static.ARQ_RPT_RECEIVED == True:

                logging.warning("ARQ | RX | REQUEST FOR REPEATING FRAMES: " + str(static.ARQ_RPT_FRAMES))
                logging.warning("ARQ | TX | SENDING REQUESTED FRAMES: " + str(static.ARQ_RPT_FRAMES))

                modem.transmit_arq_burst()
                # lets wait during sending. After sending is finished we will continue
                while static.ARQ_STATE == 'SENDING_DATA':
                    time.sleep(0.01)
                static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'

                helpers.arq_reset_timeout(False)
                helpers.arq_reset_ack(False)

                rpttimer = threading.Timer(static.ARQ_RX_RPT_TIMEOUT_SECONDS, helpers.arq_rpt_timeout)
                rpttimer.start()

                while static.ARQ_ACK_RECEIVED == False and static.ARQ_FRAME_ACK_RECEIVED == False and static.ARQ_RX_RPT_TIMEOUT == False:
                    time.sleep(0.01)  # lets reduce CPU load a little bit
                    logging.debug(static.ARQ_STATE)

                    if static.ARQ_ACK_RECEIVED == True:

                        logging.info("ARQ | RX | ACK AFTER RPT")
                        rpttimer.cancel()
                        helpers.arq_reset_ack(True)
                        static.ARQ_RPT_FRAMES = []

                if static.ARQ_RX_RPT_TIMEOUT == True and static.ARQ_ACK_RECEIVED == False:

                    logging.error("ARQ | Burst lost....")

                    helpers.arq_reset_ack(False)
                    static.ARQ_RPT_FRAMES = []

           # --------------------------------------------------------------------------------------------------------------

            elif static.ARQ_ACK_RECEIVED == True and static.ARQ_RX_ACK_TIMEOUT == 1:
                logging.warning("ARQ | RX | ACK TIMEOUT!")
                pass  # no break here so we can continue with the next try of repeating the burst

            # --------------- BREAK LOOP IF ACK HAS BEEN RECEIVED
            elif static.ARQ_ACK_RECEIVED == True:
                logging.info("ARQ | RX | ACK")
                acktimer.cancel()
                # -----------IF ACK RECEIVED, INCREMENT ITERATOR FOR MAIN LOOP TO PROCEED WITH NEXT FRAMES/BURST
                static.ARQ_N_SENT_FRAMES = static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST
                break

            # --------------- BREAK LOOP IF FRAME ACK HAS BEEN RECEIVED EARLIER AS EXPECTED
            elif static.ARQ_FRAME_ACK_RECEIVED == True:

                logging.info("ARQ | RX | EARLY FRAME ACK RECEIVED")

                # static.ARQ_N_SENT_FRAMES = #static.TX_BUFFER_SIZE
                static.ARQ_N_SENT_FRAMES = static.ARQ_N_SENT_FRAMES + static.ARQ_TX_N_FRAMES_PER_BURST
                break

            else:
                logging.debug("------------------------------->NO RULE MATCHED!")
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

        frametimer = threading.Timer(static.ARQ_RX_FRAME_TIMEOUT_SECONDS, helpers.arq_frame_timeout)
        frametimer.start()
        static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'

        # wait for frame ACK if we processed the last frame/burst
        while static.ARQ_FRAME_ACK_RECEIVED == False and static.ARQ_RX_FRAME_TIMEOUT == False and static.ARQ_N_SENT_FRAMES == static.TX_BUFFER_SIZE:
            time.sleep(0.01)  # lets reduce CPU load a little bit
            logging.debug("WAITING FOR FRAME ACK")

        # ----------- if no ACK received and out of retries.....stop frame sending
        if static.ARQ_ACK_RECEIVED == False and static.ARQ_FRAME_ACK_RECEIVED == False and static.ARQ_RX_ACK_TIMEOUT == True:
            logging.error("ARQ | TX | NO ACK RECEIVED | DATA SHOULD BE RESEND!")
            break

        # -------------------------BREAK TX BUFFER LOOP IF ALL PACKETS HAVE BEEN SENT AND WE GOT A FRAME ACK
        elif static.ARQ_N_SENT_FRAMES == static.TX_BUFFER_SIZE and static.ARQ_FRAME_ACK_RECEIVED == True:
            logging.log(25, "ARQ | RX | FRAME ACK RECEIVED - DATA TRANSMITTED! :-)")
            break

        elif static.ARQ_FRAME_ACK_RECEIVED == False and static.ARQ_RX_FRAME_TIMEOUT == True:
            logging.error("ARQ | TX | NO FRAME ACK RECEIVED")
            break

        else:
            logging.debug("NO MATCHING RULE AT THE END")

            # stop all timers
            try:
                frametimer.cancel()
            except Exception:
                pass

            try:
                acktimer.cancel()
            except Exception:
                pass

    # IF TX BUFFER IS EMPTY / ALL FRAMES HAVE BEEN SENT --> HERE WE COULD ADD AN static.VAR for IDLE STATE

    logging.info("ARQ | TX | BUFFER EMPTY")
    helpers.arq_reset_frame_machine()
    # await asyncio.sleep(2)
    time.sleep(2)
    logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]<< >>[" + str(static.DXCALLSIGN, 'utf-8') + "] [BER." + str(static.BER) + "]")
    
    #####arq_transmit_keep_alive()

    # this should close our thread so we are saving memory...
    # https://stackoverflow.com/questions/905189/why-does-sys-exit-not-exit-when-called-inside-a-thread-in-python
    sys.exit()


# BURST MACHINE TO DEFINE N BURSTS PER FRAME    ---> LATER WE CAN USE CHANNEL MESSUREMENT TO SET FRAMES PER BURST
def get_n_frames_per_burst():
    #n_frames_per_burst = randrange(1,10)
    n_frames_per_burst = 1
    return n_frames_per_burst


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

    missing_area = bytes(data_in[1:9])

    for i in range(0, 6, 2):
        if not missing_area[i:i + 2].endswith(b'\x00\x00'):
            missing = missing_area[i:i + 2]
            static.ARQ_RPT_FRAMES.insert(0, missing)


# ############################################################################################################
# ARQ DATA CHANNEL HANDLER
# ############################################################################################################


async def arq_open_data_channel():

    logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>> <<[" + str(static.DXCALLSIGN, 'utf-8') + "] [BER." + str(static.BER) + "]")

    static.ARQ_DATA_CHANNEL_MODE = 12
    static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time())
    
    while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
        time.sleep(0.01)

    connection_frame = bytearray(14)
    connection_frame[:1] = bytes([225])
    connection_frame[1:2] = static.DXCALLSIGN_CRC8
    connection_frame[2:3] = static.MYCALLSIGN_CRC8
    connection_frame[3:9] = static.MYCALLSIGN
    connection_frame[12:13] = bytes([static.ARQ_DATA_CHANNEL_MODE])

    modem.transmit_signalling(connection_frame)
    while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
        time.sleep(0.01)


def arq_received_data_channel_opener(data_in):

    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')
    
    logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>> <<[" + str(static.DXCALLSIGN, 'utf-8') + "] [BER." + str(static.BER) + "]")
    
    static.ARQ_STATE = 'DATA'
    static.TNC_STATE = 'BUSY'
    static.ARQ_SEND_KEEP_ALIVE = False
    static.ARQ_DATA_CHANNEL_MODE = int.from_bytes(bytes(data_in[12:13]), "big")
    static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time())    

    connection_frame = bytearray(14)
    connection_frame[:1] = bytes([226])
    connection_frame[1:2] = static.DXCALLSIGN_CRC8
    connection_frame[2:3] = static.MYCALLSIGN_CRC8
    connection_frame[12:13] = bytes([static.ARQ_DATA_CHANNEL_MODE])


    modem.transmit_signalling(connection_frame)
    while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
        time.sleep(0.01)

    logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "] [BER." + str(static.BER) + "]")
    static.CHANNEL_STATE = 'RECEIVING_DATA'
    # and now we are going to "RECEIVING_DATA" mode....


def arq_received_channel_is_open(data_in):
    static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time())

    if static.ARQ_DATA_CHANNEL_MODE == int.from_bytes(bytes(data_in[12:13]), "big"):
        logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "] [BER." + str(static.BER) + "]")
        
        static.ARQ_STATE = 'DATA'
        static.ARQ_READY_FOR_DATA = True
        static.ARQ_DATA_CHANNEL_LAST_RECEIVED = int(time.time())
    else:
        print("wrong mode received...")


# ############################################################################################################
# PING HANDLER
# ############################################################################################################

async def transmit_ping(callsign):
    static.DXCALLSIGN = bytes(callsign, 'utf-8').rstrip(b'\x00')
    static.DXCALLSIGN_CRC8 = helpers.get_crc_8(static.DXCALLSIGN)
    logging.info("PING [" + str(static.MYCALLSIGN, 'utf-8') + "] >>> [" + str(static.DXCALLSIGN, 'utf-8') + "] [BER." + str(static.BER) + "]")

    ping_frame = bytearray(14)
    ping_frame[:1] = bytes([210])
    ping_frame[1:2] = static.DXCALLSIGN_CRC8
    ping_frame[2:3] = static.MYCALLSIGN_CRC8
    ping_frame[3:9] = static.MYCALLSIGN

    # wait while sending....
    modem.transmit_signalling(ping_frame)
    while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
        time.sleep(0.01)


def received_ping(data_in):

    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')

    logging.info("PING [" + str(static.MYCALLSIGN, 'utf-8') + "] <<< [" + str(static.DXCALLSIGN, 'utf-8') + "] [BER." + str(static.BER) + "]")

    ping_frame = bytearray(14)
    ping_frame[:1] = bytes([211])
    ping_frame[1:2] = static.DXCALLSIGN_CRC8
    ping_frame[2:3] = static.MYCALLSIGN_CRC8
    ping_frame[3:9] = static.MYCALLSIGN

    # wait while sending....
    modem.transmit_signalling(ping_frame)
    while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
        time.sleep(0.01)


def received_ping_ack(data_in):

    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')

    logging.info("PING [" + str(static.DXCALLSIGN, 'utf-8') + "] >|< [" + str(static.MYCALLSIGN, 'utf-8') + "] [BER." + str(static.BER) + "]")
    static.TNC_STATE = 'IDLE'

# ############################################################################################################
# BROADCAST HANDLER
# ############################################################################################################


async def transmit_cq():
    logging.info("CQ CQ CQ")

    cq_frame = bytearray(14)
    cq_frame[:1] = bytes([200])
    cq_frame[1:2] = b'\x01'
    cq_frame[2:3] = static.MYCALLSIGN_CRC8
    cq_frame[3:9] = static.MYCALLSIGN

    for i in range(0, 3):

        modem.transmit_signalling(cq_frame)
        while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
            time.sleep(0.01)


def received_cq(data_in):
    static.DXCALLSIGN = b''
    static.DXCALLSIGN_CRC8 = b''
    logging.info("CQ RCVD [" + str(bytes(data_in[3:9]), 'utf-8') + "] [BER." + str(static.BER) + "]")

    # here we add the received station to the heard stations buffer
    dxcallsign = bytes(data_in[3:9]).rstrip(b'\x00')
    # check if buffer empty
    if len(static.HEARD_STATIONS) == 0:
        static.HEARD_STATIONS.append([dxcallsign, int(time.time())])
    # if not, we search and update
    else:
        for i in range(0, len(static.HEARD_STATIONS)):
            # update callsign with new timestamp
            if static.HEARD_STATIONS[i].count(dxcallsign) > 0:
                static.HEARD_STATIONS[i] = [dxcallsign, int(time.time())]
                break
            # insert if nothing found
            if i == len(static.HEARD_STATIONS) - 1:
                static.HEARD_STATIONS.append([dxcallsign, int(time.time())])
                break


async def transmit_beacon():
    logging.info("BEACON")
    frame_type = bytes([230])
    print(frame_type)
    beacon_frame = frame_type + static.MYCALLSIGN
    while static.TNC_STATE == 'BEACON':
        await asyncio.sleep(60)
        modem.transmit_signalling(beacon_frame)
        while static.CHANNEL_STATE == 'SENDING_SIGNALLING':
            time.sleep(0.01)


def received_beacon():
    static.DXCALLSIGN = b''
    static.DXCALLSIGN_CRC8 = b''
    logging.info("BEACON RCVD [" + str(bytes(data_in[3:9]), 'utf-8') + "] [BER." + str(static.BER) + "]")

    # here we add the received station to the heard stations buffer
    dxcallsign = bytes(data_in[3:9]).rstrip(b'\x00')
    # check if buffer empty
    if len(static.HEARD_STATIONS) == 0:
        static.HEARD_STATIONS.append([dxcallsign, int(time.time())])
    # if not, we search and update
    else:
        for i in range(0, len(static.HEARD_STATIONS)):
            # update callsign with new timestamp
            if static.HEARD_STATIONS[i].count(dxcallsign) > 0:
                static.HEARD_STATIONS[i] = [dxcallsign, int(time.time())]
                break
            # insert if nothing found
            if i == len(static.HEARD_STATIONS) - 1:
                static.HEARD_STATIONS.append([dxcallsign, int(time.time())])
                break
