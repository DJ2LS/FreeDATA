# FreeDV-Socket-TNC
My first attempt to learn more about FreeDV and how to create a TNC which gets data from a TCP/IP Socket.



## Credits

David Rowe and the FreeDV team for developing the modem and libraries
FreeDV Codec 2 : https://github.com/drowe67/codec2


This software has been heavily inspired by https://github.com/xssfox/freedv-tnc/





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
./main.py --port 3000 --tx 1 --rx 1
```

## Usage testclient
```
./socketclient.py --port 3000 --data "BC: hello"
```


## Socket Commands

Send a simple broadcast
```
BC:<DATA>    
```
Send an ARQ like frame which will ack the receiver for acknowledgement
```
ACK:<DATA>    
```


## Other stuff

Create audio sinkhole
```
sudo modprobe snd-aloop index=1,2 enable=1,1 pcm_substreams=1,1 id=CHAT1,CHAT2 
```

