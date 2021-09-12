# codec2 | FreeDATA
My attempt to create a free and opensource TNC with a GUI for [codec2](https://github.com/drowe67/codec2) to send data over HF channels. 
The TNC itself will be completely controllable via network.

## Under development
The project is still a prototype and not usable at this time.
Build steps for other OS than Ubuntu are provided, but the bundle is only running on Ubuntu

## Manual Installation Ubuntu
### 1. Install dependencies and codec2-FreeDATA
A folder "codec2-FreeDATA" will be created in /home/[user]
codec2-FreeDATA needs codec2 to be installed within codec2-FreeDATA/tnc folder.
```
sudo apt install git build-essential cmake
sudo apt install npm
sudo apt install python3
pip3 install psutil
pip3 install crcengine
pip3 install ujson
pip3 install pyserial
pip3 install numpy

wget https://raw.githubusercontent.com/DJ2LS/codec2-FreeDATA/main/tools/install-codec2-FreeDATA.sh
chmod +x install-codec2-FreeDATA.sh
./install-codec2-FreeDATA.sh
```

### 2. starting tnc
You need to set the "--debug" option. Otherwise daemon.py is looking for precompiled binaries which causes an error
```
cd /home/[user]/codec2-FreeDATA/tnc
python3 daemon.py --debug
```

### 3. starting gui
There will be an error on startup, that "daemon" can't be found, This is because the gui is looking for precompiled tnc software. This error can be ignored, if you're running the tnc manually from source

The gui is creating a directory "codec2-FreeDATA" for saving settings in /home/[user]/.config/
```
cd /home/[user]/codec2-FreeDATA/gui
npx electron main.js
```







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
cd codec2-FreeDATA/gui
npm i
npm i electron
npx electron main.js
```

## GUI Preview
![alt text](https://github.com/DJ2LS/FreeDATA/blob/main/documentation/FreeDATA_GUI_Preview.png "GUI Preview")

## TNC Preview
![alt text](https://github.com/DJ2LS/FreeDATA/blob/main/documentation/FreeDATA_TNC_Preview.png "TNC Preview")

##
npm outdated --> list outdated npm packages
npx npm-check-updates -u --> updated all packages
npm install --> install all updated packages

## Credits
David Rowe and the FreeDV team for developing the modem and libraries
FreeDV Codec 2 : https://github.com/drowe67/codec2
