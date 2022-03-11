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
import sock
import uuid
import base64


TESTMODE = False
 
DATA_QUEUE_TRANSMIT = queue.Queue()
DATA_QUEUE_RECEIVED = queue.Queue()

class DATA():
    """ """

    def __init__(self):

        self.data_queue_transmit = DATA_QUEUE_TRANSMIT
        self.data_queue_received = DATA_QUEUE_RECEIVED

        # ------- ARQ SESSION
        self.arq_file_transfer = False
        self.IS_ARQ_SESSION_MASTER = False
        self.arq_session_last_received = 0
        self.arq_session_timeout = 30
        self.session_connect_max_retries = 3



        self.data_channel_last_received      =   0.0         # time of last "live sign" of a frame      
        self.burst_ack_snr                   =   0           # SNR from received ack frames
        self.burst_ack                       =   False       # if we received an acknowledge frame for a burst
        self.data_frame_ack_received         =   False       # if we received an acknowledge frame for a data frame
        self.rpt_request_received            =   False       # if we received an request for repeater frames
        self.rpt_request_buffer              =   []          # requested frames, saved in a list           
        self.rx_start_of_transmission        =   0           # time of transmission start
        self.data_frame_bof                  =   b'BOF'      # 2 bytes for the BOF End of File indicator in a data frame
        self.data_frame_eof                  =   b'EOF'      # 2 bytes for the EOF End of File indicator in a data frame

        self.rx_n_max_retries_per_burst = 15
        self.n_retries_per_burst = 0
        
        self.received_low_bandwith_mode = False # indicator if we recevied a low bandwith mode channel ope ner

        self.data_channel_max_retries = 5
        
        self.mode_list_low_bw = [14,12]
        self.time_list_low_bw = [3,6]

        self.mode_list_high_bw = [14,12,10] # mode list of available modes, each mode will be used 2times per speed level
        self.time_list_high_bw = [3, 6, 7] # list for time to wait for correspinding mode in seconds

        # mode list for selecting between low bandwith ( 500Hz ) and normal modes with higher bandwith
        if static.LOW_BANDWITH_MODE:
            self.mode_list = self.mode_list_low_bw # mode list of available modes, each mode will be used 2times per speed level
            self.time_list = self.time_list_low_bw # list for time to wait for correspinding mode in seconds

        else:
            self.mode_list = self.mode_list_high_bw # mode list of available modes, each mode will be used 2times per speed level
            self.time_list = self.time_list_high_bw # list for time to wait for correspinding mode in seconds
        
        self.speed_level = len(self.mode_list) - 1    # speed level for selecting mode
        static.ARQ_SPEED_LEVEL = self.speed_level
        
        self.is_IRS = False
        self.burst_nack = False
        self.burst_nack_counter = 0
        self.frame_received_counter = 0
        
        self.rx_frame_bof_received = False
        self.rx_frame_eof_received = False

        self.transmission_timeout = 60 # transmission timeout in seconds

        worker_thread_transmit = threading.Thread(target=self.worker_transmit, name="worker thread transmit",daemon=True)
        worker_thread_transmit.start()
         
        worker_thread_receive = threading.Thread(target=self.worker_receive, name="worker thread receive",daemon=True)
        worker_thread_receive.start()
        
        # START THE THREAD FOR THE TIMEOUT WATCHDOG
        watchdog_thread = threading.Thread(target=self.watchdog, name="watchdog",daemon=True)
        watchdog_thread.start()
        
        arq_session_thread = threading.Thread(target=self.heartbeat, name="watchdog",daemon=True)
        arq_session_thread.start()        
        
        self.beacon_interval = 0
        self.beacon_thread = threading.Thread(target=self.run_beacon, name="watchdog",daemon=True)
        self.beacon_thread.start()
        
                
    def worker_transmit(self):
        """ """
        while True:

            data = self.data_queue_transmit.get()
            # [0] Command

            if data[0] == 'CQ':
                # [0] CQ
                self.transmit_cq()
                
            elif data[0] == 'STOP':
                # [0] STOP
                self.stop_transmission()

            elif data[0] == 'PING':
                # [0] PING
                # [1] dxcallsign
                self.transmit_ping(data[1])
                
            elif data[0] == 'BEACON':
                # [0] BEACON
                # [1] INTERVAL int
                # [2] STATE bool
                #self.run_beacon(data[1])
                if data[2]:
                    self.beacon_interval = data[1]
                    static.BEACON_STATE = True
                else:
                    static.BEACON_STATE = False
                    
            elif data[0] == 'ARQ_FILE':
                # [0] ARQ_FILE
                # [1] DATA_OUT bytes
                # [2] MODE int
                # [3] N_FRAMES_PER_BURST int
                self.open_dc_and_transmit(data[1], data[2], data[3])

            elif data[0] == 'ARQ_RAW':
                # [0] ARQ_RAW
                # [1] DATA_OUT bytes
                # [2] MODE int
                # [3] N_FRAMES_PER_BURST int
                self.open_dc_and_transmit(data[1], data[2], data[3])
                '''
                print(static.ARQ_SESSION)
                if not static.ARQ_SESSION:
                    self.open_dc_and_transmit(data[1], data[2], data[3])
                else:
                    self.arq_transmit(data[1], data[2], data[3])
                '''    
                
            elif data[0] == 'CONNECT':
                # [0] DX CALLSIGN
                self.arq_session_handler(data[1])                

            elif data[0] == 'DISCONNECT':
                # [0] DX CALLSIGN
                self.close_session()

            else:
                # wrong command
                print(f"wrong command {data}")
                pass

            
    def worker_receive(self):
        """ """
        while True:
            data = self.data_queue_received.get()
            # [0] bytes
            # [1] freedv instance
            # [2] bytes_per_frame
            self.process_data(bytes_out=data[0],freedv=data[1],bytes_per_frame=data[2])         


    def process_data(self, bytes_out, freedv, bytes_per_frame):    
        """

        Args:
          bytes_out: 
          freedv: 
          bytes_per_frame: 

        Returns:

        """
        # forward data only if broadcast or we are the receiver
        # bytes_out[1:3] == callsign check for signalling frames, 
        # bytes_out[2:4] == transmission
        # we could also create an own function, which returns True.
        
        frametype = int.from_bytes(bytes(bytes_out[:1]), "big")

        if bytes(bytes_out[1:3]) == static.MYCALLSIGN_CRC or bytes(bytes_out[2:4]) == static.MYCALLSIGN_CRC or frametype == 200 or frametype == 250:

            # CHECK IF FRAMETYPE IS BETWEEN 10 and 50 ------------------------
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
                structlog.get_logger("structlog").debug("FRAME NACK RECEIVED....")
                self.frame_nack_received(bytes_out[:-2])

            # BURST NACK
            elif frametype == 64:
                structlog.get_logger("structlog").debug("BURST NACK RECEIVED....")
                self.burst_nack_received(bytes_out[:-2])
                
                
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



            # SESSION OPENER
            elif frametype == 221:
                structlog.get_logger("structlog").debug("OPEN SESSION RECEIVED....")
                self.received_session_opener(bytes_out[:-2])

            # SESSION HEARTBEAT
            elif frametype == 222:
                structlog.get_logger("structlog").debug("SESSION HEARTBEAT RECEIVED....")
                self.received_session_heartbeat(bytes_out[:-2])

            # SESSION CLOSE
            elif frametype == 223:
                structlog.get_logger("structlog").debug("CLOSE ARQ SESSION RECEIVED....")
                self.received_session_close()

            # ARQ FILE TRANSFER RECEIVED!
            elif frametype == 225 or frametype == 227:
                structlog.get_logger("structlog").debug("ARQ arq_received_data_channel_opener")
                self.arq_received_data_channel_opener(bytes_out[:-2])
    
            # ARQ CHANNEL IS OPENED
            elif frametype == 226 or frametype == 228:
                structlog.get_logger("structlog").debug("ARQ arq_received_channel_is_open")
                self.arq_received_channel_is_open(bytes_out[:-2])



            # ARQ MANUAL MODE TRANSMISSION
            elif 230 <= frametype <= 240 :
                structlog.get_logger("structlog").debug("ARQ manual mode ")
                self.arq_received_data_channel_opener(bytes_out[:-2])

    
            # ARQ STOP TRANSMISSION
            elif frametype == 249:
                structlog.get_logger("structlog").debug("ARQ received stop transmission")
                self.received_stop_transmission()

            # this is outdated and we may remove it
            elif frametype == 250:
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
        """

        Args:
          data_in:bytes: 
          bytes_per_frame:int: 
          snr:int: 
          freedv: 

        Returns:

        """
        data_in = bytes(data_in)    
        
        global TESTMODE
        # only process data if we are in ARQ and BUSY state else return to quit
        if not static.ARQ_STATE and static.TNC_STATE != 'BUSY':
            return

        self.arq_file_transfer = True

        RX_PAYLOAD_PER_MODEM_FRAME = bytes_per_frame - 2    # payload per moden frame

        static.TNC_STATE = 'BUSY'
        static.ARQ_STATE = True
        static.INFO.append("ARQ;RECEIVING")
        self.data_channel_last_received = int(time.time())
            
        # get some important data from the frame
        RX_N_FRAME_OF_BURST         = int.from_bytes(bytes(data_in[:1]), "big") - 10  # get number of burst frame
        RX_N_FRAMES_PER_BURST       = int.from_bytes(bytes(data_in[1:2]), "big")  # get number of bursts from received frame


        '''   
        The RX burst buffer needs to have a fixed length filled with "None". We need this later for counting the "Nones"   
        check if burst buffer has expected length else create it
        '''
        if len(static.RX_BURST_BUFFER) != RX_N_FRAMES_PER_BURST:
            static.RX_BURST_BUFFER = [None] * RX_N_FRAMES_PER_BURST   

        # append data to rx burst buffer
        static.RX_BURST_BUFFER[RX_N_FRAME_OF_BURST] = data_in[6:] # [frame_type][n_frames_per_burst][CRC16][CRC16]
        
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
            if static.RX_FRAME_BUFFER.endswith(temp_burst_buffer):
                structlog.get_logger("structlog").info("[TNC] ARQ | RX | Frame already received - sending ACK again")
                static.RX_BURST_BUFFER = []
            
            # here we are going to search for our data in the last received bytes
            # this increases chance we are not loosing the entire frame in case of signalling frame loss
            else:
                

                # static.RX_FRAME_BUFFER --> exisitng data
                # temp_burst_buffer --> new data
                # search_area --> area where we want to search
                search_area = 510


                search_position = len(static.RX_FRAME_BUFFER)-search_area
                # find position of data. returns -1 if nothing found in area else >= 0
                # we are beginning from the end, so if data exists twice or more, only the last one should be replaced
                get_position = static.RX_FRAME_BUFFER[search_position:].rfind(temp_burst_buffer)
                # if we find data, replace it at this position with the new data and strip it
                if get_position >= 0:
                    static.RX_FRAME_BUFFER = static.RX_FRAME_BUFFER[:search_position + get_position]
                    static.RX_FRAME_BUFFER += temp_burst_buffer
                    structlog.get_logger("structlog").warning("[TNC] ARQ | RX | replacing existing buffer data", area=search_area, pos=get_position)
                # if we dont find data n this range, we really have new data and going to replace it
                else:
                    static.RX_FRAME_BUFFER += temp_burst_buffer
                    structlog.get_logger("structlog").debug("[TNC] ARQ | RX | appending data to buffer")
    



            # lets check if we didnt receive a BOF and EOF yet to avoid sending ack frames if we already received all data
            if not self.rx_frame_bof_received and not self.rx_frame_eof_received and data_in.find(self.data_frame_eof) < 0:  
                
                self.frame_received_counter += 1                
                if self.frame_received_counter >= 2:
                    self.frame_received_counter = 0
                    self.speed_level += 1
                    if self.speed_level >= len(self.mode_list):
                        self.speed_level = len(self.mode_list) - 1
                        static.ARQ_SPEED_LEVEL = self.speed_level 

                # updated modes we are listening to
                self.set_listening_modes(self.mode_list[self.speed_level])

                                
                # create an ack frame
                ack_frame = bytearray(14)
                ack_frame[:1] = bytes([60])
                ack_frame[1:3] = static.DXCALLSIGN_CRC
                ack_frame[3:5] = static.MYCALLSIGN_CRC
                ack_frame[5:6] = bytes([int(static.SNR)])
                ack_frame[6:7] = bytes([int(self.speed_level)])
                # and transmit it
                txbuffer = [ack_frame]
                structlog.get_logger("structlog").info("[TNC] ARQ | RX | SENDING ACK")
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
            rpt_frame[1:3] = static.DXCALLSIGN_CRC
            rpt_frame[3:5] = static.MYCALLSIGN_CRC
            rpt_frame[5:11]  = missing_frames

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

        # get total bytes per transmission information as soon we recevied a frame with a BOF
        if bof_position >=0:
            
            payload = static.RX_FRAME_BUFFER[bof_position+len(self.data_frame_bof):eof_position]
            frame_length = int.from_bytes(payload[4:8], "big") #4:8 4bytes
            static.TOTAL_BYTES = frame_length
            compression_factor = int.from_bytes(payload[8:9], "big") #4:8 4bytes
            compression_factor = np.clip(compression_factor, 0, 255) #limit to max value of 255
            static.ARQ_COMPRESSION_FACTOR = compression_factor / 10
            self.calculate_transfer_rate_rx(self.rx_start_of_transmission, len(static.RX_FRAME_BUFFER))
            

        if bof_position >= 0 and eof_position > 0 and not None in static.RX_BURST_BUFFER:
            print(f"bof_position {bof_position} / eof_position {eof_position}")
            self.rx_frame_bof_received = True
            self.rx_frame_eof_received = True
         
            #now extract raw data from buffer
            payload = static.RX_FRAME_BUFFER[bof_position+len(self.data_frame_bof):eof_position]
            # get the data frame crc
            data_frame_crc = payload[:4] #0:4 4bytes
            frame_length = int.from_bytes(payload[4:8], "big") #4:8 4bytes
            static.TOTAL_BYTES = frame_length
            # 8:9 = compression factor

            data_frame = payload[9:]

            data_frame_crc_received = helpers.get_crc_32(data_frame)
            # check if data_frame_crc is equal with received crc
            if data_frame_crc == data_frame_crc_received:
                structlog.get_logger("structlog").info("[TNC] ARQ | RX | DATA FRAME SUCESSFULLY RECEIVED")
                
                
                # decompression
                data_frame_decompressed = zlib.decompress(data_frame)
                static.ARQ_COMPRESSION_FACTOR = len(data_frame_decompressed) / len(data_frame)
                data_frame = data_frame_decompressed
                
                # decode to utf-8 string
                #data_frame = data_frame.decode("utf-8")

                
                # decode json objects from data frame to inspect if we received a file or message
                #rawdata = json.loads(data_frame)
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
                #if rawdata["dt"] == "f" or rawdata["dt"] == "m":
                #    datatype = rawdata["dt"]
                #else:
                #    datatype = "raw"
                    
                uniqueid = str(uuid.uuid4())
                base64_data = base64.b64encode(data_frame)
                base64_data = base64_data.decode("utf-8")
                static.RX_BUFFER.append([uniqueid, int(time.time()), static.DXCALLSIGN,static.DXGRID, base64_data])
                jsondata = {"arq":"received", "uuid" : static.RX_BUFFER[i][0],  "timestamp": static.RX_BUFFER[i][1], "dxcallsign": str(static.RX_BUFFER[i][2], 'utf-8'), "dxgrid": str(static.RX_BUFFER[i][3], 'utf-8'), "data": base64_data}
                data_out = json.dumps(jsondata)
                sock.SOCKET_QUEUE.put(data_out)
                static.INFO.append("ARQ;RECEIVING;SUCCESS")
               
                # BUILDING ACK FRAME FOR DATA FRAME
                ack_frame       = bytearray(14)
                ack_frame[:1]   = bytes([61])
                ack_frame[1:3] = static.DXCALLSIGN_CRC
                ack_frame[3:5] = static.MYCALLSIGN_CRC
                ack_frame[5:6] = bytes([int(snr)])
                ack_frame[6:7] = bytes([int(self.speed_level)])
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
                structlog.get_logger("structlog").warning("[TNC] ARQ | RX | DATA FRAME NOT SUCESSFULLY RECEIVED!", e="wrong crc", expected=data_frame_crc, received=data_frame_crc_received, overflows=static.BUFFER_OVERFLOW_COUNTER)

                # BUILDING NACK FRAME FOR DATA FRAME
                nack_frame       = bytearray(14)
                nack_frame[:1]   = bytes([63])
                nack_frame[1:3] = static.DXCALLSIGN_CRC
                nack_frame[3:5] = static.MYCALLSIGN_CRC  
                nack_frame[5:6] = bytes([int(snr)])
                nack_frame[6:7] = bytes([int(self.speed_level)])
                                
                # TRANSMIT NACK FRAME FOR BURST
                txbuffer = [nack_frame]
                static.TRANSMITTING = True
                modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])
                # wait while transmitting
                while static.TRANSMITTING:
                    time.sleep(0.01)
                    

            # update session timeout
            self.arq_session_last_received = int(time.time()) # we need to update our timeout timestamp
                                
            # And finally we do a cleanup of our buffers and states
            # do cleanup only when not in testmode
            if not TESTMODE:
                self.arq_cleanup()        
            


    def arq_transmit(self, data_out:bytes, mode:int, n_frames_per_burst:int):
        """

        Args:
          data_out:bytes: 
          mode:int: 
          n_frames_per_burst:int: 

        Returns:

        """

        global TESTMODE
        
        self.arq_file_transfer = True
        
        self.speed_level = len(self.mode_list) - 1    # speed level for selecting mode
        static.ARQ_SPEED_LEVEL = self.speed_level

        TX_N_SENT_BYTES                 = 0                     # already sent bytes per data frame
        self.tx_n_retry_of_burst        = 0                     # retries we already sent data
        TX_N_MAX_RETRIES_PER_BURST      = 50                    # max amount of retries we sent before frame is lost
        TX_N_FRAMES_PER_BURST           = n_frames_per_burst    # amount of n frames per burst    
        TX_BUFFER = []  # our buffer for appending new data
        
        # TIMEOUTS
        BURST_ACK_TIMEOUT_SECONDS       =   3.0        # timeout for burst  acknowledges
        DATA_FRAME_ACK_TIMEOUT_SECONDS  =   3.0        # timeout for data frame acknowledges
        RPT_ACK_TIMEOUT_SECONDS         =   3.0        # timeout for rpt frame acknowledges


        # save len of data_out to TOTAL_BYTES for our statistics --> kBytes
        #static.TOTAL_BYTES = round(len(data_out) / 1024, 2)
        static.TOTAL_BYTES = len(data_out)
        frame_total_size = len(data_out).to_bytes(4, byteorder='big')
        static.INFO.append("ARQ;TRANSMITTING")
        structlog.get_logger("structlog").info("[TNC] | TX | DATACHANNEL", mode=mode, Bytes=static.TOTAL_BYTES)

        
        # compression
        data_frame_compressed = zlib.compress(data_out)
        compression_factor = len(data_out) / len(data_frame_compressed)
        static.ARQ_COMPRESSION_FACTOR = np.clip(compression_factor, 0, 255)
        compression_factor = bytes([int(static.ARQ_COMPRESSION_FACTOR * 10)])
        
        data_out = data_frame_compressed    

        # reset statistics
        tx_start_of_transmission = time.time()
        self.calculate_transfer_rate_tx(tx_start_of_transmission, 0, len(data_out))

        # append a crc and beginn and end of file indicators
        frame_payload_crc = helpers.get_crc_32(data_out)
        # data_out = self.data_frame_bof + frame_payload_crc + data_out + self.data_frame_eof
        data_out = self.data_frame_bof + frame_payload_crc + frame_total_size + compression_factor + data_out + self.data_frame_eof
        
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
                    '''
                    if not self.tx_n_retry_of_burst % 2 and self.tx_n_retry_of_burst > 0:
                        self.speed_level -= 1
                        if self.speed_level < 0:
                            self.speed_level = 0
                    '''
                    
                    #if self.tx_n_retry_of_burst <= 1:
                    #    self.speed_level += 1
                    #    if self.speed_level >= len(self.mode_list)-1:
                    #        self.speed_level = len(self.mode_list)-1
                    
                    # if speed level is greater than our available modes, set speed level to maximum = lenght of mode list -1
                    
                    print(self.mode_list)
                    if self.speed_level >= len(self.mode_list):
                        self.speed_level = len(self.mode_list) - 1
                        static.ARQ_SPEED_LEVEL = self.speed_level
                    data_mode = self.mode_list[self.speed_level]
                    
                    structlog.get_logger("structlog").debug("Speed-level", level=self.speed_level, retry=self.tx_n_retry_of_burst)                    
           
                        

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
                arqheader[2:4] = static.DXCALLSIGN_CRC
                arqheader[4:6] = static.MYCALLSIGN_CRC
                    
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
                '''
                burstacktimeout = time.time() + BURST_ACK_TIMEOUT_SECONDS + 100
                while not self.burst_ack and not self.burst_nack and not self.rpt_request_received and not self.data_frame_ack_received and time.time() < burstacktimeout and static.ARQ_STATE:
                    time.sleep(0.01)
                '''
                #burstacktimeout = time.time() + BURST_ACK_TIMEOUT_SECONDS + 100
                while not self.burst_ack and not self.burst_nack and not self.rpt_request_received and not self.data_frame_ack_received and static.ARQ_STATE:
                    time.sleep(0.01)
                    
                # once we received a burst ack, reset its state and break the RETRIES loop
                if self.burst_ack:
                    self.burst_ack = False # reset ack state
                    self.tx_n_retry_of_burst = 0 # reset retries
                    break #break retry loop

                if self.burst_nack:
                    self.burst_nack = False #reset nack state

                # not yet implemented
                if self.rpt_request_received:
                    pass

                if self.data_frame_ack_received:
                    break #break retry loop
                
                
                # we need this part for leaving the repeat loop
                # static.ARQ_STATE == 'DATA' --> when stopping transmission manually
                if not static.ARQ_STATE:
                    #print("not ready for data...leaving loop....")
                    break
                    
                self.calculate_transfer_rate_tx(tx_start_of_transmission, bufferposition_end, len(data_out))    
                # NEXT ATTEMPT
                structlog.get_logger("structlog").debug("ATTEMPT", retry=self.tx_n_retry_of_burst, maxretries=TX_N_MAX_RETRIES_PER_BURST,overflows=static.BUFFER_OVERFLOW_COUNTER)
            
            # update buffer position
            bufferposition = bufferposition_end

        #     # update stats
            self.calculate_transfer_rate_tx(tx_start_of_transmission, bufferposition_end, len(data_out)) 
            #GOING TO NEXT ITERATION
            

        if self.data_frame_ack_received:
        
            static.INFO.append("ARQ;TRANSMITTING;SUCCESS")

            structlog.get_logger("structlog").info("ARQ | TX | DATA TRANSMITTED!", BytesPerMinute=static.ARQ_BYTES_PER_MINUTE, BitsPerSecond=static.ARQ_BITS_PER_SECOND, overflows=static.BUFFER_OVERFLOW_COUNTER)


                
        else:
            static.INFO.append("ARQ;TRANSMITTING;FAILED")
            structlog.get_logger("structlog").info("ARQ | TX | TRANSMISSION FAILED OR TIME OUT!", overflows=static.BUFFER_OVERFLOW_COUNTER)
            self.stop_transmission()

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
        """

        Args:
          data_in:bytes: 

        Returns:

        """
        
        # increase speed level if we received a burst ack
        #self.speed_level += 1
        #if self.speed_level >= len(self.mode_list)-1:
        #     self.speed_level = len(self.mode_list)-1
        
        # only process data if we are in ARQ and BUSY state
        if static.ARQ_STATE:
            self.burst_ack = True  # Force data loops of TNC to stop and continue with next frame
            self.data_channel_last_received = int(time.time()) # we need to update our timeout timestamp
            self.burst_ack_snr= int.from_bytes(bytes(data_in[5:6]), "big")
            self.speed_level= int.from_bytes(bytes(data_in[6:7]), "big")
            static.ARQ_SPEED_LEVEL = self.speed_level
            print(self.speed_level)
            self.burst_nack_counter = 0
    # signalling frames received
    def burst_nack_received(self, data_in:bytes):
        """

        Args:
          data_in:bytes: 

        Returns:

        """
        
        # increase speed level if we received a burst ack
        #self.speed_level += 1
        #if self.speed_level >= len(self.mode_list)-1:
        #     self.speed_level = len(self.mode_list)-1
        
        # only process data if we are in ARQ and BUSY state
        if static.ARQ_STATE:
            self.burst_nack = True  # Force data loops of TNC to stop and continue with next frame
            self.data_channel_last_received = int(time.time()) # we need to update our timeout timestamp
            self.burst_ack_snr= int.from_bytes(bytes(data_in[5:6]), "big")
            self.speed_level= int.from_bytes(bytes(data_in[6:7]), "big")
            static.ARQ_SPEED_LEVEL = self.speed_level
            self.burst_nack_counter += 1
            print(self.speed_level)


    def frame_ack_received(self):
        """ """
        # only process data if we are in ARQ and BUSY state
        if static.ARQ_STATE:       
            self.data_frame_ack_received = True  # Force data loops of TNC to stop and continue with next frame
            self.data_channel_last_received = int(time.time()) # we need to update our timeout timestamp
            self.arq_session_last_received = int(time.time()) # we need to update our timeout timestamp

    def frame_nack_received(self, data_in:bytes):
        """

        Args:
          data_in:bytes: 

        Returns:

        """
        static.INFO.append("ARQ;TRANSMITTING;FAILED")
        
        self.arq_session_last_received = int(time.time()) # we need to update our timeout timestamp
        
        if not TESTMODE:
            self.arq_cleanup()



    def burst_rpt_received(self, data_in:bytes):
        """

        Args:
          data_in:bytes: 

        Returns:

        """

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
    # ARQ SESSION HANDLER
    # ############################################################################################################

    def arq_session_handler(self, callsign):
        """

        Args:
          callsign: 

        Returns:

        """
        # das hier müssen wir checken. Sollte vielleicht in INIT!!!
        self.datachannel_timeout = False
        structlog.get_logger("structlog").info("SESSION [" + str(static.MYCALLSIGN, 'utf-8') + "]>> <<[" + str(static.DXCALLSIGN, 'utf-8') + "]", state=static.ARQ_SESSION_STATE)
        
        self.open_session(callsign)

        # wait until data channel is open
        while not static.ARQ_SESSION and not self.arq_session_timeout:
            time.sleep(0.01)
            static.ARQ_SESSION_STATE = 'connecting'

        if static.ARQ_SESSION:
            static.ARQ_SESSION_STATE = 'connected'
            return True
        else:
            static.ARQ_SESSION_STATE = 'failed'
            return False


    def open_session(self, callsign):
        """

        Args:
          callsign: 

        Returns:

        """
        self.IS_ARQ_SESSION_MASTER = True
        static.ARQ_SESSION_STATE = 'connecting'

        frametype = bytes([221])
    
        connection_frame        = bytearray(14)
        connection_frame[:1]    = frametype
        connection_frame[1:3] = static.DXCALLSIGN_CRC
        connection_frame[3:5] = static.MYCALLSIGN_CRC
        connection_frame[5:13]   = helpers.callsign_to_bytes(static.MYCALLSIGN)
        
        
        while not static.ARQ_SESSION:
            time.sleep(0.01)
            for attempt in range(1,self.session_connect_max_retries+1):
                txbuffer = [connection_frame]                
                static.TRANSMITTING = True
                
                structlog.get_logger("structlog").info("SESSION [" + str(static.MYCALLSIGN, 'utf-8') + "]>>?<<[" + str(static.DXCALLSIGN, 'utf-8') + "]", a=attempt, state=static.ARQ_SESSION_STATE)
                                
                modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])                
                # wait while transmitting
                while static.TRANSMITTING:
                    time.sleep(0.01)
                    
                timeout = time.time() + 3    
                while time.time() < timeout:    
                    time.sleep(0.01)
                    # break if data channel is openend    
                    if static.ARQ_SESSION:
                        # eventuell einfach nur return true um die nächste break ebene zu vermeiden?
                        break
                if static.ARQ_SESSION:
                    break
        
        
                if not static.ARQ_SESSION and attempt == self.session_connect_max_retries:
                    if not TESTMODE:
                        self.arq_cleanup()
                    return False
                                
                
    def received_session_opener(self, data_in:bytes):
        """

        Args:
          data_in:bytes: 

        Returns:

        """
        self.IS_ARQ_SESSION_MASTER = False
        static.ARQ_SESSION_STATE = 'connecting'

        self.arq_session_last_received = int(time.time())

        static.DXCALLSIGN_CRC = bytes(data_in[3:5])
        static.DXCALLSIGN = helpers.bytes_to_callsign(bytes(data_in[5:13]))
        
        structlog.get_logger("structlog").info("SESSION [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "]", state=static.ARQ_SESSION_STATE)
        static.ARQ_SESSION = True
        static.TNC_STATE = 'BUSY'

        self.transmit_session_heartbeat()


    def close_session(self):
        """ """
        static.ARQ_SESSION_STATE = 'disconnecting'
        structlog.get_logger("structlog").info("SESSION [" + str(static.MYCALLSIGN, 'utf-8') + "]<<X>>[" + str(static.DXCALLSIGN, 'utf-8') + "]", state=static.ARQ_SESSION_STATE)
        static.INFO.append("ARQ;SESSION;CLOSE")
        self.IS_ARQ_SESSION_MASTER = False
        static.ARQ_SESSION = False
        self.arq_cleanup()

        frametype = bytes([223])
    
        disconnection_frame        = bytearray(14)
        disconnection_frame[:1]    = frametype
        disconnection_frame[1:3] = static.DXCALLSIGN_CRC
        disconnection_frame[3:5] = static.MYCALLSIGN_CRC
        disconnection_frame[5:13]   = helpers.callsign_to_bytes(static.MYCALLSIGN)
        
        txbuffer = [disconnection_frame]                
        static.TRANSMITTING = True
                        
        modem.MODEM_TRANSMIT_QUEUE.put([14,2,250,txbuffer])                
        # wait while transmitting
        while static.TRANSMITTING:
            time.sleep(0.01)          
        
        

        
    def received_session_close(self):
        """ """
        static.ARQ_SESSION_STATE = 'disconnected'
        structlog.get_logger("structlog").info("SESSION [" + str(static.MYCALLSIGN, 'utf-8') + "]<<X>>[" + str(static.DXCALLSIGN, 'utf-8') + "]", state=static.ARQ_SESSION_STATE)
        static.INFO.append("ARQ;SESSION;CLOSE")

        self.IS_ARQ_SESSION_MASTER = False
        static.ARQ_SESSION = False
        self.arq_cleanup()


    def transmit_session_heartbeat(self):
        """ """

        static.ARQ_SESSION = True
        static.TNC_STATE = 'BUSY'
        static.ARQ_SESSION_STATE = 'connected'

        frametype = bytes([222])
    
        connection_frame        = bytearray(14)
        connection_frame[:1]    = frametype
        connection_frame[1:3] = static.DXCALLSIGN_CRC
        connection_frame[3:5] = static.MYCALLSIGN_CRC
        connection_frame[5:13]   = helpers.callsign_to_bytes(static.MYCALLSIGN)
        
        txbuffer = [connection_frame]                
        static.TRANSMITTING = True
                        
        modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])                
        # wait while transmitting
        while static.TRANSMITTING:
            time.sleep(0.01)  




    def received_session_heartbeat(self, data_in:bytes):
        """

        Args:
          data_in:bytes: 

        Returns:

        """
        structlog.get_logger("structlog").debug("received session heartbeat")
        helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, 'SESSION-HB', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)

        self.arq_session_last_received = int(time.time()) # we need to update our timeout timestamp
        
        static.ARQ_SESSION = True
        static.ARQ_SESSION_STATE = 'connected'
        static.TNC_STATE = 'BUSY'
        self.data_channel_last_received = int(time.time())
        if static.ARQ_SESSION and not self.IS_ARQ_SESSION_MASTER and not self.arq_file_transfer:
            self.transmit_session_heartbeat()

    # ############################################################################################################
    # ARQ DATA CHANNEL HANDLER
    # ############################################################################################################

    def open_dc_and_transmit(self, data_out:bytes, mode:int, n_frames_per_burst:int):
        """

        Args:
          data_out:bytes: 
          mode:int: 
          n_frames_per_burst:int: 

        Returns:

        """
        static.TNC_STATE = 'BUSY'
        self.arq_file_transfer = True
        
        # wait a moment for the case, an heartbeat is already on the way back to us
        if static.ARQ_SESSION:
            time.sleep(0.5)
        
        
        self.datachannel_timeout = False
        
        # we need to compress data for gettin a compression factor.
        # so we are compressing twice. This is not that nice and maybe theres another way
        # for calculating transmission statistics
        static.ARQ_COMPRESSION_FACTOR = len(data_out) / len(zlib.compress(data_out))
        
        self.arq_open_data_channel(mode, n_frames_per_burst)
        
        # wait until data channel is open
        while not static.ARQ_STATE and not self.datachannel_timeout:
            time.sleep(0.01)
        
        if static.ARQ_STATE:
            self.arq_transmit(data_out, mode, n_frames_per_burst)
        else:
             return False
            
    def arq_open_data_channel(self, mode:int, n_frames_per_burst:int):      
        """

        Args:
          mode:int: 
          n_frames_per_burst:int: 

        Returns:

        """
        self.is_IRS = False      
        self.data_channel_last_received = int(time.time())

        if static.LOW_BANDWITH_MODE and mode == 255:
            frametype = bytes([227])
            structlog.get_logger("structlog").debug("requesting low bandwith mode")

        else:
            frametype = bytes([225])
            structlog.get_logger("structlog").debug("requesting high bandwith mode")

        
        if 230 <= mode <= 240:
            structlog.get_logger("structlog").debug("requesting manual mode --> not yet implemented ")
            frametype = bytes([mode])
            
        connection_frame        = bytearray(14)
        connection_frame[:1]    = frametype
        connection_frame[1:3] = static.DXCALLSIGN_CRC
        connection_frame[3:5] = static.MYCALLSIGN_CRC
        connection_frame[5:13]   = helpers.callsign_to_bytes(static.MYCALLSIGN)
        connection_frame[13:14] = bytes([n_frames_per_burst])                    
        
        while not static.ARQ_STATE:
            time.sleep(0.01)
            for attempt in range(1,self.data_channel_max_retries+1):
                static.INFO.append("DATACHANNEL;OPENING")
                structlog.get_logger("structlog").info("[TNC] ARQ | DATA | TX | [" + str(static.MYCALLSIGN, 'utf-8') + "]>> <<[" + str(static.DXCALLSIGN, 'utf-8') + "]", attempt=str(attempt) + "/" + str(self.data_channel_max_retries))                
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

                if not static.ARQ_STATE and attempt == self.data_channel_max_retries:
                    static.INFO.append("DATACHANNEL;FAILED")
                    
                    structlog.get_logger("structlog").warning("[TNC] ARQ | TX | DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]>>X<<[" + str(static.DXCALLSIGN, 'utf-8') + "]")
                    self.datachannel_timeout = True
                    if not TESTMODE:
                        self.arq_cleanup()
                    
                    return False
                    #sys.exit() # close thread and so connection attempts


 


    def arq_received_data_channel_opener(self, data_in:bytes):
        """

        Args:
          data_in:bytes: 

        Returns:

        """
        self.arq_file_transfer = True
        self.is_IRS = True        
        static.INFO.append("DATACHANNEL;RECEIVEDOPENER")
        static.DXCALLSIGN_CRC = bytes(data_in[3:5])
        static.DXCALLSIGN = helpers.bytes_to_callsign(bytes(data_in[5:13]))
        n_frames_per_burst = int.from_bytes(bytes(data_in[13:14]), "big")    
        frametype = int.from_bytes(bytes(data_in[:1]), "big")
        #check if we received low bandwith mode
        if frametype == 225:
            self.received_low_bandwith_mode = False
            self.mode_list = self.mode_list_high_bw 
            self.time_list = self.time_list_high_bw
            self.speed_level = len(self.mode_list) - 1 
        else:
            self.received_low_bandwith_mode = True
            self.mode_list = self.mode_list_low_bw 
            self.time_list = self.time_list_low_bw
            self.speed_level = len(self.mode_list) - 1 
   
        
        if 230 <= frametype <= 240:
            print("manual mode request")
        
        # updated modes we are listening to
        self.set_listening_modes(self.mode_list[self.speed_level])

        helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'DATA-CHANNEL', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
            
        structlog.get_logger("structlog").info("[TNC] ARQ | DATA | RX | [" + str(static.MYCALLSIGN, 'utf-8') + "]>> <<[" + str(static.DXCALLSIGN, 'utf-8') + "]", bandwith="wide")
           
        static.ARQ_STATE = True
        static.TNC_STATE = 'BUSY'


        self.reset_statistics()

        self.data_channel_last_received = int(time.time())
        # check if we are in low bandwith mode
        if static.LOW_BANDWITH_MODE or self.received_low_bandwith_mode:
            frametype = bytes([228])
            structlog.get_logger("structlog").debug("responding with low bandwith mode")
        else:
            frametype = bytes([226])
            structlog.get_logger("structlog").debug("responding with high bandwith mode")
        
        connection_frame = bytearray(14)
        connection_frame[:1] = frametype
        connection_frame[1:3] = static.DXCALLSIGN_CRC
        connection_frame[3:5] = static.MYCALLSIGN_CRC
        connection_frame[13:14] = bytes([static.ARQ_PROTOCOL_VERSION]) #crc8 of version for checking protocol version    

        txbuffer = [connection_frame]
        
        static.TRANSMITTING = True
        modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])
        # wait while transmitting
        while static.TRANSMITTING:
            time.sleep(0.01)
        structlog.get_logger("structlog").info("[TNC] ARQ | DATA | RX | [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "]", bandwith="wide", snr=static.SNR)
        
        # set start of transmission for our statistics
        self.rx_start_of_transmission = time.time()



    def arq_received_channel_is_open(self, data_in:bytes):
        """
        Called if we received a data channel opener
        Args:
          data_in:bytes: 

        Returns:

        """
        protocol_version = int.from_bytes(bytes(data_in[13:14]), "big")
        if protocol_version == static.ARQ_PROTOCOL_VERSION:
            static.INFO.append("DATACHANNEL;OPEN")
            static.DXCALLSIGN_CRC = bytes(data_in[3:5])
            frametype = int.from_bytes(bytes(data_in[:1]), "big")  
                
            if frametype == 228:
                self.received_low_bandwith_mode = True
                self.mode_list = self.mode_list_low_bw 
                self.time_list = self.time_list_low_bw
                self.speed_level = len(self.mode_list) - 1 
                structlog.get_logger("structlog").debug("low bandwith mode", modes=self.mode_list)
            else:
                self.received_low_bandwith_mode = False
                self.mode_list = self.mode_list_high_bw 
                self.time_list = self.time_list_high_bw
                self.speed_level = len(self.mode_list) - 1 
                structlog.get_logger("structlog").debug("high bandwith mode", modes=self.mode_list)
                
            helpers.add_to_heard_stations(static.DXCALLSIGN,static.DXGRID, 'DATA-CHANNEL', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
            
            structlog.get_logger("structlog").info("[TNC] ARQ | DATA | TX | [" + str(static.MYCALLSIGN, 'utf-8') + "]>>|<<[" + str(static.DXCALLSIGN, 'utf-8') + "]", snr=static.SNR)

            # as soon as we set ARQ_STATE to DATA, transmission starts   
            static.ARQ_STATE = True
            self.data_channel_last_received = int(time.time())
        else:
            static.TNC_STATE = 'IDLE'
            static.ARQ_STATE = False
            static.INFO.append("PROTOCOL;VERSION_MISSMATCH")
            structlog.get_logger("structlog").warning("protocol version missmatch", received=protocol_version, own=static.ARQ_PROTOCOL_VERSION)
            self.arq_cleanup()


    # ---------- PING
    def transmit_ping(self, dxcallsign:bytes):
        """
        Funktion for controlling pings
        Args:
          dxcallsign:bytes: 

        Returns:

        """
        static.DXCALLSIGN = dxcallsign
        static.DXCALLSIGN_CRC = helpers.get_crc_16(static.DXCALLSIGN)
                
        static.INFO.append("PING;SENDING")
        structlog.get_logger("structlog").info("[TNC] PING REQ [" + str(static.MYCALLSIGN, 'utf-8') + "] >>> [" + str(static.DXCALLSIGN, 'utf-8') + "]" )

        ping_frame      = bytearray(14)
        ping_frame[:1]  = bytes([210])
        ping_frame[1:3] = static.DXCALLSIGN_CRC
        ping_frame[3:5] = static.MYCALLSIGN_CRC
        ping_frame[5:13] = helpers.callsign_to_bytes(static.MYCALLSIGN)

        txbuffer = [ping_frame]
        print(helpers.callsign_to_bytes(static.MYCALLSIGN))
        print(txbuffer)
        static.TRANSMITTING = True
        modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])  
        # wait while transmitting
        while static.TRANSMITTING:
            time.sleep(0.01)
            
    def received_ping(self, data_in:bytes, frequency_offset:str):
        """
        Called if we received a ping

        Args:
          data_in:bytes: 
          frequency_offset:str: 

        Returns:

        """

        static.DXCALLSIGN_CRC = bytes(data_in[3:5])
        static.DXCALLSIGN = helpers.bytes_to_callsign(bytes(data_in[5:13]))
        helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, 'PING', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
        
        static.INFO.append("PING;RECEIVING")

        structlog.get_logger("structlog").info("[TNC] PING REQ [" + str(static.MYCALLSIGN, 'utf-8') + "] <<< [" + str(static.DXCALLSIGN, 'utf-8') + "]", snr=static.SNR )

        ping_frame      = bytearray(14)
        ping_frame[:1]  = bytes([211])
        ping_frame[1:3] = static.DXCALLSIGN_CRC
        ping_frame[3:5] = static.MYCALLSIGN_CRC
        ping_frame[5:11] = static.MYGRID
        ping_frame[11:13] = frequency_offset.to_bytes(2, byteorder='big', signed=True)

        txbuffer = [ping_frame]
        static.TRANSMITTING = True
        modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])
        # wait while transmitting
        while static.TRANSMITTING:
            time.sleep(0.01)
            
    def received_ping_ack(self, data_in:bytes):
        """
        Called if a PING ack has been received
        Args:
          data_in:bytes: 

        Returns:

        """

        static.DXCALLSIGN_CRC = bytes(data_in[3:5])
        static.DXGRID = bytes(data_in[5:11]).rstrip(b'\x00')
           
        helpers.add_to_heard_stations(static.DXCALLSIGN, static.DXGRID, 'PING-ACK', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)
        
        static.INFO.append("PING;RECEIVEDACK")

        structlog.get_logger("structlog").info("[TNC] PING ACK [" + str(static.MYCALLSIGN, 'utf-8') + "] >|< [" + str(static.DXCALLSIGN, 'utf-8') + "]", snr=static.SNR )
        static.TNC_STATE = 'IDLE'
    

    def stop_transmission(self):
        """
        Force a stop of the running transmission
        """
        structlog.get_logger("structlog").warning("[TNC] Stopping transmission!")
        stop_frame      = bytearray(14)
        stop_frame[:1]  = bytes([249])
        stop_frame[1:3] = static.DXCALLSIGN_CRC
        stop_frame[3:5] = static.MYCALLSIGN_CRC

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
        """
        Received a transmission stop
        """
        structlog.get_logger("structlog").warning("[TNC] Stopping transmission!")
        static.TNC_STATE = 'IDLE'
        static.ARQ_STATE = False
        static.INFO.append("TRANSMISSION;STOPPED")
        self.arq_cleanup()
        
    # ----------- BROADCASTS
    
    def run_beacon(self):
        """
        Controlling funktion for running a beacon
        Args:
          interval:int: 

        Returns:

        """
        try:
            
            while 1:
                time.sleep(0.5)
                while static.BEACON_STATE:

                    if static.BEACON_STATE and not static.ARQ_SESSION and not self.arq_file_transfer and not static.BEACON_PAUSE:
                        static.INFO.append("BEACON;SENDING")
                        structlog.get_logger("structlog").info("[TNC] Sending beacon!", interval=self.beacon_interval)  
                        
                        beacon_frame = bytearray(14)
                        beacon_frame[:1]   = bytes([250])
                        beacon_frame[1:9]  = helpers.callsign_to_bytes(static.MYCALLSIGN)
                        beacon_frame[9:13] = static.MYGRID[:4]
                        txbuffer = [beacon_frame]

                        static.TRANSMITTING = True
                        modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])
                        # wait while transmitting
                        while static.TRANSMITTING:
                            time.sleep(0.01)
                            
                    interval_timer = time.time() + self.beacon_interval
                    while time.time() < interval_timer and static.BEACON_STATE and not static.BEACON_PAUSE:
                        time.sleep(0.01)

        except Exception as e:
            print(e)

    def received_beacon(self, data_in:bytes):
        """
        Called if we received a beacon
        Args:
          data_in:bytes: 

        Returns:

        """
    # here we add the received station to the heard stations buffer
        dxcallsign = helpers.bytes_to_callsign(bytes(data_in[1:9]))
        dxgrid = bytes(data_in[9:13]).rstrip(b'\x00')
        static.INFO.append("BEACON;RECEIVING")
        structlog.get_logger("structlog").info("[TNC] BEACON RCVD [" + str(dxcallsign, 'utf-8') + "]["+ str(dxgrid, 'utf-8') +"] ", snr=static.SNR)
        helpers.add_to_heard_stations(dxcallsign,dxgrid, 'BEACON', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)



    def transmit_cq(self):
        """
        Transmit a CQ
        """
        structlog.get_logger("structlog").info("CQ CQ CQ")
        static.INFO.append("CQ;SENDING")
        
        cq_frame       = bytearray(14)
        cq_frame[:1]   = bytes([200])
        cq_frame[1:9]  = helpers.callsign_to_bytes(static.MYCALLSIGN)
        cq_frame[9:13] = static.MYGRID[:4]
        
        txbuffer = [cq_frame]
        print(txbuffer)
        static.TRANSMITTING = True
        modem.MODEM_TRANSMIT_QUEUE.put([14,2,500,txbuffer])
        # wait while transmitting
        while static.TRANSMITTING:
            time.sleep(0.01)
        return


    def received_cq(self, data_in:bytes):
        """
        Called if we received a CQ
        Args:
          data_in:bytes: 

        Returns:

        """
        # here we add the received station to the heard stations buffer
        dxcallsign = helpers.bytes_to_callsign(bytes(data_in[1:9]))
        dxgrid = bytes(data_in[9:13]).rstrip(b'\x00')
        static.INFO.append("CQ;RECEIVING")
        structlog.get_logger("structlog").info("[TNC] CQ RCVD [" + str(dxcallsign, 'utf-8') + "]["+ str(dxgrid, 'utf-8') +"] ", snr=static.SNR)
        helpers.add_to_heard_stations(dxcallsign, dxgrid, 'CQ CQ CQ', static.SNR, static.FREQ_OFFSET, static.HAMLIB_FREQUENCY)

    # ------------ CALUCLATE TRANSFER RATES
    def calculate_transfer_rate_rx(self, rx_start_of_transmission:float, receivedbytes:int) -> list:
        """
        Calculate Transferrate for receiving data
        Args:
          rx_start_of_transmission:float: 
          receivedbytes:int: 

        Returns:

        """
        
        try: 
            static.ARQ_TRANSMISSION_PERCENT = int((receivedbytes*static.ARQ_COMPRESSION_FACTOR / (static.TOTAL_BYTES)) * 100)

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



    def reset_statistics(self):
        """
        Reset statistics
        """
        # reset ARQ statistics
        static.ARQ_BYTES_PER_MINUTE_BURST = 0
        static.ARQ_BYTES_PER_MINUTE = 0
        static.ARQ_BITS_PER_SECOND_BURST = 0
        static.ARQ_BITS_PER_SECOND = 0
        static.ARQ_TRANSMISSION_PERCENT = 0
        static.TOTAL_BYTES = 0
        
    def calculate_transfer_rate_tx(self, tx_start_of_transmission:float, sentbytes:int, tx_buffer_length:int) -> list:
        """
        Calcualte Transferrate for transmission
        Args:
          tx_start_of_transmission:float: 
          sentbytes:int: 
          tx_buffer_length:int: 

        Returns:

        """
        
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
        """
        Cleanup funktion which clears all ARQ states
        """


        structlog.get_logger("structlog").debug("cleanup")
        
        self.rx_frame_bof_received = False
        self.rx_frame_eof_received = False
        self.burst_ack = False
        self.rpt_request_received = False
        self.data_frame_ack_received = False
        static.RX_BURST_BUFFER = []
        static.RX_FRAME_BUFFER = b'' 
        self.burst_ack_snr= 255

        # reset modem receiving state to reduce cpu load
        modem.RECEIVE_DATAC1 = False
        modem.RECEIVE_DATAC3 = False

        # reset buffer overflow counter
        static.BUFFER_OVERFLOW_COUNTER = [0,0,0]

        self.is_IRS = False
        self.burst_nack = False
        self.burst_nack_counter = 0
        self.frame_received_counter = 0
        self.speed_level = len(self.mode_list) - 1
        static.ARQ_SPEED_LEVEL = self.speed_level
        
        # low bandwith mode indicator
        self.received_low_bandwith_mode = False
        
        # reset retry counter for rx channel / burst
        self.n_retries_per_burst = 0
        
        if not static.ARQ_SESSION:
            static.TNC_STATE = 'IDLE'
            
        static.ARQ_STATE = False
        self.arq_file_transfer = False
        
        static.BEACON_PAUSE = False
        
        
        
        
        
    def arq_reset_ack(self,state:bool):
        """
        Funktion for resetting acknowledge states
        Args:
          state:bool: 

        Returns:

        """

        self.burst_ack = state
        self.rpt_request_received = state
        self.data_frame_ack_received = state


    def set_listening_modes(self, mode):
        """
        Function for setting the data modes we are listening to for saving cpu power

        Args:
          mode: 

        Returns:

        """
        # set modes we want listening to
        
        mode_name = codec2.freedv_get_mode_name_by_value(mode)
        if mode_name == 'datac1':
            modem.RECEIVE_DATAC1 = True
            structlog.get_logger("structlog").debug("changing listening data mode", mode="datac1")

        elif mode_name == 'datac3':
            modem.RECEIVE_DATAC3 = True
            structlog.get_logger("structlog").debug("changing listening data mode", mode="datac3")
        elif mode_name == 'allmodes':
            modem.RECEIVE_DATAC1 = True
            modem.RECEIVE_DATAC3 = True
            structlog.get_logger("structlog").debug("changing listening data mode", mode="datac1/datac3")
                    

    # ------------------------- WATCHDOG FUNCTIONS FOR TIMER
    def watchdog(self):
        """Author: DJ2LS
        
        watchdog master function. Frome here we call the watchdogs

        Args:

        Returns:

        """
        while True:
            time.sleep(0.1)
            self.data_channel_keep_alive_watchdog()
            self.burst_watchdog()
            self.arq_session_keep_alive_watchdog()


    def burst_watchdog(self):
        """
        watchdog which checks if we are running into a connection timeout
        DATA BURST
        """
      
        # IRS SIDE        
        if static.ARQ_STATE and static.TNC_STATE == 'BUSY' and self.is_IRS:
            if self.data_channel_last_received + self.time_list[self.speed_level] > time.time():
                #print((self.data_channel_last_received + self.time_list[self.speed_level])-time.time())
                pass
            else:
                structlog.get_logger("structlog").warning("packet timeout", attempt=self.n_retries_per_burst,  max_attempts=self.rx_n_max_retries_per_burst, speed_level=self.speed_level)
                self.frame_received_counter = 0
                self.burst_nack_counter += 1
                if self.burst_nack_counter >= 2:
                    self.speed_level -= 1
                    #print(self.burst_nack_counter)
                    #print(self.speed_level)
                    static.ARQ_SPEED_LEVEL = self.speed_level
                    self.burst_nack_counter = 0
                if self.speed_level <= 0:
                    self.speed_level = 0
                    static.ARQ_SPEED_LEVEL = self.speed_level
                
                # updated modes we are listening to
                self.set_listening_modes(self.mode_list[self.speed_level])
                
                # BUILDING NACK FRAME FOR DATA FRAME
                burst_nack_frame       = bytearray(14)
                burst_nack_frame[:1]   = bytes([64])
                burst_nack_frame[1:3] = static.DXCALLSIGN_CRC
                burst_nack_frame[3:5] = static.MYCALLSIGN_CRC  
                burst_nack_frame[5:6] = bytes([0])
                burst_nack_frame[6:7] = bytes([int(self.speed_level)])
                                
                # TRANSMIT NACK FRAME FOR BURST
                txbuffer = [burst_nack_frame]
                static.TRANSMITTING = True
                modem.MODEM_TRANSMIT_QUEUE.put([14,1,0,txbuffer])
                # wait while transmitting
                #while static.TRANSMITTING:
                #    #time.sleep(0.01)
                #    self.data_channel_last_received = time.time()
                self.data_channel_last_received = time.time()
                self.n_retries_per_burst += 1
                
            if self.n_retries_per_burst >= self.rx_n_max_retries_per_burst:
                self.stop_transmission()
                self.arq_cleanup()

                
    def data_channel_keep_alive_watchdog(self):
        """
        watchdog which checks if we are running into a connection timeout
        DATA CHANNEL        
        """
                
        # and not static.ARQ_SEND_KEEP_ALIVE:
        if static.ARQ_STATE and static.TNC_STATE == 'BUSY':
            time.sleep(0.01)
            if self.data_channel_last_received + self.transmission_timeout > time.time():
                time.sleep(0.01)
                #print(self.data_channel_last_received + self.transmission_timeout - time.time())
                #pass
            else:
                self.data_channel_last_received = 0
                structlog.get_logger("structlog").info("DATA [" + str(static.MYCALLSIGN, 'utf-8') + "]<<T>>[" + str(static.DXCALLSIGN, 'utf-8') + "]")
                static.INFO.append("ARQ;RECEIVING;FAILED")
                if not TESTMODE:
                    self.arq_cleanup()
                    
    def arq_session_keep_alive_watchdog(self):
        """
        watchdog which checks if we are running into a connection timeout
        ARQ SESSION
        """
        if static.ARQ_SESSION and static.TNC_STATE == 'BUSY' and not self.arq_file_transfer:
            if self.arq_session_last_received + self.arq_session_timeout > time.time():
                time.sleep(0.01)
            else:
                structlog.get_logger("structlog").info("SESSION [" + str(static.MYCALLSIGN, 'utf-8') + "]<<T>>[" + str(static.DXCALLSIGN, 'utf-8') + "]")
                static.INFO.append("ARQ;SESSION;TIMEOUT")
                self.close_session()
                
                 
                    
    def heartbeat(self):
        """
        heartbeat thread which auto resumes the heartbeat signal within a arq session
        """
        while 1:
            time.sleep(0.01)
            if static.ARQ_SESSION and self.IS_ARQ_SESSION_MASTER and not self.arq_file_transfer:
                time.sleep(1)
                self.transmit_session_heartbeat()
                time.sleep(2)
