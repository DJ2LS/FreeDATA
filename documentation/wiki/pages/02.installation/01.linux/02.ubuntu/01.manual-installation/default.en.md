---
title: 'Manual Installation'
---

!!! **Note:** Tested with Ubuntu 20.04 LTS, Debian 10, Mint 20

##  1. Permissions
add user to dialout group to access serial devices without root
```
sudo adduser $USER dialout
logout / login
```
## 2. Dependencies
```
sudo apt install git build-essential cmake npm
sudo npm install -g n
sudo n stable
sudo apt install python3-hamlib (if not found: python3-libhamlib2)
sudo apt install python3 portaudio19-dev python3-pyaudio python3-pip python3-colorama
pip3 install psutil crcengine ujson pyserial numpy structlog
```

## 3. Install FreeDATA
```
git clone https://github.com/DJ2LS/FreeDATA.git
cd FreeDATA/gui
npm i
cd ..
```
## Optional: Install codec2
If you want to use the latest version of codec2, just download and compile it.
The tnc will detect, if a self compiled version is used. Otherwise a precompiled binary will be used.
```
cd tnc (FreeDATA/tnc)
git clone https://github.com/drowe67/codec2.git
cd codec2
mkdir build_linux
cd build_linux
cmake ..
make
```

## Optional: Update Hamlib
Older versions of Ubuntu, like Ubuntu 20.04 LTS or Suse have sometimes outdated versions of Hamlib in their repositories. If you need a newer version, because of your radio for example, you can install the latest version from source.

!! Please uninstall older hamlib version before installing from source with `sudo apt uninstall python3-libhamlib2`!
```
sudo apt install libusb-1.0-0 swig
cd ~/Downloads
https://github.com/Hamlib/Hamlib/releases/download/4.4/hamlib-4.4.tar.gz
tar xvf hamlib-4.4.tar.gz
cd hamlib-4.4
./configure --with-python-binding PYTHON=$(which python3)
make
sudo make install
sudo ldconfig
```