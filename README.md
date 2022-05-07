# FreeDATA
My attempt to create a free and open-source TNC with a GUI for [codec2](https://github.com/drowe67/codec2) with the idea of sending messages and data from one network based application.

[mailing-list](https://groups.io/g/freedata)

## Under development

![Build Windows](https://github.com/DJ2LS/FreeDATA/actions/workflows/build-project-win.yml/badge.svg)
![Build Linux](https://github.com/DJ2LS/FreeDATA/actions/workflows/build-project-linux.yml/badge.svg)
![Build macOS](https://github.com/DJ2LS/FreeDATA/actions/workflows/build-project-mac.yml/badge.svg)

Please keep in mind, that this project is still a prototype with many issues which need to be solved.
Build steps for other OS than Ubuntu are provided, but not fully working, yet.

Please check the ['Releases'](https://github.com/DJ2LS/FreeDATA/releases) section for downloading nightly builds

## Preview
![preview](https://github.com/DJ2LS/FreeDATA/blob/main/documentation/FreeDATA_preview.gif?raw=true "Preview")

## Credits
* David Rowe and the FreeDV team for developing the modem and libraries -
FreeDV Codec 2 : https://github.com/drowe67/codec2
* xssfox, her repository helped me a lot in an early stage of development -
xssfox : https://github.com/xssfox/freedv-tnc
* Wolfgang, for lending me his radio, so I'm able to do real hf tests

## Running the Ubuntu app bundle
Download the latest developer release from the releases section, unpack it and just start the ".AppImage file". No more dependencies

## Installation
Please check the [wiki](https://wiki.freedata.app) for installation instructions

## Code Unit Tests
The following tests cover some TNC functionality and the interface to codec2:
1. Name: audio_buffer
   Tests the thread safety of the audio buffer routines.
2. Name: resampler
   Tests FreeDATA audio resampling from 48KHz to 8KHz.
3. Name: tnc_state_machine
   Tests TNC transitions between states.
4. Name: helper_routines
   Tests various helper routines.
5. Name: py_highsnr_stdio_P_P_multi
   Tests a high signal-to-noise ratio (good quality) audio path using multiple codecs. (Pure python.)
6. Name: py_highsnr_stdio_P_P_datacx
   Tests a high signal-to-noise ratio audio path using multiple individual codecs.  (Pure python.)
7. Name: highsnr_stdio_P_C_single
   Tests compatibility with FreeDATA's transmit and freedv's raw data receive.
8. Name: highsnr_stdio_C_P_single
   Tests compatibility with freedv's raw data transmit and FreeDATA's receive.
9. Name: highsnr_stdio_P_P_single
   Tests a high signal-to-noise ratio audio path using multiple codecs. (Requires POSIX system.)
10. Name: highsnr_stdio_P_P_multi
    Tests a high signal-to-noise ratio audio path using multiple codecs. (Requires POSIX system.)

The following tests can not currently be run with Github's pipeline as they require the ALSA dummy device
kernel module to be installed. They also do not perform reliably. These tests are slowly being
replaced with equivalent pipeline-compatible tests.
11. Name: highsnr_virtual1_P_P_single_alsa
    Tests a high signal-to-noise ratio audio path using a single codec directly over an ALSA dummy device.
12. Name: highsnr_virtual2_P_P_single
    Tests a high signal-to-noise ratio audio path using a single codec over an ALSA dummy device.
13. Name: highsnr_virtual3_P_P_multi
    Tests a high signal-to-noise ratio audio path using multiple codecs over an ALSA dummy device.
14. Name: highsnr_virtual4_P_P_single_callback
15. Name: highsnr_virtual4_P_P_single_callback_outside
16. Name: highsnr_virtual5_P_P_multi_callback
17. Name: highsnr_virtual5_P_P_multi_callback_outside
18. Name: highsnr_ARQ_short

