---
title: 'Manual installation'
---

!!! Tested with openSuse 15.3

!! FreeDATA had a lot of problems the last time it has been tested. Please be careful, specially with hamlib!
# 1. Permissions
add user to dialout group to access serial devices without root
```
sudo usermod -a -G dialout
```
# 2. Dependencies
```
sudo zypper install git cmake npm
sudo zypper install -t pattern devel_basis
sudo zypper install portaudio-devel python3-PyAudio
sudo npm install -g n
sudo n stable
pip3 install psutil crcengine ujson pyserial numpy structlog
```

# 3. Install hamlib python binding
```
sudo zypper install git python3-devel swig
cd ~/Downloads
wget https://github.com/Hamlib/Hamlib/releases/download/4.4/hamlib-4.4.tar.gz
tar xvf hamlib-4.4.tar.gz
cd hamlib-4.4
./configure --with-python-binding PYTHON=$(which python3)
make
sudo make install
sudo ldconfig
```

# 4. Install FreeDATA
```
git clone https://github.com/DJ2LS/FreeDATA.git
cd FreeDATA/gui
npm i
cd ..
```
# Optional: Install codec2
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