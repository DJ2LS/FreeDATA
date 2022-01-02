#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 27 20:43:40 2020

@author: DJ2LS
"""
import sys
import logging, structlog, log_handler
import threading
import time
from random import randrange
import asyncio
import zlib
import ujson as json
import static
import modem
import helpers
modem = modem.RF()

'''
Author: DJ2LS
Description:
data_handler is a module like file, which handles all the ARQ related parts.
Because of the fact, that we need to use it from both directions - circular import,
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

DATA_FRAME_BOF                  =   b'BOF'#b'\xAA\xAA' # 2 bytes for the BOF End of File indicator in a data frame
DATA_FRAME_EOF                  =   b'EOF'#b'\xFF\xFF' # 2 bytes for the EOF End of File indicator in a data frame


def arq_data_received(data_in:bytes, bytes_per_frame:int):
    data_in = bytes(data_in)    
    
    # we neeed to declare our global variables, so the thread has access to them
    global RX_START_OF_TRANSMISSION
    global DATA_CHANNEL_LAST_RECEIVED
    global DATA_CHANNEL_READY_FOR_DATA
    global DATA_FRAME_BOF
    global DATA_FRAME_EOF
    # only process data if we are in ARQ and BUSY state else return to quit
    if static.ARQ_STATE != 'DATA' and static.TNC_STATE != 'BUSY':
        return
    
    # these vars will be overwritten during processing data
    RX_FRAME_BOF_RECEIVED = False       # here we save, if we received a "beginn of (data)frame"
    RX_FRAME_EOF_RECEIVED = False       # here we save, if we received a "end of (data)frame"
    
    RX_PAYLOAD_PER_MODEM_FRAME = bytes_per_frame - 2    # payload per moden frame

    static.TNC_STATE = 'BUSY'
    static.ARQ_STATE = 'DATA'
    static.INFO.append("ARQ;RECEIVING")
    DATA_CHANNEL_LAST_RECEIVED = int(time.time())
        
    # get some important data from the frame
    RX_N_FRAME_OF_BURST         = int.from_bytes(bytes(data_in[:1]), "big") - 10  # get number of burst frame
    RX_N_FRAMES_PER_BURST       = int.from_bytes(bytes(data_in[1:2]), "big")  # get number of bursts from received frame
    
    print(f"RX_N_FRAME_OF_BURST-{RX_N_FRAME_OF_BURST}")
    print(f"RX_N_FRAMES_PER_BURST-{RX_N_FRAMES_PER_BURST}")

    '''   
    The RX burst buffer needs to have a fixed length filled with "None". We need this later for counting the "Nones"   
    check if burst buffer has expected length else create it
    '''
    if len(static.RX_BURST_BUFFER) != RX_N_FRAMES_PER_BURST:
        static.RX_BURST_BUFFER = [None] * RX_N_FRAMES_PER_BURST   
    
    # append data to rx burst buffer
    static.RX_BURST_BUFFER[RX_N_FRAME_OF_BURST] = data_in[4:]

 
    '''
    check if we received all frames per burst by checking if burst buffer has no more "Nones"
    this is the ideal case because we received all data
    '''
    if not None in static.RX_BURST_BUFFER:
        # then iterate through burst buffer and append data to frame buffer
        for i in range(0,len(static.RX_BURST_BUFFER)):
            static.RX_FRAME_BUFFER += static.RX_BURST_BUFFER[i]
        # then delete burst buffer
            static.RX_BURST_BUFFER = []

        # lets check if we didnt receive a BOF and EOF yet to avoid sending ack frames if we already received all data
        if not RX_FRAME_BOF_RECEIVED and not RX_FRAME_EOF_RECEIVED and data_in.find(DATA_FRAME_EOF) < 0:  
            print(RX_FRAME_BOF_RECEIVED)
            print(RX_FRAME_EOF_RECEIVED)
            # create an ack frame
            ack_frame = bytearray(14)
            ack_frame[:1] = bytes([60])
            ack_frame[1:2] = static.DXCALLSIGN_CRC8
            ack_frame[2:3] = static.MYCALLSIGN_CRC8

            # and transmit it
            txbuffer = [ack_frame]
            structlog.get_logger("structlog").info("[TNC] ARQ | RX | ACK")
            modem.transmit(mode=14, repeats=1, repeat_delay=0, frames=txbuffer)

            calculate_transfer_rate_rx(RX_START_OF_TRANSMISSION, len(static.RX_FRAME_BUFFER))   

    
    # check if we received last frame of burst and we have "Nones" in our rx buffer
    # this is an indicator for missed frames.
    # with this way of doing this, we always MUST receive the last frame of a burst otherwise the entire 
    # burst is lost
    elif RX_N_FRAME_OF_BURST == RX_N_FRAMES_PER_BURST -1:
        # check where a None is in our burst buffer and do frame+1, beacuse lists start at 0
        missing_frames = [(frame+1) for frame, element in enumerate(static.RX_BURST_BUFFER) if element == None]
        
        # then create a repeat frame 
        rpt_frame       = bytearray(14)
        rpt_frame[:1]   = bytes([62])
        rpt_frame[1:2]  = static.DXCALLSIGN_CRC8
        rpt_frame[2:3]  = static.MYCALLSIGN_CRC8
        rpt_frame[3:9]  = missing_frames

        # and transmit it
        txbuffer = [rpt_frame]
        structlog.get_logger("structlog").info("[TNC] ARQ | RX | Requesting", frames=missing_frames)
        modem.transmit(mode=14, repeats=1, repeat_delay=0, frames=txbuffer)
        calculate_transfer_rate_rx(RX_START_OF_TRANSMISSION, len(static.RX_FRAME_BUFFER))
        
        
    # we should never reach this point
    else:
        structlog.get_logger("structlog").error("we shouldnt reach this point...")
    
    # We have a BOF and EOF flag in our data. If we received both we received our frame.
    # In case of loosing data but we received already a BOF and EOF we need to make sure, we 
    # received the complete last burst by checking it for Nones    
    bof_position = static.RX_FRAME_BUFFER.find(DATA_FRAME_BOF)
    eof_position = static.RX_FRAME_BUFFER.find(DATA_FRAME_EOF)
    if bof_position >= 0 and eof_position > 0 and not None in static.RX_BURST_BUFFER:
        print(f"bof_position {bof_position} / eof_position {eof_position}")
        RX_FRAME_BOF_RECEIVED = True
        RX_FRAME_EOF_RECEIVED = True
     
        #now extract raw data from buffer
        payload = static.RX_FRAME_BUFFER[bof_position+len(DATA_FRAME_BOF):eof_position]
        # get the data frame crc

        data_frame_crc = payload[:2]
        data_frame = payload[2:]

        # check if data_frame_crc is equal with received crc
        if data_frame_crc == helpers.get_crc_16(data_frame):
            structlog.get_logger("structlog").info("[TNC] ARQ | RX | DATA FRAME SUCESSFULLY RECEIVED")
            static.INFO.append("ARQ;RECEIVING;SUCCESS")
            
            # decompression
            data_frame_decompressed = zlib.decompress(data_frame)
            static.ARQ_COMPRESSION_FACTOR = len(data_frame_decompressed) / len(data_frame)
            data_frame = data_frame_decompressed
            # decode to utf-8 string
            data_frame = data_frame.decode("utf-8")
            
            # decode json objects from data frame to inspect if we received a file or message
            rawdata = json.loads(data_frame)
            '''
            if datatype is a file, we append to RX_BUFFER, which contains files only
            dt = datatype
            --> f = file
            --> m = message
            fn = filename
            ft = filetype
            d = data                
            crc = checksum            
            '''
            if rawdata["dt"] == "f":
                #logging.debug("RECEIVED FILE --> MOVING DATA TO RX BUFFER")
                static.RX_BUFFER.append([static.DXCALLSIGN,static.DXGRID,int(time.time()), data_frame])
                
            # if datatype is a file, we append to RX_MSG_BUFFER, which contains messages only            
            if rawdata["dt"] == "m":
                static.RX_MSG_BUFFER.append([static.DXCALLSIGN,static.DXGRID,int(time.time()), complete_data_frame])
                #logging.debug("RECEIVED MESSAGE --> MOVING DATA TO MESSAGE BUFFER")
            
            
            # BUILDING ACK FRAME FOR DATA FRAME
            ack_frame       = bytearray(14)
            ack_frame[:1]   = bytes([61])
            ack_frame[1:2]  = static.DXCALLSIGN_CRC8
            ack_frame[2:3]  = static.MYCALLSIGN_CRC8

            # TRANSMIT ACK FRAME FOR BURST
            structlog.get_logger("structlog").info("[TNC] ARQ | RX | SENDING DATA FRAME ACK", snr=static.SNR, crc=data_frame_crc.hex())
            txbuffer = [ack_frame]
            modem.transmit(mode=14, repeats=1, repeat_delay=0, frames=txbuffer)
            
            # update our statistics AFTER the frame ACK
            calculate_transfer_rate_rx(RX_START_OF_TRANSMISSION, len(static.RX_FRAME_BUFFER))
                        
            structlog.get_logger("structlog").info("[TNC] | RX | DATACHANNEL [" + str(static.MYCALLSIGN, 'utf-8') + "]<< >>[" + str(static.DXCALLSIGN, 'utf-8') + "]", snr=static.SNR)

        else:
            static.INFO.append("ARQ;RECEIVING;FAILED")
            structlog.get_logger("structlog").warning("[TNC] ARQ | RX | DATA FRAME NOT SUCESSFULLY RECEIVED!", e="wrong crc")
     
        
        # And finally we do a cleanup of our buffers and states
        DATA_CHANNEL_READY_FOR_DATA = False
        RX_FRAME_BOF_RECEIVED = False
        RX_FRAME_EOF_RECEIVED = False
        static.RX_BURST_BUFFER = []
        static.RX_FRAME_BUFFER = b''
        static.TNC_STATE = 'IDLE'
        static.ARQ_STATE = 'IDLE'        
        


def arq_transmit(data_out:bytes, mode:int, n_frames_per_burst:int):
    
    global RPT_REQUEST_BUFFER
    global DATA_FRAME_ACK_RECEIVED
    global RPT_REQUEST_RECEIVED
    global BURST_ACK_RECEIVED
    #global TX_START_OF_TRANSMISSION
    global DATA_CHANNEL_READY_FOR_DATA
    global DATA_FRAME_BOF
    global DATA_FRAME_EOF
    
        
    DATA_CHANNEL_MODE = mode

    TX_N_SENT_BYTES                = 0                      # already sent bytes per data frame
    TX_N_RETRIES_PER_BURST          = 0                     # retries we already sent data
    TX_N_MAX_RETRIES_PER_BURST      = 5                     # max amount of retries we sent before frame is lost
    TX_N_FRAMES_PER_BURST           = n_frames_per_burst    # amount of n frames per burst    
    TX_BUFFER = []  # our buffer for appending new data
    
    # TIMEOUTS
    BURST_ACK_TIMEOUT_SECONDS       =   3.0         # timeout for burst  acknowledges
    DATA_FRAME_ACK_TIMEOUT_SECONDS  =   3.0        # timeout for data frame acknowledges
    RPT_ACK_TIMEOUT_SECONDS         =   3.0        # timeout for rpt frame acknowledges

    static.INFO.append("ARQ;TRANSMITTING")
    structlog.get_logger("structlog").info("[TNC] | TX | DATACHANNEL", mode=DATA_CHANNEL_MODE, bytes=len(data_out))

    # save len of data_out to TOTAL_BYTES for our statistics
    static.TOTAL_BYTES = len(data_out)
    
    # compression
    data_frame_compressed = zlib.compress(data_out)
    static.ARQ_COMPRESSION_FACTOR = len(data_out) / len(data_frame_compressed)
    data_out = data_frame_compressed    



    tx_start_of_transmission = time.time()
    # reset statistics
    calculate_transfer_rate_tx(tx_start_of_transmission, 0, len(data_out))

    # append a crc and beginn and end of file indicators
    frame_payload_crc = helpers.get_crc_16(data_out)
    data_out = DATA_FRAME_BOF + frame_payload_crc + data_out + DATA_FRAME_EOF
    #initial bufferposition is 0
    bufferposition = 0    
    # iterate through data out buffer
    while bufferposition < len(data_out) and not DATA_FRAME_ACK_RECEIVED and DATA_CHANNEL_READY_FOR_DATA and static.ARQ_STATE == 'DATA':

        print(DATA_CHANNEL_READY_FOR_DATA)
        print(DATA_FRAME_ACK_RECEIVED)


        # we have TX_N_MAX_RETRIES_PER_BURST attempts for sending a burst
        for TX_N_RETRIES_PER_BURST in range(0,TX_N_MAX_RETRIES_PER_BURST):
            # payload information
            payload_per_frame = modem.get_bytes_per_frame(mode) -2 
            # tempbuffer list for storing our data frames
            tempbuffer = []
            # append data frames with TX_N_FRAMES_PER_BURST to tempbuffer
            for i in range(0, TX_N_FRAMES_PER_BURST):
                arqheader = bytearray()
                arqheader[:1] = bytes([10 + i])
                arqheader[1:2] = bytes([TX_N_FRAMES_PER_BURST]) 
                arqheader[3:4] = bytes(static.DXCALLSIGN_CRC8) 
                arqheader[4:5] = bytes(static.MYCALLSIGN_CRC8) 
                
                bufferposition_end = (bufferposition + payload_per_frame - len(arqheader))           
                
                # normal behavior
                if bufferposition_end <= len(data_out):
                   
                   frame = data_out[bufferposition:bufferposition_end]
                   frame = arqheader + frame 
                   
                # this point shouldnt reached that often                   
                elif bufferposition > len(data_out):
                    break
                
                # the last bytes of a frame    
                else:
                    extended_data_out = data_out[bufferposition:]
                    extended_data_out += bytes([0]) * (payload_per_frame-len(extended_data_out)-len(arqheader))
                    frame = arqheader + extended_data_out
                
                # update the bufferposition    
                # bufferposition = bufferposition_end
             
                tempbuffer.append(frame)
            
            structlog.get_logger("structlog").info("[TNC] ARQ | TX | FRAMES", mode=DATA_CHANNEL_MODE, fpb=TX_N_FRAMES_PER_BURST, retry=TX_N_RETRIES_PER_BURST)
            modem.transmit(mode=DATA_CHANNEL_MODE, repeats=1, repeat_delay=0, frames=tempbuffer)
            
            # lets wait for an ACK or RPT frame
            burstacktimeout = time.time() + BURST_ACK_TIMEOUT_SECONDS
            while not BURST_ACK_RECEIVED and not RPT_REQUEST_RECEIVED and not DATA_FRAME_ACK_RECEIVED and time.time() < burstacktimeout and DATA_CHANNEL_READY_FOR_DATA and static.ARQ_STATE == 'DATA':
                time.sleep(0.001)
                
            # once we received a burst ack, reset its state and break the RETRIES loop
            if BURST_ACK_RECEIVED:
                BURST_ACK_RECEIVED = False # reset ack state
                TX_N_RETRIES_PER_BURST = 0 # reset retries
                break #break retry loop

            if RPT_REQUEST_RECEIVED:
                pass

            if DATA_FRAME_ACK_RECEIVED:
                break #break retry loop
            
            
            # we need this part for leaving the repeat loop
            if not DATA_CHANNEL_READY_FOR_DATA:
                #print("not ready for data...leaving loop....")
                break
                
                
            # NEXT ATTEMPT
            print(f"ATTEMPT {TX_N_RETRIES_PER_BURST}/{TX_N_MAX_RETRIES_PER_BURST}")
        
        # update buffer position
        bufferposition = bufferposition_end
        # update stats
        calculate_transfer_rate_tx(tx_start_of_transmission, bufferposition_end, len(data_out)) 
        #GOING TO NEXT ITERATION
        

    if DATA_FRAME_ACK_RECEIVED:
        structlog.get_logger("structlog").info("ARQ | TX | DATA TRANSMITTED!", BytesPerMinute=static.ARQ_BYTES_PER_MINUTE, BitsPerSecond=static.ARQ_BITS_PER_SECOND)
    else:
        structlog.get_logger("structlog").info("ARQ | TX | TRANSMISSION FAILED OR TIME OUT!")

    # and last but not least doing a state cleanup
    static.TNC_STATE = 'IDLE'
    static.ARQ_STATE = 'IDLE'
    DATA_CHANNEL_READY_FOR_DATA = False
    BURST_ACK_RECEIVED = False
    RPT_REQUEST_RECEIVED = False
    DATA_FRAME_ACK_RECEIVED = False
   






















def burst_ack_received():
    global BURST_ACK_RECEIVED
    global DATA_CHANNEL_LAST_RECEIVED
    
    # only process data if we are in ARQ and BUSY state
    if static.ARQ_STATE == 'DATA':
        BURST_ACK_RECEIVED = True  # Force data loops of TNC to stop and continue with next frame
        DATA_CHANNEL_LAST_RECEIVED = int(time.time()) # we need to update our timeout timestamp


def frame_ack_received():
    global DATA_FRAME_ACK_RECEIVED
    global DATA_CHANNEL_LAST_RECEIVED

    # only process data if we are in ARQ and BUSY state
    if static.ARQ_STATE == 'DATA':       
        DATA_FRAME_ACK_RECEIVED = True  # Force data loops of TNC to stop and continue with next frame
        DATA_CHANNEL_LAST_RECEIVED = int(time.time()) # we need to update our timeout timestamp


def burst_rpt_received(data_in:bytes):
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


def open_dc_and_transmit(data_out:bytes, mode:int, n_frames_per_burst:int):
    global DATA_CHANNEL_READY_FOR_DATA
    
    static.TNC_STATE = 'BUSY'
    
    # we need to compress data for gettin a compression factor.
    # so we are compressing twice. This is not that nice and maybe theres another way
    # for calculating transmission statistics
    static.ARQ_COMPRESSION_FACTOR = len(data_out) / len(zlib.compress(data_out))
    
    
    arq_open_data_channel(mode, len(data_out))   
    # wait until data channel is open
    while not DATA_CHANNEL_READY_FOR_DATA:
        time.sleep(0.01)
 
    arq_transmit(data_out, mode, n_frames_per_burst)
    
def arq_open_data_channel(mode:int, data_len:int):
    global DATA_CHANNEL_READY_FOR_DATA
    global DATA_CHANNEL_LAST_RECEIVED
    
    DATA_CHANNEL_MAX_RETRIES        =   5           # N attempts for connecting to another station
    
    #DATA_CHANNEL_MODE = int(mode)    
    DATA_CHANNEL_LAST_RECEIVED = int(time.time())

    # multiply compression factor for reducing it from float to int
    compression_factor = int(static.ARQ_COMPRESSION_FACTOR * 10)

    connection_frame        = bytearray(14)
    connection_frame[:1]    = bytes([225])
    connection_frame[1:2]   = static.DXCALLSIGN_CRC8
    connection_frame[2:3]   = static.MYCALLSIGN_CRC8
    connection_frame[3:9]   = static.MYCALLSIGN
    connection_frame[9:12]  = data_len.to_bytes(3, byteorder='big')
    connection_frame[12:13] = bytes([compression_factor])
    
    
    
    while not DATA_CHANNEL_READY_FOR_DATA:
        time.sleep(0.01)
        for attempt in range(1,DATA_CHANNEL_MAX_RETRIES+1):
            static.INFO.append("DATACHANNEL;OPENING")
            
            structlog.get_logger("structlog").info("[TNC] ARQ | DATA | TX | [" + str(static.MYCALLSIGN, 'utf-8') + "]>> <<[" + str(static.DXCALLSIGN, 'utf-8') + "]", attempt=str(attempt) + "/" + str(DATA_CHANNEL_MAX_RETRIES))
            
            
              
            txbuffer = [connection_frame]
            modem.transmit(mode=14, repeats=1, repeat_delay=0, frames=txbuffer) 
            
            timeout = time.time() + 3    
            while time.time() < timeout:    
                time.sleep(0.01)
                # break if data channel is openend    
                if DATA_CHANNEL_READY_FOR_DATA:
                    break
            if DATA_CHANNEL_READY_FOR_DATA:
                break

            if not DATA_CHANNEL_READY_FOR_DATA and attempt == DATA_CHANNEL_MAX_RETRIES:
                static.INFO.append("DATACHANNEL;FAILED")
                
                structlog.get_logger("structlog").warning("[TNC] ARQ | TX | DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>>X<<[" + str(static.DXCALLSIGN, 'utf-8') + "]")
                static.TNC_STATE = 'IDLE'
                static.ARQ_STATE = 'IDLE'
                sys.exit() # close thread and so connection attempts


def arq_received_data_channel_opener(data_in:bytes):
    
    #global DATA_CHANNEL_MODE
    global DATA_CHANNEL_LAST_RECEIVED
    global RX_START_OF_TRANSMISSION
    
    
    static.INFO.append("DATACHANNEL;RECEIVEDOPENER")
    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')
    
    helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'DATA-CHANNEL', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
        
    structlog.get_logger("structlog").info("[TNC] ARQ | DATA | RX | [" + str(static.MYCALLSIGN, 'utf-8') + "]>> <<[" + str(static.DXCALLSIGN, 'utf-8') + "]")
    
    
    static.ARQ_STATE = 'DATA'
    static.TNC_STATE = 'BUSY'

    #mode = int.from_bytes(bytes(data_in[12:13]), "big")
    static.TOTAL_BYTES = int.from_bytes(bytes(data_in[9:12]), "big")
    static.ARQ_COMPRESSION_FACTOR = float(int.from_bytes(bytes(data_in[12:13]), "big") / 10)
    print(static.ARQ_COMPRESSION_FACTOR)
    print(int.from_bytes(bytes(data_in[12:13]), "big"))
    print(bytes(data_in[12:13]))
    DATA_CHANNEL_LAST_RECEIVED = int(time.time())

    connection_frame = bytearray(14)
    connection_frame[:1] = bytes([226])
    connection_frame[1:2] = static.DXCALLSIGN_CRC8
    connection_frame[2:3] = static.MYCALLSIGN_CRC8
    connection_frame[3:9] = static.MYCALLSIGN
    
    #connection_frame[12:13] = bytes([mode])

    
    
    txbuffer = [connection_frame]
    modem.transmit(mode=14, repeats=1, repeat_delay=0, frames=txbuffer)
    
    structlog.get_logger("structlog").info("[TNC] ARQ | DATA | RX | [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "]", snr=static.SNR)
    
    # set start of transmission for our statistics
    RX_START_OF_TRANSMISSION = time.time()
    
def arq_received_channel_is_open(data_in:bytes):

    global DATA_CHANNEL_LAST_RECEIVED
    global DATA_CHANNEL_READY_FOR_DATA
    global DATA_CHANNEL_MODE
    
    static.INFO.append("DATACHANNEL;OPEN")
    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')
    helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'DATA-CHANNEL', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
    
    DATA_CHANNEL_LAST_RECEIVED = int(time.time())

    # we are doing a mode check here, but this doesn't seem to be necessary since we have simultaneous decoding
    # we are forcing doing a transmission at the moment --> see else statement
    if DATA_CHANNEL_MODE == int.from_bytes(bytes(data_in[12:13]), "big"):
        structlog.get_logger("structlog").info("[TNC] ARQ | DATA | TX | [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "]", snr=static.SNR)

        # as soon as we set ARQ_STATE to DATA, transmission starts   
        static.ARQ_STATE = 'DATA'
        DATA_CHANNEL_READY_FOR_DATA = True
        DATA_CHANNEL_LAST_RECEIVED = int(time.time())
    else:
        structlog.get_logger("structlog").info("[TNC] ARQ | DATA | TX | [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "]", snr=static.SNR, info="wrong mode rcvd")
        # as soon as we set ARQ_STATE to DATA, transmission starts
        static.ARQ_STATE = 'DATA'
        DATA_CHANNEL_READY_FOR_DATA = True
        DATA_CHANNEL_LAST_RECEIVED = int(time.time())

# ############################################################################################################
# PING HANDLER
# ############################################################################################################

def transmit_ping(callsign:str):
    static.DXCALLSIGN = bytes(callsign, 'utf-8').rstrip(b'\x00')
    static.DXCALLSIGN_CRC8 = helpers.get_crc_8(static.DXCALLSIGN)
    
    static.INFO.append("PING;SENDING")
    structlog.get_logger("structlog").info("[TNC] PING REQ [" + str(static.MYCALLSIGN, 'utf-8') + "] >>> [" + str(static.DXCALLSIGN, 'utf-8') + "]" )

    ping_frame      = bytearray(14)
    ping_frame[:1]  = bytes([210])
    ping_frame[1:2] = static.DXCALLSIGN_CRC8
    ping_frame[2:3] = static.MYCALLSIGN_CRC8
    ping_frame[3:9] = static.MYCALLSIGN

    txbuffer = [ping_frame]
    modem.transmit(mode=14, repeats=1, repeat_delay=0, frames=txbuffer)    

def received_ping(data_in:bytes, frequency_offset:str):

    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')
    helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'PING', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
    
    static.INFO.append("PING;RECEIVING")

    structlog.get_logger("structlog").info("[TNC] PING REQ [" + str(static.MYCALLSIGN, 'utf-8') + "] <<< [" + str(static.DXCALLSIGN, 'utf-8') + "]", snr=static.SNR )

    ping_frame      = bytearray(14)
    ping_frame[:1]  = bytes([211])
    ping_frame[1:2] = static.DXCALLSIGN_CRC8
    ping_frame[2:3] = static.MYCALLSIGN_CRC8
    ping_frame[3:9] = static.MYGRID
    ping_frame[9:11] = frequency_offset.to_bytes(2, byteorder='big', signed=True)

    txbuffer = [ping_frame]
    modem.transmit(mode=14, repeats=1, repeat_delay=0, frames=txbuffer)

def received_ping_ack(data_in:bytes):

    static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
    static.DXGRID = bytes(data_in[3:9]).rstrip(b'\x00')
       
    helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'PING-ACK', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
    
    static.INFO.append("PING;RECEIVEDACK")

    structlog.get_logger("structlog").info("[TNC] PING ACK [" + str(static.MYCALLSIGN, 'utf-8') + "] >|< [" + str(static.DXCALLSIGN, 'utf-8') + "]", snr=static.SNR )
    static.TNC_STATE = 'IDLE'

# ############################################################################################################
# BROADCAST HANDLER
# ############################################################################################################

def run_beacon(interval:int):
    try:
        structlog.get_logger("structlog").warning("[TNC] Starting beacon!", interval=interval)
        
        while static.BEACON_STATE and static.ARQ_STATE == 'IDLE':

            beacon_frame = bytearray(14)
            beacon_frame[:1]   = bytes([230])
            beacon_frame[1:2]  = b'\x01'
            beacon_frame[2:8]  = static.MYCALLSIGN
            beacon_frame[8:14] = static.MYGRID
        
            static.INFO.append("BEACON;SENDING")
            structlog.get_logger("structlog").info("[TNC] Sending beacon!", interval=interval)  
            
            txbuffer = [beacon_frame]
            modem.transmit(mode=14, repeats=1, repeat_delay=0, frames=txbuffer)
            time.sleep(interval)
            
                                            
    except Exception as e:
        print(e)

def received_beacon(data_in:bytes):
# here we add the received station to the heard stations buffer
    dxcallsign = bytes(data_in[2:8]).rstrip(b'\x00')
    dxgrid = bytes(data_in[8:14]).rstrip(b'\x00')
    static.INFO.append("BEACON;RECEIVING")
    structlog.get_logger("structlog").info("[TNC] BEACON RCVD [" + str(dxcallsign, 'utf-8') + "]["+ str(dxgrid, 'utf-8') +"] ", snr=static.SNR)
    helpers.add_to_heard_stations(dxcallsign,dxgrid, 'BEACON', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)


    
    
def transmit_cq():
    logging.info("CQ CQ CQ")
    static.INFO.append("CQ;SENDING")
    
    cq_frame       = bytearray(14)
    cq_frame[:1]   = bytes([200])
    cq_frame[1:2]  = b'\x01'
    #cq_frame[2:3] = static.MYCALLSIGN_CRC8
    #cq_frame[3:9] = static.MYCALLSIGN
    cq_frame[2:8]  = static.MYCALLSIGN
    cq_frame[8:14] = static.MYGRID
    
    txbuffer = [cq_frame]
    modem.transmit(mode=14, repeats=1, repeat_delay=1000, frames=txbuffer)
    #while not modem.transmit(14, 1, txbuffer):
    #    pass


def received_cq(data_in:bytes):
    # here we add the received station to the heard stations buffer
    dxcallsign = bytes(data_in[2:8]).rstrip(b'\x00')
    dxgrid = bytes(data_in[8:14]).rstrip(b'\x00')
    static.INFO.append("CQ;RECEIVING")
    structlog.get_logger("structlog").info("[TNC] CQ RCVD [" + str(dxcallsign, 'utf-8') + "]["+ str(dxgrid, 'utf-8') +"] ", snr=static.SNR)
    helpers.add_to_heard_stations(dxcallsign,dxgrid, 'CQ CQ CQ', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)




def arq_reset_ack(state:bool):
    """
    Author: DJ2LS
    """
    global BURST_ACK_RECEIVED
    global RPT_REQUEST_RECEIVED
    global DATA_FRAME_ACK_RECEIVED
    
    BURST_ACK_RECEIVED = state
    RPT_REQUEST_RECEIVED = state
    DATA_FRAME_ACK_RECEIVED = state


def calculate_transfer_rate_rx(rx_start_of_transmission:float, receivedbytes:int) -> list:
    
    try: 
        static.ARQ_TRANSMISSION_PERCENT = int((receivedbytes*static.ARQ_COMPRESSION_FACTOR / static.TOTAL_BYTES) * 100)

        transmissiontime = time.time() - rx_start_of_transmission
        
        if receivedbytes > 0:
            static.ARQ_BITS_PER_SECOND = int((receivedbytes*8) / transmissiontime)
            static.ARQ_BYTES_PER_MINUTE = int((receivedbytes) / (transmissiontime/60))
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




def calculate_transfer_rate_tx(tx_start_of_transmission:float, sentbytes:int, tx_buffer_length:int) -> list:
    
    try:
        static.ARQ_TRANSMISSION_PERCENT = int((sentbytes / tx_buffer_length) * 100)
        
        transmissiontime = time.time() - tx_start_of_transmission

        if sentbytes > 0:
            
            static.ARQ_BITS_PER_SECOND = int((sentbytes*8) / transmissiontime)
            static.ARQ_BYTES_PER_MINUTE = int((sentbytes) / (transmissiontime/60))

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
        time.sleep(0.5)
        data_channel_keep_alive_watchdog()


def data_channel_keep_alive_watchdog():
    """
    Author: DJ2LS

    """
    global DATA_CHANNEL_LAST_RECEIVED
    global DATA_CHANNEL_READY_FOR_DATA
    global BURST_ACK_RECEIVED
    global RPT_REQUEST_RECEIVED
    global DATA_FRAME_ACK_RECEIVED
    
    # and not static.ARQ_SEND_KEEP_ALIVE:
    if static.ARQ_STATE == 'DATA' and static.TNC_STATE == 'BUSY':
        time.sleep(0.01)
        if DATA_CHANNEL_LAST_RECEIVED + 30 > time.time():
            time.sleep(0.01)
            #pass
        else:
            DATA_CHANNEL_LAST_RECEIVED = 0
            logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]<<T>>[" + str(static.DXCALLSIGN, 'utf-8') + "]")
            #arq_reset_frame_machine()  

            static.TNC_STATE = 'IDLE'
            static.ARQ_STATE = 'IDLE'
            DATA_CHANNEL_READY_FOR_DATA = False
            BURST_ACK_RECEIVED = False
            RPT_REQUEST_RECEIVED = False
            DATA_FRAME_ACK_RECEIVED = False
            
            
            


# START THE THREAD FOR THE TIMEOUT WATCHDOG
WATCHDOG_SERVER_THREAD = threading.Thread(target=watchdog, name="watchdog")
WATCHDOG_SERVER_THREAD.start()  





              

