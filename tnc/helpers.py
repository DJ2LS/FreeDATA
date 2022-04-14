#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 21:25:14 2020

@author: DJ2LS
"""

import time
import crcengine
import static



def wait(seconds):
    """

    Args:
      seconds: 

    Returns:

    """
    timeout = time.time() + seconds

    while time.time() < timeout:
        time.sleep(0.01)
    return True
    
    

def get_crc_8(data):
    """Author: DJ2LS
    
    Get the CRC8 of a byte string
    
    param: data = bytes()

    Args:
      data: 

    Returns:

    """
    crc_algorithm = crcengine.new('crc8-ccitt')  # load crc8 library
    crc_data = crc_algorithm(data)
    crc_data = crc_data.to_bytes(1, byteorder='big')
    return crc_data


def get_crc_16(data):
    """Author: DJ2LS
    
    Get the CRC16 of a byte string
    
    param: data = bytes()

    Args:
      data: 

    Returns:

    """
    crc_algorithm = crcengine.new('crc16-ccitt-false')  # load crc16 library
    crc_data = crc_algorithm(data)
    crc_data = crc_data.to_bytes(2, byteorder='big')
    return crc_data

def get_crc_32(data):
    """Author: DJ2LS
    
    Get the CRC32 of a byte string
    
    param: data = bytes()

    Args:
      data: 

    Returns:

    """
    crc_algorithm = crcengine.new('crc32')  # load crc16 library
    crc_data = crc_algorithm(data)
    crc_data = crc_data.to_bytes(4, byteorder='big')
    return crc_data


def add_to_heard_stations(dxcallsign, dxgrid, datatype, snr, offset, frequency):
    """

    Args:
      dxcallsign: 
      dxgrid: 
      datatype: 
      snr: 
      offset: 
      frequency: 

    Returns:

    """

    # check if buffer empty
    if len(static.HEARD_STATIONS) == 0:
        static.HEARD_STATIONS.append([dxcallsign, dxgrid, int(time.time()), datatype, snr, offset, frequency])
    # if not, we search and update
    else:
        for i in range(0, len(static.HEARD_STATIONS)):
            # update callsign with new timestamp
            if static.HEARD_STATIONS[i].count(dxcallsign) > 0:
                static.HEARD_STATIONS[i] = [dxcallsign, dxgrid, int(time.time()), datatype, snr, offset, frequency]
                break
            # insert if nothing found
            if i == len(static.HEARD_STATIONS) - 1:
                static.HEARD_STATIONS.append([dxcallsign, dxgrid, int(time.time()), datatype, snr, offset, frequency])
                break


#    for idx, item in enumerate(static.HEARD_STATIONS):
#        if dxcallsign in item:
#            item = [dxcallsign, int(time.time())]
#            static.HEARD_STATIONS[idx] = item



def callsign_to_bytes(callsign):
    """

    Args:
      callsign: 

    Returns:

    """
    # http://www.aprs.org/aprs11/SSIDs.txt
    #-0 Your primary station usually fixed and message capable
    #-1 generic additional station, digi, mobile, wx, etc
    #-2 generic additional station, digi, mobile, wx, etc
    #-3 generic additional station, digi, mobile, wx, etc
    #-4 generic additional station, digi, mobile, wx, etc
    #-5 Other networks (Dstar, Iphones, Androids, Blackberry's etc)
    #-6 Special activity, Satellite ops, camping or 6 meters, etc
    #-7 walkie talkies, HT's or other human portable
    #-8 boats, sailboats, RV's or second main mobile
    #-9 Primary Mobile (usually message capable)
    #-10 internet, Igates, echolink, winlink, AVRS, APRN, etc
    #-11 balloons, aircraft, spacecraft, etc
    #-12 APRStt, DTMF, RFID, devices, one-way trackers*, etc
    #-13 Weather stations
    #-14 Truckers or generally full time drivers
    #-15 generic additional station, digi, mobile, wx, etc
    
    # try converting to bytestring if possible type string
    try:    
        callsign = bytes(callsign, 'utf-8')       
    except:
        pass

    # we need to do this step to reduce the needed paypload by the callsign ( stripping "-" out of the callsign ) 
    callsign = callsign.split(b'-')
    try:
        ssid = int(callsign[1])
    except:
        ssid = 0
        
    callsign = callsign[0]
    
    bytestring = bytearray(8)
    bytestring[:len(callsign)] = callsign
    bytestring[7:8] = bytes([ssid])

    return bytes(bytestring) 
    
def bytes_to_callsign(bytestring):
    """

    Args:
      bytestring: 

    Returns:

    """

    # http://www.aprs.org/aprs11/SSIDs.txt
    #-0 Your primary station usually fixed and message capable
    #-1 generic additional station, digi, mobile, wx, etc
    #-2 generic additional station, digi, mobile, wx, etc
    #-3 generic additional station, digi, mobile, wx, etc
    #-4 generic additional station, digi, mobile, wx, etc
    #-5 Other networks (Dstar, Iphones, Androids, Blackberry's etc)
    #-6 Special activity, Satellite ops, camping or 6 meters, etc
    #-7 walkie talkies, HT's or other human portable
    #-8 boats, sailboats, RV's or second main mobile
    #-9 Primary Mobile (usually message capable)
    #-10 internet, Igates, echolink, winlink, AVRS, APRN, etc
    #-11 balloons, aircraft, spacecraft, etc
    #-12 APRStt, DTMF, RFID, devices, one-way trackers*, etc
    #-13 Weather stations
    #-14 Truckers or generally full time drivers
    #-15 generic additional station, digi, mobile, wx, etc
        
    # we need to do this step to reduce the needed paypload by the callsign ( stripping "-" out of the callsign )    

    callsign = bytes(bytestring[:7])
    callsign = callsign.rstrip(b'\x00')
    ssid = int.from_bytes(bytes(bytestring[7:8]), "big")

    callsign = callsign + b'-'
    callsign = callsign.decode('utf-8')
    callsign = callsign + str(ssid)
    callsign = callsign.encode('utf-8')
    
    return bytes(callsign) 




def check_callsign(callsign:bytes, crc_to_check:bytes):
    """
    Funktion to check a crc against a callsign to calculate the ssid by generating crc until we got it

    Args:
      callsign: Callsign which we want to check
      crc_to_check: The CRC which we want the callsign to check against 

    Returns:
        [True, Callsign + SSID]
        False
    """

    crc_algorithm = crcengine.new('crc16-ccitt-false')  # load crc16 library
    
    try:
        callsign = callsign.split(b'-')
        callsign = callsign[0] # we want the callsign without SSID
        
    except:
        callsign = callsign
    
    print(static.SSID_LIST)
    for ssid in static.SSID_LIST:
        print(ssid)    
    for ssid in static.SSID_LIST:
    #for ssid in range(0,254):
        call_with_ssid = bytearray(callsign)        
        call_with_ssid.extend('-'.encode('utf-8'))
        call_with_ssid.extend(str(ssid).encode('utf-8'))

        callsign_crc = get_crc_16(call_with_ssid)

        if callsign_crc == crc_to_check:
            print(call_with_ssid)
            return [True, bytes(call_with_ssid)]
    
    return [False, ""]



def encode_grid(grid):
    """
    @auther: DB1UJ
    Args:
      grid:string: maidenhead QTH locater [a-r][a-r][0-9][0-9][a-x][a-x]
    Returns:
      4 bytes contains 26 bit valid data with encoded grid locator
    """
    out_code_word = int(0)

    grid = grid.upper() # upper case to be save

    int_first = ord(grid[0])-65 # -65 offset for 'A' become zero, utf8 table
    int_sec   = ord(grid[1])-65 # -65 offset for 'A' become zero, utf8 table

    int_val = (int_first * 18) + int_sec # encode for modulo devision, 2 numbers in 1

    out_code_word = (int_val & 0b111111111) # only 9 bit LSB A - R * A - R is needed
    out_code_word = out_code_word << 9 # shift 9 bit left having space next bits, letter A-R * A-R

    int_val = int(grid[2:4]) # number string to number int, highest value 99
    out_code_word = out_code_word | (int_val & 0b1111111) # using bit OR to add new value
    out_code_word = out_code_word << 7 # shift 7 bit left having space next bits, letter A-X

    int_val = ord(grid[4])-65 # -65 offset for 'A' become zero, utf8 table
    out_code_word = out_code_word | (int_val & 0b11111) # using bit OR to add new value
    out_code_word = out_code_word << 5 # shift 5 bit left having space next bits, letter A-X

    int_val = ord(grid[5])-65 # -65 offset for 'A' become zero, utf8 table
    out_code_word = out_code_word | (int_val & 0b11111) # using bit OR to add new value

    return out_code_word.to_bytes(length=4, byteorder='big')

def decode_grid(b_code_word:bytes):
    """
    @auther: DB1UJ
    Args:
      b_code_word:bytes: 4 bytes with 26 bit valid data LSB
    Returns:
      grid:str: upper case maidenhead QTH locater [A-R][A-R][0-9][0-9][A-X][A-X]
    """
    code_word = int.from_bytes(b_code_word, byteorder='big', signed=False)

    grid = chr((code_word & 0b11111) + 65) 
    code_word = code_word >> 5

    grid = chr((code_word & 0b11111) + 65) + grid
    code_word = code_word >> 7

    grid = str(int(code_word & 0b1111111)) + grid
    if (code_word & 0b1111111) < 10:
        grid = '0' + grid
    code_word = code_word >> 9

    int_val = int(code_word & 0b111111111)
    int_first = int_val // 18
    int_sec   = int_val % 18
    grid = chr(int(int_first)+65) + chr(int(int_sec)+65) + grid

    return grid
