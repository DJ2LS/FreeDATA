# FreeDATA

My attempt to create a free and open-source TNC with a GUI for [codec2](https://github.com/drowe67/codec2) with the idea of sending messages and data from one network based application.

[mailing-list](https://groups.io/g/freedata)

## Under development

![Build](https://github.com/DJ2LS/FreeDATA/actions/workflows/build_multiplatform.yml/badge.svg)
[![CodeFactor](https://www.codefactor.io/repository/github/dj2ls/freedata/badge)](https://www.codefactor.io/repository/github/dj2ls/freedata)

Please keep in mind, this project is still under development with many issues which need to be solved.

### existing/planned TNC features

- [x] network based
- [x] raw data transfer
- [x] fft output
- [x] JSON based commands
- [x] speed levels
- [x] ARQ - stop and wait
- [x] SNR operation level SNR > 0dB MPP/MPD
- [x] file compression
- [x] auto updater
- [x] channel measurement
- [ ] hybrid ARQ
- [ ] tbc...

### existing/planned Chat features

- [x] chat messages
- [x] file transfer
- [x] file transfer with chat message
- [x] database for not loosing messages
- [x] smileys
- [ ] database network sync
- [ ] voice messages
- [ ] image compression
- [ ] status messages
- [ ] avatars
- [ ] tbc...

## Data Preview

![preview](https://github.com/DJ2LS/FreeDATA/blob/main/documentation/data_preview.gif?raw=true "Preview")

## Chat Preview

![preview](https://github.com/DJ2LS/FreeDATA/blob/main/documentation/chat_preview_fast.gif?raw=true "Preview")

## Installation

Please check the [wiki](https://wiki.freedata.app) for installation instructions
Please check the ['Releases'](https://github.com/DJ2LS/FreeDATA/releases) section for downloading precompiled builds

## Credits

- David Rowe and the FreeDV team for developing the modem and libraries -
  FreeDV Codec 2 : https://github.com/drowe67/codec2
- xssfox, her repository helped a lot in an early stage of development -
  xssfox : https://github.com/xssfox/freedv-tnc
