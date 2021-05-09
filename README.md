# FreeDV-JATE
## FreeDV- Just Another TNC Experiment
My first attempt to learn more about FreeDV and how to create a TNC which gets data from a TCP/IP socket 


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
python3 main.py --rx 1 --tx 1 --deviceport /dev/ttyUSB0 --deviceid 311
```

## Usage GUI
```
cd tools/tnc_gui
python3 tnc_gui.py
```
