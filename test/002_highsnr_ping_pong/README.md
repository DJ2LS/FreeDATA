
# FreeDV-JATE [Just Another TNC Experiment]

## 002_HIGHSNR_PING_PONG

### INSTALL TEST SUITE
#### Install prerequierements
```
sudo apt update
sudo apt upgrade
sudo apt install git cmake build-essential python3-pip portaudio19-dev python3-pyaudio
pip3 install crcengine
pip3 install threading
```

Go into a directory of your choice
Run the following commands --> They will download and compile the latest codec2 ( dr-packet ) files and LPCNet as well into the directory of your choice
```
wget https://raw.githubusercontent.com/DJ2LS/FreeDV-JATE/002_HIGHSNR_PING_PONG/install_test_suite.sh
chmod +x install_test_suite.sh
./install_test_suite.sh
```



### PARAMETERS
| parameter | description | side
|--|--|--|
| - -txmode 12 | set the mode for FreeDV ( 10,11,12,14 ) | Terminal 1 & Terminal 2
| - -rxmode 14 | set the mode for FreeDV ( 10,11,12,14 ) | Terminal 1 & Terminal 2
| - -frames 1 | set the number of frames per burst | Terminal 1
| - -bursts 1 | set the number of bursts | Terminal 1
| - -audioinput 2 | set the audio device | Terminal 1 & Terminal 2
| - -audiooutput 1 | set the audio device | Terminal 1 & Terminal 2
| - -debug | if used, print additional debugging output | Terminal 1 & Terminal 2
  	



### AUDIO TESTS VIA VIRTUAL AUDIO DEVICE

 #### Create audio sinkhole and subdevices
 Note: This command needs to be run again after every reboot
 ```
sudo modprobe snd-aloop index=1,2 enable=1,1 pcm_substreams=1,1 id=CHAT1,CHAT2 
```
check if devices have been created



    aplay -l
Output should be like this:
```
    Karte 0: Intel [HDA Intel], Gerät 0: Generic Analog [Generic Analog]
      Sub-Geräte: 1/1
      Sub-Gerät #0: subdevice #0
    Karte 1: CHAT1 [Loopback], Gerät 0: Loopback PCM [Loopback PCM]
      Sub-Geräte: 1/1
      Sub-Gerät #0: subdevice #0
    Karte 1: CHAT1 [Loopback], Gerät 1: Loopback PCM [Loopback PCM]
      Sub-Geräte: 1/1
      Sub-Gerät #0: subdevice #0
    Karte 2: CHAT2 [Loopback], Gerät 0: Loopback PCM [Loopback PCM]
      Sub-Geräte: 1/1
      Sub-Gerät #0: subdevice #0
    Karte 2: CHAT2 [Loopback], Gerät 1: Loopback PCM [Loopback PCM]
      Sub-Geräte: 1/1
      Sub-Gerät #0: subdevice #0
```

### Run tests:

#### Terminal 1: Ping
```
python3 PING.py --txmode 12 --rxmode 14 --audioinput 2 --audiooutput 2 --frames 1 --bursts 2
```
Output
```
BURSTS: 2 FRAMES: 1
-----------------------------------------------------------------
TX | PING | BURST [1/2] FRAME [1/1]
RX | PONG | BURST [1/2] FRAME [1/1]
-----------------------------------------------------------------
TX | PING | BURST [2/2] FRAME [1/1]
RX | PONG | BURST [2/2] FRAME [1/1]
```

#### Terminal 2: Pong
```
python3 PONG.py --txmode 14 --rxmode 12 --audioinput 2 --audiooutput 2
```
Output
```
RX | BURST [1/2] FRAME [1/1] >>> SENDING PONG
RX | BURST [2/2] FRAME [1/1] >>> SENDING PONG
```
