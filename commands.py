#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 23:10:21 2020

@author: DJ2LS
"""

import freedv
import logging
import sound

import pyaudio

class Helpers():
    
    def crc16(data: bytes):
        
        #https://stackoverflow.com/a/60604183
        
        
        xor_in = 0x0000  # initial value
        xor_out = 0x0000  # final XOR value
        poly = 0x8005  # generator polinom (normal form)

        reg = xor_in
        for octet in data:
        # reflect in
            for i in range(8):
                topbit = reg & 0x8000
                if octet & (0x80 >> i):
                    topbit ^= 0x8000
                reg <<= 1
                if topbit:
                    reg ^= poly
            reg &= 0xFFFF
            # reflect out
        return reg ^ xor_out

    def getAudioDevices():
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range(0, numdevices):
            if (p.get_device_info_by_host_api_device_index(0,i).get('maxInputChannels')) > 0:
                print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
            if (p.get_device_info_by_host_api_device_index(0,i).get('maxOutputChannels')) > 0:
                print("Output Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))


class TX():
    
        
    def Broadcast(self, bcdata):
        
        modem = freedv.FreeDV()
        audio = sound.Audio()
        
        
        #preamble = b'\x00' * modem.bytes_per_frame * 2          #SET PREAMPLE
        preamble = b'\x00\x00\x00'
        header = b''                                 # SET HEADER
        #postamble = b'\xFF' * modem.bytes_per_frame# * 2 # SET POSTAMPLE
        frame = preamble + header + bcdata# + postamble # COMBINE PREAMPLE, HEADER, DATA AND POSTAMPLE
        
        logging.info(hex(Helpers.crc16(bcdata)))
        logging.info(len(hex(Helpers.crc16(bcdata))))
        #testcrc = modem.c_lib.freedv_gen_crc16(frame,modem.payload_per_frame)
        
                     
        logging.info("BYTES PER FRAME: " + str(modem.bytes_per_frame))
        logging.info("PAYLOAD PER FRAME: " + str(modem.payload_per_frame))
        logging.info("FRAME LENGTH: " + str(len(frame)))
        #logging.info(str(len(frame)/modem.bytes_per_frame))
        #logging.info(str(len(frame) % modem.bytes_per_frame))
        
        
        # Check if data is divisable by bytes per frame. If yes (0) skip, If no (>0) fill up with frames
        checkframe = len(frame) % modem.bytes_per_frame
        
       # filecrc = binascii.crc16(frame).to_bytes(2, byteorder='big', signed=False)
        
        
        
        
        #if checkframe != 0:
         #   filler = bytes(modem.bytes_per_frame - (len(frame) % modem.bytes_per_frame))
         #   logging.info("FILLER: " + str(len(filler)))
         #   
         #   frame = frame + filler
         #   if len(filler) == 6:
         #       filler * 2
            #frame = frame + filler
        #checkframe = len(frame) % modem.bytes_per_frame * 2
        #logging.info("CHECKFRAME: " + str(checkframe))
        #logging.info("FRAME LENGTH: " + str(len(frame)))
            
        # Pull frame into a datalist to work as a simple buffer   
        data_list = [frame[i:i+modem.bytes_per_frame*2] for i in range(0, len(frame), modem.bytes_per_frame*2)] # PACK DATAFRAME TO A LIST WHICH IS AS BIG AS THE FRAME SIZE OF FREEDV MODE

        #data_list.append(b'0x00')      


        length = len(data_list) # GET LENGTH OF DATA LIST
    
        # Loop through data list for every item and modulate it
        for i in range(length): # LOOP THROUGH DATA LIST
            #crc = Helpers.crc16(data_list[i])
            #logging.info(hex(crc))
            logging.info(data_list[i])
            modulated_data = modem.Modulate(data_list[i])
            #logging.info(bytes(modulated_data))
            audio.Play(modulated_data)    
            
            



class RX():

    def ReceiveAudio():
        
        audio = sound.Audio.Record()
        frame = freedv.FreeDV.Demodulate(audio)            
        logging.info(frame)    
            
            
            
            
            
            
            
        