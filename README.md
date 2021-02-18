# FreeDV-JATE
## FreeDV- Just Another TNC Experiment
My first attempt to learn more about FreeDV and how to create a TNC which gets data from a TCP/IP socket 

## ToDo

- [x] ARQ: Stop-And-Wait
- [x] ARQ: Go-Back-N
- [x] ARQ: Selective repeating of lost arq frames
- [x] ARQ: Dynamic number of frames per burst
- [ ] ARQ: Set frames per burst automatically by channel quality
- [x] SOCKET: Run commands via TCP/IP socket
- [ ] TRX: Control radio via hamlib
- [ ] MODE: Beacon
- [ ] MODE: Broadcast
- [ ] MODE: ARQ AX25
- [ ] MODE: Gear shifting ARQ
- [ ] TNC: CLI GUI for basic settings
- [ ] TNC: Multicore support
- [ ] MODEM: Sample rate conversion

## Setup
Install FreeDV-Socket-TNC directly to home folder and compile codec2 automatically
```
sudo apt install portaudio19-dev build-essential cmake
wget https://raw.githubusercontent.com/DJ2LS/FreeDV-Socket-TNC/dev/install_socket_tnc.sh -O ~/install_socket_tnc.sh
chmod +x ~/install_socket_tnc.sh
./install_socket_tnc.sh
```

## Usage main program
```
./main.py --port 3000 --tx 1 --rx 1 --mode 12
```

## Usage TCP/IP socket client
```
python3 readfromsocket.py --port 3000 --data "GET:RX_BUFFER:0
```

## Socket Commands

#### SOCKETTEST
Message for testing purposes which repeats:
```
SOCKETTEST
```
"WELL DONE! YOU ARE ABLE TO COMMUNICATE WITH THE TNC"


#### TRANSMIT ARQ MESSAGE 'HELLO!'
```
ARQ:HELLO!
```

#### SET NEW CALLSIGN
```
SET:MYCALLSIGN:AA1AA
```

#### GET CALLSIGN
```
GET:MYCALLSIGN
```

#### GET CALLSIGN CRC8
```
GET:MYCALLSIGN_CRC8
```

#### GET DX CALLSIGN
```
GET:DXCALLSIGN
```

#### GET ARQ STATE
```
GET:ARQ_STATE
```

#### GET RX BUFFER LENGTH / SIZE
```
GET:RX_BUFFER_LENGTH
```

#### GET RX BUFFER
```
GET:RX_BUFFER:POSITION
```
Position = 0 --> Latest Data
Position 1-N --> Buffer positions

#### DELETE RX BUFFER
```
DEL:RX_BUFFER
```




## Other stuff

### Audio sinkhole
Send real audio without external devices or sound cards
```
sudo modprobe snd-aloop index=1,2 enable=1,1 pcm_substreams=1,1 id=CHAT1,CHAT2 
```
### TNC 1
```
./main.py --port 3000 --tx 1 --rx 1
```
### TNC 2
```
./main.py --port 3001 --tx 2 --rx 2
```


## Credits

David Rowe and the FreeDV team for developing the modem and libraries
FreeDV Codec 2 : https://github.com/drowe67/codec2


This software has been inspired by https://github.com/xssfox/freedv-tnc/

