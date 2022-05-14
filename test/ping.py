 #!/usr/bin/env python3
# -*- coding: utf-8 -*-


import ctypes
from ctypes import *
import pathlib
import pyaudio
import time
import threading
import argparse
import sys

#--------------------------------------------GET PARAMETER INPUTS
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--bursts', dest="N_BURSTS", default=0, type=int)
parser.add_argument('--frames', dest="N_FRAMES_PER_BURST", default=0, type=int)
parser.add_argument('--delay', dest="DELAY_BETWEEN_BURSTS", default=0, type=int)
parser.add_argument('--txmode', dest="FREEDV_TX_MODE", default=0, type=int)
parser.add_argument('--rxmode', dest="FREEDV_RX_MODE", default=0, type=int)
parser.add_argument('--audiooutput', dest="AUDIO_OUTPUT", default=0, type=int)
parser.add_argument('--audioinput', dest="AUDIO_INPUT", default=0, type=int)
parser.add_argument('--debug', dest="DEBUGGING_MODE", action="store_true")

args, _ = parser.parse_known_args()


N_BURSTS = args.N_BURSTS
N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
DELAY_BETWEEN_BURSTS = args.DELAY_BETWEEN_BURSTS/1000

AUDIO_OUTPUT_DEVICE = args.AUDIO_OUTPUT
AUDIO_INPUT_DEVICE = args.AUDIO_INPUT

# 1024 good for mode 6
AUDIO_FRAMES_PER_BUFFER = 2048
MODEM_SAMPLE_RATE = 8000

FREEDV_TX_MODE = args.FREEDV_TX_MODE
FREEDV_RX_MODE = args.FREEDV_RX_MODE

DEBUGGING_MODE = args.DEBUGGING_MODE
        #-------------------------------------------- LOAD FREEDV
libname = pathlib.Path().absolute() / "codec2/build_linux/src/libcodec2.so"
c_lib = ctypes.CDLL(libname)

        #--------------------------------------------CREATE PYAUDIO  INSTANCE
p = pyaudio.PyAudio()
        #--------------------------------------------GET SUPPORTED SAMPLE RATES FROM SOUND DEVICE
#AUDIO_SAMPLE_RATE_TX = int(p.get_device_info_by_index(AUDIO_OUTPUT_DEVICE)['defaultSampleRate'])
#AUDIO_SAMPLE_RATE_RX = int(p.get_device_info_by_index(AUDIO_INPUT_DEVICE)['defaultSampleRate'])
AUDIO_SAMPLE_RATE_TX = 8000
AUDIO_SAMPLE_RATE_RX = 8000
        #--------------------------------------------OPEN AUDIO CHANNEL TX

stream_tx = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=AUDIO_SAMPLE_RATE_TX,
                            frames_per_buffer=AUDIO_FRAMES_PER_BUFFER, #n_nom_modem_samples
                            output=True,
                            output_device_index=AUDIO_OUTPUT_DEVICE,
                            )

stream_rx = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=AUDIO_SAMPLE_RATE_RX,
                            frames_per_buffer=AUDIO_FRAMES_PER_BUFFER,
                            input=True,
                            input_device_index=AUDIO_INPUT_DEVICE,
                            )





