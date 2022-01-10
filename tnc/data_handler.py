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
import codec2
import queue



TESTMODE = False
 
DATA_QUEUE_TRANSMIT = queue.Queue()
DATA_QUEUE_RECEIVED = queue.Queue()

class DATA():

    def __init__(self):

        print("init DATA handler...")
        
        self.data_queue_transmit = DATA_QUEUE_TRANSMIT
        self.data_queue_received = DATA_QUEUE_RECEIVED


        self.data_channel_last_received      =   0.0         # time of last "live sign" of a frame      
        self.burst_ack_snr                  =   0           # SNR from received ack frames
        self.burst_ack              =   False       # if we received an acknowledge frame for a burst
        self.data_frame_ack_received         =   False       # if we received an acknowledge frame for a data frame
        self.rpt_request_received            =   False       # if we received an request for repeater frames
        self.rpt_request_buffer              =   []          # requested frames, saved in a list           
        self.rx_start_of_transmission        =   0           # time of transmission start
        self.data_frame_bof                  =   b'BOF'#b'\xAA\xAA' # 2 bytes for the BOF End of File indicator in a data frame
        self.data_frame_eof                  =   b'EOF'#b'\xFF\xFF' # 2 bytes for the EOF End of File indicator in a data frame

        self.mode_list = [14,14,14,12,10] # mode list of available modes, each mode will be used 2times per speed level

        self.rx_frame_bof_received = False
        self.rx_frame_eof_received = False

        self.transmission_timeout = 360 # transmission timeout in seco

        worker_thread_transmit = threading.Thread(target=self.worker_transmit, name="worker thread transmit")
        worker_thread_transmit.start()
         
        worker_thread_receive = threading.Thread(target=self.worker_receive, name="worker thread receive")
        worker_thread_receive.start()
        
        # START THE THREAD FOR THE TIMEOUT WATCHDOG
        watchdog_thread = threading.Thread(target=self.watchdog, name="watchdog")
        watchdog_thread.start()
        
        
    def worker_transmit(self):
         while True:
            data = self.data_queue_transmit.get()
            # [0] Command

            if data[0] == 'CQ':
                # [0] CQ
                self.transmit_cq()
            elif data[0] == 'STOP':
                self.stop_transmission()
            
            elif data[0] == 'PING':
                # [0] PING
                # [1] dxcallsign
                self.transmit_ping(data[1])
                
            elif data[0] == 'BEACON':
                # [0] BEACON
                # [1] INTERVAL int
                # [2] STATE bool
                self.run_beacon(data[1])

            elif data[0] == 'ARQ_FILE':
                # [0] ARQ_FILE
                # [1] DATA_OUT bytes
                # [2] MODE int
                # [3] N_FRAMES_PER_BURST int
                self.open_dc_and_transmit(data[1], data[2], data[3])

            elif data[0] == 'ARQ_MESSAGE':
                # [0] ARQ_FILE
                # [1] DATA_OUT bytes
                # [2] MODE int
                # [3] N_FRAMES_PER_BURST int
                self.open_dc_and_transmit(data[1], data[2], data[3])
                
                
            else:
                # wrong command
                pass
            
            
    def worker_receive(self):
         while True:
            data = self.data_queue_received.get()
            # [0] bytes
            # [1] freedv instance
            # [2] bytes_per_frame
            self.process_data(bytes_out=data[0],freedv=data[1],bytes_per_frame=data[2])         


    def process_data(self, bytes_out, freedv, bytes_per_frame):    
        # forward data only if broadcast or we are the receiver
        # bytes_out[1:2] == callsign check for signalling frames, 
        # bytes_out[6:7] == callsign check for data frames, 
        # bytes_out[1:2] == b'\x01' --> broadcasts like CQ with n frames per_burst = 1
        # we could also create an own function, which returns True. 

        if bytes(bytes_out[1:2]) == static.MYCALLSIGN_CRC8 or bytes(bytes_out[3:4]) == static.MYCALLSIGN_CRC8 or bytes(bytes_out[1:2]) == b'\x01':

            # CHECK IF FRAMETYPE IS BETWEEN 10 and 50 ------------------------
            frametype = int.from_bytes(bytes(bytes_out[:1]), "big")
            frame = frametype - 10
            n_frames_per_burst = int.from_bytes(bytes(bytes_out[1:2]), "big")

            #frequency_offset = self.get_frequency_offset(freedv)
            #print("Freq-Offset: " + str(frequency_offset))
            
            if 50 >= frametype >= 10:
                # get snr of received data
                #snr = self.calculate_snr(freedv)
                # we need to find a wy fixing this because of mooving to class system this isn't working anymore
                snr = static.SNR
                structlog.get_logger("structlog").debug("[TNC] RX SNR", snr=snr)
                # send payload data to arq checker without CRC16
                self.arq_data_received(bytes(bytes_out[:-2]), bytes_per_frame, snr, freedv)

                # if we received the last frame of a burst or the last remaining rpt frame, do a modem unsync
                #if static.RX_BURST_BUFFER.count(None) <= 1 or (frame+1) == n_frames_per_burst:
                #    structlog.get_logger("structlog").debug(f"LAST FRAME OF BURST --> UNSYNC {frame+1}/{n_frames_per_burst}")
                #    self.c_lib.freedv_set_sync(freedv, 0)

            # BURST ACK
            elif frametype == 60:
                structlog.get_logger("structlog").debug("ACK RECEIVED....")
                self.burst_ack_received(bytes_out[:-2])

            # FRAME ACK
            elif frametype == 61:
                structlog.get_logger("structlog").debug("FRAME ACK RECEIVED....")
                self.frame_ack_received()

            # FRAME RPT
            elif frametype == 62:
                structlog.get_logger("structlog").debug("REPEAT REQUEST RECEIVED....")
                self.burst_rpt_received(bytes_out[:-2])

            # FRAME NACK
            elif frametype == 63:
                structlog.get_logger("structlog").debug("FRAME NOT ACK RECEIVED....")
                self.frame_nack_received(bytes_out[:-2])

            # CQ FRAME
            elif frametype == 200:
                structlog.get_logger("structlog").debug("CQ RECEIVED....")
                self.received_cq(bytes_out[:-2])

            # PING FRAME
            elif frametype == 210:
                structlog.get_logger("structlog").debug("PING RECEIVED....")
                # = self.get_frequency_offset(freedv)
                # we need to fix this later
                frequency_offset = 0
                #print("Freq-Offset: " + str(frequency_offset))
                self.received_ping(bytes_out[:-2], frequency_offset)
                

            # PING ACK
            elif frametype == 211:
                structlog.get_logger("structlog").debug("PING ACK RECEIVED....")
                # early detection of frequency offset
                #frequency_offset = int.from_bytes(bytes(bytes_out[9:11]), "big", signed=True)
                #print("Freq-Offset: " + str(frequency_offset))
                #current_frequency = self.my_rig.get_freq()
                #corrected_frequency = current_frequency + frequency_offset
                # temporarely disabled this feature, beacuse it may cause some confusion.
                # we also have problems if we are operating at band bordes like 7.000Mhz
                # If we get a corrected frequency less 7.000 Mhz, Ham Radio devices will not transmit...
                #self.my_rig.set_vfo(Hamlib.RIG_VFO_A)
                #self.my_rig.set_freq(Hamlib.RIG_VFO_A, corrected_frequency)
                self.received_ping_ack(bytes_out[:-2])

            # ARQ FILE TRANSFER RECEIVED!
            elif frametype == 225:
                structlog.get_logger("structlog").debug("ARQ arq_received_data_channel_opener")
                self.arq_received_data_channel_opener(bytes_out[:-2])
    
            # ARQ CHANNEL IS OPENED
            elif frametype == 226:
                structlog.get_logger("structlog").debug("ARQ arq_received_channel_is_open")
                self.arq_received_channel_is_open(bytes_out[:-2])

    
            # ARQ STOP TRANSMISSION
            elif frametype == 227:
                structlog.get_logger("structlog").debug("ARQ received stop transmis")
                self.received_stop_transmission()

            # ARQ CONNECT ACK / KEEP ALIVE
            # this is outdated and we may remove it
            elif frametype == 230:
                structlog.get_logger("structlog").debug("BEACON RECEIVED")
                self.received_beacon(bytes_out[:-2])

            # TESTFRAMES
            elif frametype == 255:
                structlog.get_logger("structlog").debug("TESTFRAME RECEIVED", frame=bytes_out[:])
                               
            else:
                structlog.get_logger("structlog").warning("[TNC] ARQ - other frame type", frametype=frametype)

        else:
            # for debugging purposes to receive all data
            structlog.get_logger("structlog").debug("[TNC] Unknown frame received", frame=bytes_out[:-2])



    def arq_data_received(self, data_in:bytes, bytes_per_frame:int, snr:int, freedv):
        data_in = bytes(data_in)    
        
        global TESTMODE
        # only process data if we are in ARQ and BUSY state else return to quit
        if not static.ARQ_STATE and static.TNC_STATE != 'BUSY':
            return

        RX_PAYLOAD_PER_MODEM_FRAME = bytes_per_frame - 2    # payload per moden frame

        static.TNC_STATE = 'BUSY'
        static.ARQ_STATE = True
        static.INFO.append("ARQ;RECEIVING")
        self.data_channel_last_received = int(time.time())
            
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
        
        structlog.get_logger("structlog").debug("[TNC] static.RX_BURST_BUFFER", buffer=static.RX_BURST_BUFFER)
        '''
        check if we received all frames per burst by checking if burst buffer has no more "Nones"
        this is the ideal case because we received all data
        '''
        if not None in static.RX_BURST_BUFFER:
            # then iterate through burst buffer and stick the burst together
            # the temp burst buffer is needed for checking, if we already recevied data
            temp_burst_buffer = b''
            for i in range(0,len(static.RX_BURST_BUFFER)):
                #static.RX_FRAME_BUFFER += static.RX_BURST_BUFFER[i]
                temp_burst_buffer += static.RX_BURST_BUFFER[i]

            # if frame buffer ends not with the current frame, we are going to append new data
            # if data already exists, we received the frame correctly, but the ACK frame didnt receive its destination (ISS)
            if not static.RX_FRAME_BUFFER.endswith(temp_burst_buffer):
                static.RX_FRAME_BUFFER += temp_burst_buffer
                static.RX_BURST_BUFFER = []
            else:
                structlog.get_logger("structlog").info("[TNC] ARQ | RX | Frame already received - sending ACK again")
                static.RX_BURST_BUFFER = []

            # lets check if we didnt receive a BOF and EOF yet to avoid sending ack frames if we already received all data
            if not self.rx_frame_bof_received and not self.rx_frame_eof_received and data_in.find(self.data_frame_eof) < 0:  
                
                # create an ack frame
                ack_frame = bytearray(14)
                ack_frame[:1] = bytes([60])
                ack_frame[1:2] = static.DXCALLSIGN_CRC8
                ack_frame[2:3] = static.MYCALLSIGN_CRC8
                ack_frame[3:4] = bytes([int(snr)])
                # and transmit it
                txbuffer = [ack_frame]
                structlog.get_logger("structlog").info("[TNC] ARQ | RX | ACK")
                static.TRANSMITTING = True
                modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])
                # wait while transmitting
                while static.TRANSMITTING:
                    time.sleep(0.01)
                self.calculate_transfer_rate_rx(self.rx_start_of_transmission, len(static.RX_FRAME_BUFFER))   

        
        # check if we received last frame of burst and we have "Nones" in our rx buffer
        # this is an indicator for missed frames.
        # with this way of doing this, we always MUST receive the last frame of a burst otherwise the entire 
        # burst is lost
        elif RX_N_FRAME_OF_BURST == RX_N_FRAMES_PER_BURST -1:
            # check where a None is in our burst buffer and do frame+1, beacuse lists start at 0
            missing_frames = [(frame+1) for frame, element in enumerate(static.RX_BURST_BUFFER) if element == None]
            
            structlog.get_logger("structlog").debug("all frames per burst received", frame=RX_N_FRAME_OF_BURST, frames=RX_N_FRAMES_PER_BURST)
                
            # set n frames per burst to modem
            # this is an idea so its not getting lost....
            # we need to work on this 
            codec2.api.freedv_set_frames_per_burst(freedv,len(missing_frames))
            
            
            # then create a repeat frame 
            rpt_frame       = bytearray(14)
            rpt_frame[:1]   = bytes([62])
            rpt_frame[1:2]  = static.DXCALLSIGN_CRC8
            rpt_frame[2:3]  = static.MYCALLSIGN_CRC8
            rpt_frame[3:9]  = missing_frames

            # and transmit it
            txbuffer = [rpt_frame]
            structlog.get_logger("structlog").info("[TNC] ARQ | RX | Requesting", frames=missing_frames)
            static.TRANSMITTING = True
            modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])
            # wait while transmitting
            while static.TRANSMITTING:
                time.sleep(0.01)
            self.calculate_transfer_rate_rx(self.rx_start_of_transmission, len(static.RX_FRAME_BUFFER))
            
            
        # we should never reach this point
        else:
            structlog.get_logger("structlog").error("we shouldnt reach this point...", frame=RX_N_FRAME_OF_BURST, frames=RX_N_FRAMES_PER_BURST)
        
        # We have a BOF and EOF flag in our data. If we received both we received our frame.
        # In case of loosing data but we received already a BOF and EOF we need to make sure, we 
        # received the complete last burst by checking it for Nones    
        bof_position = static.RX_FRAME_BUFFER.find(self.data_frame_bof)
        eof_position = static.RX_FRAME_BUFFER.find(self.data_frame_eof)
        if bof_position >= 0 and eof_position > 0 and not None in static.RX_BURST_BUFFER:
            print(f"bof_position {bof_position} / eof_position {eof_position}")
            self.rx_frame_bof_received = True
            self.rx_frame_eof_received = True
         
            #now extract raw data from buffer
            payload = static.RX_FRAME_BUFFER[bof_position+len(self.data_frame_bof):eof_position]
            # get the data frame crc

            data_frame_crc = payload[:2]
            data_frame = payload[2:]

            data_frame_crc_received = helpers.get_crc_16(data_frame)
            # check if data_frame_crc is equal with received crc
            if data_frame_crc == data_frame_crc_received:
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
                    #structlog.get_logger("structlog").debug("RECEIVED FILE --> MOVING DATA TO RX BUFFER")
                    static.RX_BUFFER.append([static.DXCALLSIGN,static.DXGRID,int(time.time()), data_frame])
                    
                # if datatype is a file, we append to RX_MSG_BUFFER, which contains messages only            
                if rawdata["dt"] == "m":
                    static.RX_MSG_BUFFER.append([static.DXCALLSIGN,static.DXGRID,int(time.time()), data_frame])
                    #structlog.get_logger("structlog").debug("RECEIVED MESSAGE --> MOVING DATA TO MESSAGE BUFFER")
                
                # BUILDING ACK FRAME FOR DATA FRAME
                ack_frame       = bytearray(14)
                ack_frame[:1]   = bytes([61])
                ack_frame[1:2]  = static.DXCALLSIGN_CRC8
                ack_frame[2:3]  = static.MYCALLSIGN_CRC8

                # TRANSMIT ACK FRAME FOR BURST
                structlog.get_logger("structlog").info("[TNC] ARQ | RX | SENDING DATA FRAME ACK", snr=static.SNR, crc=data_frame_crc.hex())
                txbuffer = [ack_frame]
                static.TRANSMITTING = True
                modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])
                # wait while transmitting
                while static.TRANSMITTING:
                    time.sleep(0.01)
                # update our statistics AFTER the frame ACK
                self.calculate_transfer_rate_rx(self.rx_start_of_transmission, len(static.RX_FRAME_BUFFER))
                           
                structlog.get_logger("structlog").info("[TNC] | RX | DATACHANNEL [" + str(static.MYCALLSIGN, 'utf-8') + "]<< >>[" + str(static.DXCALLSIGN, 'utf-8') + "]", snr=static.SNR)

            else:
                static.INFO.append("ARQ;RECEIVING;FAILED")
                structlog.get_logger("structlog").warning("[TNC] ARQ | RX | DATA FRAME NOT SUCESSFULLY RECEIVED!", e="wrong crc", expected=data_frame_crc, received=data_frame_crc_received)

                # BUILDING NACK FRAME FOR DATA FRAME
                nack_frame       = bytearray(14)
                nack_frame[:1]   = bytes([63])
                nack_frame[1:2]  = static.DXCALLSIGN_CRC8
                nack_frame[2:3]  = static.MYCALLSIGN_CRC8     
                
                # TRANSMIT NACK FRAME FOR BURST
                txbuffer = [nack_frame]
                static.TRANSMITTING = True
                modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])
                # wait while transmitting
                while static.TRANSMITTING:
                    time.sleep(0.01)
            # And finally we do a cleanup of our buffers and states
            # do cleanup only when not in testmode
            if not TESTMODE:
                self.arq_cleanup()        
            


    def arq_transmit(self, data_out:bytes, mode:int, n_frames_per_burst:int):

        global TESTMODE
        
        self.speed_level = len(self.mode_list) - 1    # speed level for selecting mode
        

        TX_N_SENT_BYTES                = 0                      # already sent bytes per data frame
        self.tx_n_retry_of_burst          = 0                     # retries we already sent data
        TX_N_MAX_RETRIES_PER_BURST      = 50                     # max amount of retries we sent before frame is lost
        TX_N_FRAMES_PER_BURST           = n_frames_per_burst    # amount of n frames per burst    
        TX_BUFFER = []  # our buffer for appending new data
        
        # TIMEOUTS
        BURST_ACK_TIMEOUT_SECONDS       =   3.0         # timeout for burst  acknowledges
        DATA_FRAME_ACK_TIMEOUT_SECONDS  =   3.0        # timeout for data frame acknowledges
        RPT_ACK_TIMEOUT_SECONDS         =   3.0        # timeout for rpt frame acknowledges


        # save len of data_out to TOTAL_BYTES for our statistics --> kBytes
        static.TOTAL_BYTES = round(len(data_out) / 1024, 2)
        
        
        static.INFO.append("ARQ;TRANSMITTING")
        structlog.get_logger("structlog").info("[TNC] | TX | DATACHANNEL", mode=mode, kBytes=static.TOTAL_BYTES)

        
        # compression
        data_frame_compressed = zlib.compress(data_out)
        static.ARQ_COMPRESSION_FACTOR = len(data_out) / len(data_frame_compressed)
        data_out = data_frame_compressed    

        # reset statistics
        tx_start_of_transmission = time.time()
        self.calculate_transfer_rate_tx(tx_start_of_transmission, 0, len(data_out))

        # append a crc and beginn and end of file indicators
        frame_payload_crc = helpers.get_crc_16(data_out)
        data_out = self.data_frame_bof + frame_payload_crc + data_out + self.data_frame_eof
        
        #initial bufferposition is 0
        bufferposition = 0

        # iterate through data out buffer
        while bufferposition < len(data_out) and not self.data_frame_ack_received and static.ARQ_STATE:

                       
            # we have TX_N_MAX_RETRIES_PER_BURST attempts for sending a burst
            for self.tx_n_retry_of_burst in range(0,TX_N_MAX_RETRIES_PER_BURST):

                # AUTO MODE SELECTION
                # mode 255 == AUTO MODE
                # force usage of selected mode
                if mode != 255:
                    data_mode = mode
                    structlog.get_logger("structlog").debug("FIXED MODE", mode=data_mode)

                else:
                    # we are doing a modulo check of transmission retries of the actual burst
                    # every 2nd retry which failes, decreases speedlevel by 1.
                    # as soon as we received an ACK for the current burst, speed_level will increase
                    # by 1.
                    # the can be optimised by checking the optimal speed level for the current conditions
                    print(self.tx_n_retry_of_burst)
                    if not self.tx_n_retry_of_burst % 2 and self.tx_n_retry_of_burst > 0:
                        self.speed_level -= 1
                        if self.speed_level < 0:
                            self.speed_level = 0
                    
                    #if self.tx_n_retry_of_burst <= 1:
                    #    self.speed_level += 1
                    #    if self.speed_level >= len(self.mode_list)-1:
                    #        self.speed_level = len(self.mode_list)-1
                    data_mode = self.mode_list[self.speed_level]
                    print(f"data_mode {data_mode} speed_level {self.speed_level}")
                    
           
                        

                # payload information
                payload_per_frame = modem.get_bytes_per_frame(data_mode) -2 

                # tempbuffer list for storing our data frames
                tempbuffer = []
            
                # append data frames with TX_N_FRAMES_PER_BURST to tempbuffer
                # this part ineeds to a completly rewrite!
                # TX_NF_RAMES_PER_BURST = 1 is working

                arqheader = bytearray()
                arqheader[:1] = bytes([10]) #bytes([10 + i])
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
                    
                    
                # append frame to tempbuffer for transmission
                tempbuffer.append(frame)
                
                structlog.get_logger("structlog").debug("[TNC] tempbuffer", tempbuffer=tempbuffer)
                structlog.get_logger("structlog").info("[TNC] ARQ | TX | FRAMES", mode=data_mode, fpb=TX_N_FRAMES_PER_BURST, retry=self.tx_n_retry_of_burst)
                
                # we need to set our TRANSMITTING flag before we are adding an object the transmit queue
                # this is not that nice, we could improve this somehow
                static.TRANSMITTING = True
                modem.MODEM_TRANSMIT_QUEUE.put([data_mode,1,0,tempbuffer])
                
                # wait while transmitting
                while static.TRANSMITTING:
                    time.sleep(0.01)
                
                # after transmission finished  wait for an ACK or RPT frame
                burstacktimeout = time.time() + BURST_ACK_TIMEOUT_SECONDS
                while not self.burst_ack and not self.rpt_request_received and not self.data_frame_ack_received and time.time() < burstacktimeout and static.ARQ_STATE:
                    time.sleep(0.01)
                    structlog.get_logger("structlog").debug("[TNC] waiting for ack", burst_ack=self.burst_ack, frame_ack = self.data_frame_ack_received, arq_state = static.ARQ_STATE)
                    
                    
                # once we received a burst ack, reset its state and break the RETRIES loop
                if self.burst_ack:
                    self.burst_ack = False # reset ack state
                    self.tx_n_retry_of_burst = 0 # reset retries
                    break #break retry loop

                if self.rpt_request_received:
                    pass

                if self.data_frame_ack_received:
                    break #break retry loop
                
                
                # we need this part for leaving the repeat loop
                # static.ARQ_STATE == 'DATA' --> when stopping transmission manually
                if not static.ARQ_STATE:
                    #print("not ready for data...leaving loop....")
                    break
                    
                    
                # NEXT ATTEMPT
                structlog.get_logger("structlog").debug("ATTEMPT", retry=self.tx_n_retry_of_burst, maxretries=TX_N_MAX_RETRIES_PER_BURST)
            
            # update buffer position
            bufferposition = bufferposition_end

        #     # update stats
            self.calculate_transfer_rate_tx(tx_start_of_transmission, bufferposition_end, len(data_out)) 
            #GOING TO NEXT ITERATION
            

        if self.data_frame_ack_received:
        
            static.INFO.append("ARQ;TRANSMITTING;SUCCESS")

            structlog.get_logger("structlog").info("ARQ | TX | DATA TRANSMITTED!", BytesPerMinute=static.ARQ_BYTES_PER_MINUTE, BitsPerSecond=static.ARQ_BITS_PER_SECOND)


                
        else:
            static.INFO.append("ARQ;TRANSMITTING;FAILED")
            structlog.get_logger("structlog").info("ARQ | TX | TRANSMISSION FAILED OR TIME OUT!")

        # and last but not least doing a state cleanup    
        # do cleanup only when not in testmode
        if not TESTMODE:
            self.arq_cleanup()

        # quit after transmission
        if TESTMODE:
            import os
            os._exit(0)



    # signalling frames received
    def burst_ack_received(self, data_in:bytes):
        
        # increase speed level if we received a burst ack
        self.speed_level += 1
        if self.speed_level >= len(self.mode_list)-1:
             self.speed_level = len(self.mode_list)-1
        
        # only process data if we are in ARQ and BUSY state
        if static.ARQ_STATE:
            self.burst_ack = True  # Force data loops of TNC to stop and continue with next frame
            self.data_channel_last_received = int(time.time()) # we need to update our timeout timestamp
            self.burst_ack_snr= int.from_bytes(bytes(data_in[3:4]), "big")


    def frame_ack_received(self):
        # only process data if we are in ARQ and BUSY state
        if static.ARQ_STATE:       
            self.data_frame_ack_received = True  # Force data loops of TNC to stop and continue with next frame
            self.data_channel_last_received = int(time.time()) # we need to update our timeout timestamp


    def frame_nack_received(self, data_in:bytes):
        static.INFO.append("ARQ;TRANSMITTING;FAILED")
        if not TESTMODE:
            self.arq_cleanup()



    def burst_rpt_received(self, data_in:bytes):

        # only process data if we are in ARQ and BUSY state
        if static.ARQ_STATE and static.TNC_STATE == 'BUSY':
               
            self.rpt_request_received = True
            self.data_channel_last_received = int(time.time()) # we need to update our timeout timestamp
            self.rpt_request_buffer = []

            missing_area = bytes(data_in[3:12])  # 1:9

            for i in range(0, 6, 2):
                if not missing_area[i:i + 2].endswith(b'\x00\x00'):
                    missing = missing_area[i:i + 2]
                    self.rpt_request_buffer.insert(0, missing)



    # ############################################################################################################
    # ARQ DATA CHANNEL HANDLER
    # ############################################################################################################


    def open_dc_and_transmit(self, data_out:bytes, mode:int, n_frames_per_burst:int):
        
        static.TNC_STATE = 'BUSY'
        
        # we need to compress data for gettin a compression factor.
        # so we are compressing twice. This is not that nice and maybe theres another way
        # for calculating transmission statistics
        static.ARQ_COMPRESSION_FACTOR = len(data_out) / len(zlib.compress(data_out))
        
        
        
        self.arq_open_data_channel(mode, len(data_out), n_frames_per_burst)   
        # wait until data channel is open
        while not static.ARQ_STATE:
            time.sleep(0.01)
     
        self.arq_transmit(data_out, mode, n_frames_per_burst)
    
    def arq_open_data_channel(self, mode:int, data_len:int, n_frames_per_burst:int):
        
        DATA_CHANNEL_MAX_RETRIES        =   5           # N attempts for connecting to another station
        self.data_channel_last_received = int(time.time())

        # devide by 1024 for getting Bytes -> kBytes 
        data_len = int(data_len / 1024)

        # multiply compression factor for reducing it from float to int
        compression_factor = int(static.ARQ_COMPRESSION_FACTOR * 10)

        connection_frame        = bytearray(14)
        connection_frame[:1]    = bytes([225])
        connection_frame[1:2]   = static.DXCALLSIGN_CRC8
        connection_frame[2:3]   = static.MYCALLSIGN_CRC8
        connection_frame[3:9]   = static.MYCALLSIGN
        connection_frame[9:10]   = bytes([0]) # ONE BYTE LEFT FOR OTHER THINGS
        connection_frame[10:12]  = data_len.to_bytes(2, byteorder='big')
        connection_frame[12:13] = bytes([compression_factor])
        connection_frame[13:14] = bytes([n_frames_per_burst])    
        
        while not static.ARQ_STATE:
            time.sleep(0.01)
            for attempt in range(1,DATA_CHANNEL_MAX_RETRIES+1):
                static.INFO.append("DATACHANNEL;OPENING")
                
                structlog.get_logger("structlog").info("[TNC] ARQ | DATA | TX | [" + str(static.MYCALLSIGN, 'utf-8') + "]>> <<[" + str(static.DXCALLSIGN, 'utf-8') + "]", attempt=str(attempt) + "/" + str(DATA_CHANNEL_MAX_RETRIES))
                
                txbuffer = [connection_frame]
                
                static.TRANSMITTING = True
                modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])                
                # wait while transmitting
                while static.TRANSMITTING:
                    time.sleep(0.01)
                
                timeout = time.time() + 3    
                while time.time() < timeout:    
                    time.sleep(0.01)
                    # break if data channel is openend    
                    if static.ARQ_STATE:
                        break
                if static.ARQ_STATE:
                    break

                if not static.ARQ_STATE and attempt == DATA_CHANNEL_MAX_RETRIES:
                    static.INFO.append("DATACHANNEL;FAILED")
                    
                    structlog.get_logger("structlog").warning("[TNC] ARQ | TX | DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>>X<<[" + str(static.DXCALLSIGN, 'utf-8') + "]")
                    if not TESTMODE:
                        self.arq_cleanup()
                    sys.exit() # close thread and so connection attempts


    def arq_received_data_channel_opener(self, data_in:bytes):

        static.INFO.append("DATACHANNEL;RECEIVEDOPENER")
        static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
        static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')

        static.TOTAL_BYTES = int.from_bytes(bytes(data_in[10:12]), "big") # kBytes
        static.ARQ_COMPRESSION_FACTOR = float(int.from_bytes(bytes(data_in[12:13]), "big") / 10)
        n_frames_per_burst = int.from_bytes(bytes(data_in[13:14]), "big")    
        
        #we need to find a way how to do this. this isn't working anymore since we mode to a class based module
        #modem.set_frames_per_burst(n_frames_per_burst)

        helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'DATA-CHANNEL', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
            
        structlog.get_logger("structlog").info("[TNC] ARQ | DATA | RX | [" + str(static.MYCALLSIGN, 'utf-8') + "]>> <<[" + str(static.DXCALLSIGN, 'utf-8') + "]")
           
        static.ARQ_STATE = True
        static.TNC_STATE = 'BUSY'

        self.data_channel_last_received = int(time.time())

        connection_frame = bytearray(14)
        connection_frame[:1] = bytes([226])
        connection_frame[1:2] = static.DXCALLSIGN_CRC8
        connection_frame[2:3] = static.MYCALLSIGN_CRC8
        connection_frame[3:9] = static.MYCALLSIGN

        txbuffer = [connection_frame]
        
        static.TRANSMITTING = True
        modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])
        # wait while transmitting
        while static.TRANSMITTING:
            time.sleep(0.01)
        structlog.get_logger("structlog").info("[TNC] ARQ | DATA | RX | [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "]", snr=static.SNR)
        
        # set start of transmission for our statistics
        self.rx_start_of_transmission = time.time()
    
    def arq_received_channel_is_open(self, data_in:bytes):
        
        static.INFO.append("DATACHANNEL;OPEN")
        static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
        static.DXCALLSIGN = bytes(data_in[3:9]).rstrip(b'\x00')
        helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'DATA-CHANNEL', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
        
        self.data_channel_last_received = int(time.time())

        structlog.get_logger("structlog").info("[TNC] ARQ | DATA | TX | [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "]", snr=static.SNR)

        # as soon as we set ARQ_STATE to DATA, transmission starts   
        static.ARQ_STATE = True
        self.data_channel_last_received = int(time.time())
    




    # ---------- PING
    def transmit_ping(self, callsign:str):
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
        static.TRANSMITTING = True
        modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])  
        # wait while transmitting
        while static.TRANSMITTING:
            time.sleep(0.01)
    def received_ping(self, data_in:bytes, frequency_offset:str):

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
        static.TRANSMITTING = True
        modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])
        # wait while transmitting
        while static.TRANSMITTING:
            time.sleep(0.01)       
    def received_ping_ack(self, data_in:bytes):

        static.DXCALLSIGN_CRC8 = bytes(data_in[2:3]).rstrip(b'\x00')
        static.DXGRID = bytes(data_in[3:9]).rstrip(b'\x00')
           
        helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'PING-ACK', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
        
        static.INFO.append("PING;RECEIVEDACK")

        structlog.get_logger("structlog").info("[TNC] PING ACK [" + str(static.MYCALLSIGN, 'utf-8') + "] >|< [" + str(static.DXCALLSIGN, 'utf-8') + "]", snr=static.SNR )
        static.TNC_STATE = 'IDLE'
    

    def stop_transmission(self):
        structlog.get_logger("structlog").warning("[TNC] Stopping transmission!")
        stop_frame      = bytearray(14)
        stop_frame[:1]  = bytes([227])
        stop_frame[1:2] = static.DXCALLSIGN_CRC8
        stop_frame[2:3] = static.MYCALLSIGN_CRC8

        txbuffer = [stop_frame]
        static.TRANSMITTING = True
        modem.MODEM_TRANSMIT_QUEUE.put([14,2,250,txbuffer])
        while static.TRANSMITTING:
            time.sleep(0.01)
            
        static.TNC_STATE = 'IDLE'
        static.ARQ_STATE = False
        static.INFO.append("TRANSMISSION;STOPPED")
        self.arq_cleanup()

    def received_stop_transmission(self):
        structlog.get_logger("structlog").warning("[TNC] Stopping transmission!")
        static.TNC_STATE = 'IDLE'
        static.ARQ_STATE = False
        static.INFO.append("TRANSMISSION;STOPPED")
        self.arq_cleanup()
        
    # ----------- BROADCASTS
    
    def run_beacon(self, interval:int):
        try:
            structlog.get_logger("structlog").warning("[TNC] Starting beacon!", interval=interval)

            while static.BEACON_STATE and not static.ARQ_STATE:

                beacon_frame = bytearray(14)
                beacon_frame[:1]   = bytes([230])
                beacon_frame[1:2]  = b'\x01'
                beacon_frame[2:8]  = static.MYCALLSIGN
                beacon_frame[8:14] = static.MYGRID
            
                static.INFO.append("BEACON;SENDING")
                structlog.get_logger("structlog").info("[TNC] Sending beacon!", interval=interval)  
                
                txbuffer = [beacon_frame]
                static.TRANSMITTING = True
                modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])
                # wait while transmitting
                while static.TRANSMITTING:
                    time.sleep(0.01)
                time.sleep(interval)
                #threading.Event().wait(interval)
                                                                
        except Exception as e:
            print(e)

    def received_beacon(self, data_in:bytes):
    # here we add the received station to the heard stations buffer
        dxcallsign = bytes(data_in[2:8]).rstrip(b'\x00')
        dxgrid = bytes(data_in[8:14]).rstrip(b'\x00')
        static.INFO.append("BEACON;RECEIVING")
        structlog.get_logger("structlog").info("[TNC] BEACON RCVD [" + str(dxcallsign, 'utf-8') + "]["+ str(dxgrid, 'utf-8') +"] ", snr=static.SNR)
        helpers.add_to_heard_stations(dxcallsign,dxgrid, 'BEACON', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)



    def transmit_cq(self):
        logging.info("CQ CQ CQ")
        static.INFO.append("CQ;SENDING")
        
        cq_frame       = bytearray(14)
        cq_frame[:1]   = bytes([200])
        cq_frame[1:2]  = b'\x01'
        cq_frame[2:8]  = static.MYCALLSIGN
        cq_frame[8:14] = static.MYGRID
        
        txbuffer = [cq_frame]
        static.TRANSMITTING = True
        modem.MODEM_TRANSMIT_QUEUE.put([14,2,500,txbuffer])
        # wait while transmitting
        while static.TRANSMITTING:
            time.sleep(0.01)
        return


    def received_cq(self, data_in:bytes):
        # here we add the received station to the heard stations buffer
        dxcallsign = bytes(data_in[2:8]).rstrip(b'\x00')
        dxgrid = bytes(data_in[8:14]).rstrip(b'\x00')
        static.INFO.append("CQ;RECEIVING")
        structlog.get_logger("structlog").info("[TNC] CQ RCVD [" + str(dxcallsign, 'utf-8') + "]["+ str(dxgrid, 'utf-8') +"] ", snr=static.SNR)
        helpers.add_to_heard_stations(dxcallsign,dxgrid, 'CQ CQ CQ', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)

    # ------------ CALUCLATE TRANSFER RATES
    def calculate_transfer_rate_rx(self, rx_start_of_transmission:float, receivedbytes:int) -> list:
        
        try: 
            static.ARQ_TRANSMISSION_PERCENT = int((receivedbytes*static.ARQ_COMPRESSION_FACTOR / (static.TOTAL_BYTES * 1024)) * 100)

            transmissiontime = time.time() - self.rx_start_of_transmission
            
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




    def calculate_transfer_rate_tx(self, tx_start_of_transmission:float, sentbytes:int, tx_buffer_length:int) -> list:
        
        try:
            static.ARQ_TRANSMISSION_PERCENT = int((sentbytes / tx_buffer_length) * 100)
            
            transmissiontime = time.time() - tx_start_of_transmission

            if sentbytes > 0:
                
                static.ARQ_BITS_PER_SECOND = int((sentbytes*8) / transmissiontime) # Bits per Second
                static.ARQ_BYTES_PER_MINUTE = int((sentbytes) / (transmissiontime/60)) #Bytes per Minute

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


    # ----------------------CLEANUP AND RESET FUNCTIONS
    def arq_cleanup(self):


        structlog.get_logger("structlog").debug("cleanup")
        
        self.rx_frame_bof_received = False
        self.rx_frame_eof_received = False
        static.TNC_STATE = 'IDLE'
        static.ARQ_STATE = False
        self.burst_ack = False
        self.rpt_request_received = False
        self.data_frame_ack_received = False
        static.RX_BURST_BUFFER = []
        static.RX_FRAME_BUFFER = b'' 
        self.burst_ack_snr= 255

    def arq_reset_ack(self,state:bool):

        self.burst_ack = state
        self.rpt_request_received = state
        self.data_frame_ack_received = state


    # ------------------------- WATCHDOG FUNCTIONS FOR TIMER
    def watchdog(self):
        """
        Author: DJ2LS

        watchdog master function. Frome here we call the watchdogs
        """
        while True:
            time.sleep(0.5)
            self.data_channel_keep_alive_watchdog()


    def data_channel_keep_alive_watchdog(self):
        """
        Author: DJ2LS

        """
                
        # and not static.ARQ_SEND_KEEP_ALIVE:
        if static.ARQ_STATE and static.TNC_STATE == 'BUSY':
            time.sleep(0.01)
            if self.data_channel_last_received + self.transmission_timeout > time.time():
                time.sleep(0.01)
                #pass
            else:
                self.data_channel_last_received = 0
                logging.info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]<<T>>[" + str(static.DXCALLSIGN, 'utf-8') + "]")
                static.INFO.append("ARQ;RECEIVING;FAILED")
                if not TESTMODE:
                    self.arq_cleanup()
