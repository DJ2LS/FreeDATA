
# FreeDV-JATE [Just Another TNC Experiment]

## 001_HIGHSNR_STDIO_AUDIO TEST SUITE

### INSTALL TEST SUITE
#### Install prerequierements
```
sudo apt update
sudo apt upgrade
sudo apt install git cmake build-essential python3-pip portaudio19-dev python3-pyaudio
pip3 install crcengine
pip3 install threading
```

Change into a directory of your choice
Run the following commands --> They will download and compile the latest codec2 ( dr-packet ) files and LPCNet as well into the directory of your choice
```
wget https://raw.githubusercontent.com/DJ2LS/FreeDV-JATE/001_HIGHSNR_STDIO_AUDIO/install_test_suite.sh
chmod +x install_test_suite.sh
./install_test_suite.sh
```



### PARAMETERS
| parameter | description | side
|--|--|--|
| - -mode 12 | set the mode for FreeDV ( 10,11,12 ) | TX & RX
| - -delay 1 | set the delay between burst | TX
| - -frames 1 | set the number of frames per burst | TX & RX
| - -bursts 1 | set the number of bursts | TX & RX
| - -input "audio" | if set, program switches to audio instead of stdin | RX
| - -audioinput 2 | set the audio device | RX
| - -output "audio" | if set, program switches to audio instead of stdout | TX
| - -audiooutput 1 | set the audio device | TX
| - -debug | if used, print additional debugging output | RX
  	


### STDIO TESTS FOR TERMINAL USAGE ONLY

    python3 test_tx.py --mode 12 --delay 500 --frames 2 --bursts 1 | python3 test_rx.py --mode 12 --frames 2 --bursts 1



### AUDIO TESTS VIA VIRTUAL AUDIO DEVICE

 #### Create audio sinkhole and subdevices
 Note: This command needs to be run again after every reboot
 ```
sudo modprobe snd-aloop index=1,2 enable=1,1 pcm_substreams=1,1 id=CHAT1,CHAT2 
```
check if devices have been created



    aplay -l
Output should be like this:


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

#### Run tests:
Its important, to run TEST_RX at first to reduce the chance that we get some system side audio errors. Tests are showing, that its important to start with audio device "2" at first and then go to the lower virtual devices "1". 
Audio device "0" is the default sound card. 

##### RX side

    python3 test_rx.py --mode 12 --frames 2 --bursts 1 --input "audio" --audioinput 2 --debug
    
##### TX side

    python3 test_tx.py --mode 12 --delay 500 --frames 2 --bursts 1 --output "audio" --audiooutput 1