def receive():

    c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
    freedv = c_lib.freedv_open(FREEDV_RX_MODE)
    bytes_per_frame = int(c_lib.freedv_get_bits_per_modem_frame(freedv)/8)
    payload_per_frame = bytes_per_frame -2
    n_nom_modem_samples = c_lib.freedv_get_n_nom_modem_samples(freedv)
    n_tx_modem_samples = c_lib.freedv_get_n_tx_modem_samples(freedv) #get n_tx_modem_samples which defines the size of the modulation object # --> *2

    bytes_out = (ctypes.c_ubyte * bytes_per_frame) #bytes_per_frame
    bytes_out = bytes_out() #get pointer from bytes_out

    total_n_bytes = 0
    rx_total_frames = 0
    rx_frames = 0
    rx_bursts = 0
    receive = True
    while receive == True:
        time.sleep(0.01)

        nin = c_lib.freedv_nin(freedv)
        nin_converted = int(nin*(AUDIO_SAMPLE_RATE_RX/MODEM_SAMPLE_RATE))
        if DEBUGGING_MODE == True:
            print("-----------------------------")
            print("NIN:  " + str(nin) + " [ " + str(nin_converted) + " ]")

        data_in = stream_rx.read(nin_converted,  exception_on_overflow = False)
        data_in = data_in.rstrip(b'\x00')

        c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), bytes_out, data_in] # check if really neccessary
        nbytes = c_lib.freedv_rawdatarx(freedv, bytes_out, data_in) # demodulate audio
        total_n_bytes = total_n_bytes + nbytes
        if DEBUGGING_MODE == True:
            print("SYNC: " + str(c_lib.freedv_get_rx_status(freedv)))

        if nbytes == bytes_per_frame:
            rx_total_frames = rx_total_frames + 1
            rx_frames = rx_frames + 1

            if rx_frames == N_FRAMES_PER_BURST:
                rx_frames = 0
                rx_bursts = rx_bursts + 1
                c_lib.freedv_set_sync(freedv,0)


            burst = bytes_out[0]
            n_total_burst = bytes_out[1]
            frame = bytes_out[2]
            n_total_frame = bytes_out[3]


            print("RX | PONG | BURST [" + str(burst) + "/" + str(n_total_burst) +  "] FRAME [" + str(frame) + "/" + str(n_total_frame) + "]")
            print("-----------------------------------------------------------------")
            c_lib.freedv_set_sync(freedv,0)


        if rx_bursts == N_BURSTS:
            receive = False



RECEIVE = threading.Thread(target=receive, name="RECEIVE THREAD")
RECEIVE.start()


c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
freedv = c_lib.freedv_open(FREEDV_TX_MODE)
bytes_per_frame = int(c_lib.freedv_get_bits_per_modem_frame(freedv)/8)
payload_per_frame = bytes_per_frame -2
n_nom_modem_samples = c_lib.freedv_get_n_nom_modem_samples(freedv)
n_tx_modem_samples = c_lib.freedv_get_n_tx_modem_samples(freedv) #get n_tx_modem_samples which defines the size of the modulation object # --> *2

mod_out = ctypes.c_short * n_tx_modem_samples
mod_out = mod_out()
mod_out_preamble = ctypes.c_short * (1760*2) #1760 for mode 10,11,12 #4000 for mode 9
mod_out_preamble = mod_out_preamble()



print("BURSTS: " + str(N_BURSTS) + " FRAMES: " + str(N_FRAMES_PER_BURST) )
print("-----------------------------------------------------------------")

for i in range(0,N_BURSTS):

    c_lib.freedv_rawdatapreambletx(freedv, mod_out_preamble);

    txbuffer = bytearray()
    txbuffer += bytes(mod_out_preamble)

    for n in range(0,N_FRAMES_PER_BURST):

        data_out = bytearray()
        data_out += bytes([i+1])
        data_out += bytes([N_BURSTS])
        data_out += bytes([n+1])
        data_out += bytes([N_FRAMES_PER_BURST])

        buffer = bytearray(payload_per_frame) # use this if CRC16 checksum is required ( DATA1-3)
        buffer[:len(data_out)] = data_out # set buffersize to length of data which will be send

        crc = ctypes.c_ushort(c_lib.freedv_gen_crc16(bytes(buffer), payload_per_frame))     # generate CRC16
        crc = crc.value.to_bytes(2, byteorder='big') # convert crc to 2 byte hex string
        buffer += crc        # append crc16 to buffer

        data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
        c_lib.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and safe it into mod_out pointer

        txbuffer += bytes(mod_out)

    print("TX | PING | BURST [" + str(i+1) + "/" + str(N_BURSTS) +  "] FRAME [" + str(n+1) + "/" + str(N_FRAMES_PER_BURST) + "]")
    stream_tx.write(bytes(txbuffer))
    ACK_TIMEOUT = time.time() + 3
    txbuffer = bytearray()

    #time.sleep(DELAY_BETWEEN_BURSTS)

    # WAIT UNTIL WE RECEIVD AN ACK/DATAC0 FRAME
    while ACK_TIMEOUT >= time.time():
        time.sleep(0.01)


time.sleep(1)
stream_tx.close()
p.terminate()
