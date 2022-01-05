
# Instructions

1. Install:
   ```
   cd FreeDATA
   mkdir build
   cd build
   cmake -DCODEC2_BUILD_DIR=$HOME/codec2/build_linux ..
   ```
2. List available tests:
   ```
   ctest -N
   Test project /home/david/FreeDATA/build
   Test #1: 000_audio_tests
   Test #2: 001_highsnr_stdio_audio

   Total Tests: 2
   ```
3. Run tests:
   ```
   ctest --output-on-failure
   ```
4. Run tests verbosely:
   ```
   ctest -V
   ```




# 001_HIGHSNR_STDIO_AUDIO TEST SUITE

1. Install
   ```
   sudo apt update
   sudo apt upgrade
   sudo apt install git cmake build-essential python3-pip portaudio19-dev python3-pyaudio
   pip3 install crcengine
   pip3 install threading
   ```
1. Install codec2, and set up the `libcodec2.so` shared library path, for example
   ```
   export LD_LIBRARY_PATH=${HOME}/codec2/build_linux/src
   ```

## STDIO tests

Pipes are used to move audio samples from the Tx to Rx:

```
python3 test_tx.py --mode datac1 --delay 500 --frames 2 --bursts 1 | python3 test_rx.py --mode datac1 --frames 2 --bursts 1
```

## AUDIO test via virtual audio devices

1. Create virtual audio devices. Note: This command needs to be run again after every reboot
   ```
   sudo modprobe snd-aloop index=1,2 enable=1,1 pcm_substreams=1,1 id=CHAT1,CHAT2 
   ```

1. Check if devices have been created
   ```
    aplay -l

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
   
1. Determine the audio device number you would like to use:
   ```
   python3 test_rx.py --list
   <snip>
   audiodev:  0 HDA Intel PCH: ALC269VC Analog (hw:0,0)
   audiodev:  1 HDA Intel PCH: HDMI 0 (hw:0,3)
   audiodev:  2 HDA Intel PCH: HDMI 1 (hw:0,7)
   audiodev:  3 HDA Intel PCH: HDMI 2 (hw:0,8)
   audiodev:  4 Loopback: PCM (hw:1,0)
   audiodev:  5 Loopback: PCM (hw:1,1)
   audiodev:  6 Loopback: PCM (hw:2,0)
   audiodev:  7 Loopback: PCM (hw:2,1)
   ```
   In this case we choose audiodev 4 for the RX and 5 for the Tx.

1. Start the Rx first, then Tx in separate consoles:
   ```
   python3 test_rx.py --mode datac0 --frames 2 --bursts 1 --audiodev 4 --debug
   python3 test_tx.py --mode datac0 --frames 2 --bursts 1 --audiodev 5
