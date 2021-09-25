# FreeDATA
My attempt to create a free and opensource TNC with a GUI for [codec2](https://github.com/drowe67/codec2) to send data over HF channels. 

## Under development
This project is still a prototype and not usable at this time.
Build steps for other OS than Ubuntu are provided, but not working, yet.

## Credits
* David Rowe and the FreeDV team for developing the modem and libraries -
FreeDV Codec 2 : https://github.com/drowe67/codec2
* xssfox, his repository helped me a lot in an early stage of development -
xssfox : https://github.com/xssfox/freedv-tnc
* Wolfgang, for lending me his radio so I'm able to do real hf tests

## Running the app bundle
Just download the latest developer release from the releases section, unpack it and just start the ".AppImage file". No more dependencies

## Manual Installation Ubuntu
### 0. add user to dialout group to access serial devices without root
```
sudo adduser $USER dialout
logout / login
```

### 1. Install dependencies, codec2 and FreeDATA
```
sudo apt install git build-essential cmake
sudo apt install npm
npm cache clean -f
sudo npm install -g n
sudo n stable
sudo apt install python3
sudo apt install portaudio19-dev
sudo apt install python3-pyaudio
sudo apt install python3-pip
pip3 install psutil
pip3 install crcengine
pip3 install ujson
pip3 install pyserial
pip3 install numpy

git clone https://github.com/DJ2LS/FreeDATA.git
cd FreeDATA/gui
npm i
cd ..
cd tnc

git clone https://github.com/drowe67/codec2.git
cd codec2
mkdir build_linux
cd build_linux
cmake ..
make

```

### 2. starting tnc
You need to set the "--debug" option. Otherwise daemon.py is looking for precompiled binaries which causes an error
```
cd /home/[user]/FreeDATA/tnc
python3 daemon.py --debug
```
A successfull start looks like this. 
```
SRV | STARTING TCP/IP SOCKET FOR CMD ON PORT: 3001
```
As soon as you're connected the gui, it could look like below. If you're getting a bunch of errors from ALSA lib like below - this should't affect usability 
```
SRV | STARTING TCP/IP SOCKET FOR CMD ON PORT: 3001
Client connected...
ALSA lib pcm.c:2660:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.rear
ALSA lib pcm.c:2660:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.center_lfe
ALSA lib pcm.c:2660:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.side
...<snip>...
```


### 3. starting gui
There will be an error on startup, that "daemon" can't be found, This is because the gui is looking for precompiled tnc software. This error can be ignored, if you're running the tnc manually from source

The gui is creating a directory "FreeDATA" for saving settings in /home/[user]/.config/
```
cd /home/[user]/FreeDATA/gui
npx electron main.js
```
If you start the gui, it will have a look for the daemon, which is by default "localhost / 127.0.0.1". The main window will stay blured as long as it can't connect to the daemon. If you want to connect to a daemon which is running on another host, just select it via "remote TNC" and enter the ip address.
![gui disconnected](https://raw.githubusercontent.com/DJ2LS/FreeDATA/main/documentation/codec2-FreeDATA-start-disconnected.png "TNC disconnected")

As soon as the gui is able to connect to the daemon, the main window will be getting clear and you can see some settings like your audio devices and connected USB devices like a USB Interface III for example.
![gui connected](https://raw.githubusercontent.com/DJ2LS/FreeDATA/main/documentation/codec2-FreeDATA-start-connected.png "TNC connected")



# ----------------------------------------------------------------
## Manual Installation macOS
### Install brew and python3
#### https://docs.python-guide.org/starting/install3/osx/

```
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
brew install python
pip3 install psutil
pip3 install crcengine
pip3 install ujson
pip3 install pyserial
pip3 install numpy

```
### Install dependencies
```
xcode-select --install
brew remove portaudio
brew install portaudio
pip3 install pyaudio
```

## Manual Installation Windows
### Install python3
```
Download Python from https://www.python.org/downloads/
Add Python to systempath https://www.educative.io/edpresso/how-to-add-python-to-path-variable-in-windows
Download and install pyaudio from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
eg.: pip install PyAudio-0.2.11-cp37-cp37m-win_amd64.whl
pip install psutil
pip install crcengine
pip install ujson
pip install pyserial
pip install numpy
python daemon.py

```

### Install nodejs
```
https://nodejs.org/en/download/
cd FreeDATA/gui
npm i
npm i electron
npx electron main.js
```
### npm updating
* npm outdated --> list outdated npm packages
* npx npm-check-updates -u --> updated all packages
* npm install --> install all updated packages

* npm cache clean -f
* sudo npm install -g n
* sudo n stable --> upgrade node to latest version
