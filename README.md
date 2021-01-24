
# FreeDV-JATE [Just Another TNC Experiment]

## 001_HIGHSNR_STDIO_AUDIO TEST SUITE

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

    python3 TEST_TX.py --mode 12 --delay 500 --frames 2 --bursts 1 | python3 TEST_RX.py --mode 12 --frames 2 --bursts 1



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

    python3 TEST_RX.py --mode 12 --frames 2 --bursts 1 --input "audio" --audioinput 2 --debug
    
##### TX side

    python3 TEST_TX.py --mode 12 --delay 500 --frames 2 --bursts 1 --output "audio" --audiooutput 1


