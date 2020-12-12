# FreeDV-Socket-TNC
My first attempt to learn more about FreeDV and how to create a TNC which gets data from a TCP/IP Socket.

## Setup

sudo apt install portaudio19-dev


## Run
./__main__.py --rx-sound-device 2 --tx-sound-device 2 --port 3000

## Parameters
--rx-sound-device <1>
--tx-sound-device <1>
--port <3000>

To list all audio devices run 
./__main__.py --list-audio-devices


## Socket Commands

BC:<DATA>    Send a simple broadcast




##Credits

David Rowe and the FreeDV team for developing the modem and libraries
FreeDV Codec 2 : https://github.com/drowe67/codec2


This software has been heavily inspired by https://github.com/xssfox/freedv-tnc/
