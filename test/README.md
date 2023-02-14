# Unit Test Menu

The following `CTest` tests cover some TNC functionality and the interface to codec2:

1. Name: `audio_buffer`
   Tests the thread safety of the audio buffer routines.
1. Name: `resampler`
   Tests FreeDATA audio resampling from 48KHz to 8KHz.
1. Name: `tnc_state_machine`
   Tests TNC transitions between states. This needs to be expanded.
1. Name: `tnc_irs_iss`
   Tests TNC modem queue interaction. This needs to be expanded.
1. Name: `helper_routines`
   Tests various helper routines.
1. Name: `py_highsnr_stdio_P_P_multi`
   Tests a high signal-to-noise ratio (good quality) audio path using multiple codecs. (Pure python.)
1. Name: `py_highsnr_stdio_P_P_datacx`
   Tests a high signal-to-noise ratio audio path using multiple individual codecs.
1. Name: `py_highsnr_stdio_P_C_datacx`
   Tests a high signal-to-noise ratio audio path using multiple individual codecs.
1. Name: `py_highsnr_stdio_C_P_datacx`
   Tests a high signal-to-noise ratio audio path using multiple individual codecs.
1. Name: `highsnr_stdio_P_C_single`
   Tests compatibility with FreeDATA's transmit and freedv's raw data receive.
1. Name: `highsnr_stdio_C_P_single`
   Tests compatibility with freedv's raw data transmit and FreeDATA's receive.
1. Name: `highsnr_stdio_P_P_single`
   Tests a high signal-to-noise ratio audio path using multiple codecs. (Requires POSIX system.)
1. Name: `highsnr_stdio_P_P_multi`
   Tests a high signal-to-noise ratio audio path using multiple codecs. (Requires POSIX system.)

The following tests can not currently be run with GitHub's pipeline as they require the ALSA dummy device
kernel module to be installed. They also do not perform reliably. These tests are slowly being
replaced with equivalent pipeline-compatible tests.

1. Name: `highsnr_virtual1_P_P_single_alsa`
   Tests a high signal-to-noise ratio audio path using a single codec directly over an ALSA dummy device.
1. Name: `highsnr_virtual2_P_P_single`
   Tests a high signal-to-noise ratio audio path using a single codec over an ALSA dummy device.
   **Not functional** due to an incompatibility between the two scripts in the way they determine audio devices.
1. Name: `highsnr_virtual3_P_P_multi`
   Tests a high signal-to-noise ratio audio path using multiple codecs over an ALSA dummy device.
1. Name: `highsnr_virtual4_P_P_single_callback`
   **Not functional** due to an incompatibility between the two scripts in the way they determine audio devices.
1. Name: `highsnr_virtual4_P_P_single_callback_outside`
   **Not functional** due to an incompatibility between the two scripts in the way they determine audio devices.
1. Name: `highsnr_virtual5_P_P_multi_callback`
1. Name: `highsnr_virtual5_P_P_multi_callback_outside`

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
   or, to include only GitHub-compatible tests:
   ```
   GITHUB_RUN_ID=0 ctest --output-on-failure
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
python3 util_tx.py --mode datac1 --delay 500 --frames 2 --bursts 1 | python3 util_rx.py --mode datac1 --frames 2 --bursts 1
```

## Moderate signal-to-noise ratio (SNR)

Tests need to be written that test a low SNR data path so that the TNC performance when packets are lost can be evaluated.

## AUDIO test via virtual audio devices

### Important:

The virtual audio devices are great for testing, but they are also a little tricky to handle. So there's a high chance, the tests will fail, if you are running them via virtual audio devices. You should run the tests several times, while keeping this in mind. Most time the ctest is working even if it is failing.

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
   python3 util_rx.py --list
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
   python3 util_rx.py --mode datac0 --frames 2 --bursts 1 --audiodev 4 --debug
   python3 util_tx.py --mode datac0 --frames 2 --bursts 1 --audiodev 5
   ```
