# FreeDATA
My attempt to create a free and opensource TNC with a GUI for [codec2](https://github.com/drowe67/codec2) to send data over HF channels. 

## Under development
This project is still a prototype and not usable at this time.
Build steps for other OS than Ubuntu are provided, but not working, yet.

## Credits
* David Rowe and the FreeDV team for developing the modem and libraries -
FreeDV Codec 2 : https://github.com/drowe67/codec2
* xssfox, her repository helped me a lot in an early stage of development -
xssfox : https://github.com/xssfox/freedv-tnc
* Wolfgang, for lending me his radio so I'm able to do real hf tests

## Running the Ubuntu app bundle
Just download the latest developer release from the releases section, unpack it and just start the ".AppImage file". No more dependencies

## Manual Installation Ubuntu
### 0. add user to dialout group to access serial devices without root
```
sudo adduser $USER dialout
logout / login
```
### 1. Install dependencies, codec2 and FreeDATA
#### 1.1 Dependencies
```
sudo apt install git build-essential cmake npm
sudo npm install -g n
sudo n stable
sudo apt install python3-hamlib (if not found: python3-libhamlib2)
sudo apt install python3 portaudio19-dev python3-pyaudio python3-pip
pip3 install psutil crcengine ujson pyserial numpy structlog
```
#### 1.2 Install FreeDATA
```
git clone https://github.com/DJ2LS/FreeDATA.git
cd FreeDATA/gui
npm i
cd ..
```
#### Optional: Install codec2
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
#### Optional: Install newer/latest Hamlib if needed
Older versions of Ubuntu, like Ubuntu 20.04 LTS or Suse have sometimes outdated versions of Hamlib in their repositories. If you need a newer version, because of your radio for example, you can install the latest version from source.
```
sudo apt install libusb-1.0-0
cd ~/Downloads
wget https://github.com/Hamlib/Hamlib/releases/download/4.3.1/hamlib-4.3.1.tar.gz
tar xvf hamlib-4.3.1.tar.gz
cd hamlib-4.3.1
./configure --with-python-binding PYTHON=$(which python3)
make
sudo make install
sudo ldconfig
```

### 2. Starting FreeDATA
#### 2.1 Starting the TNC daemon
```
cd /home/$USER/FreeDATA/tnc
python3 daemon.py
```
A successfull start looks like this. 
```
2021-11-24 17:45:40 [info     ] [DMN] Starting...              python=3.8
2021-11-24 17:45:40 [info     ] [DMN] Hamlib found             version=4.3
2021-11-24 17:45:40 [info     ] [DMN] Starting TCP/IP socket   port=3001
```


### 2.2 Starting the GUI
* Note: There will be an error on startup, that "daemon" can't be found, This is because the gui is looking for precompiled tnc software. This error can be ignored, if you're running the tnc manually from source and should occur if you're using the app bundle.

* The gui is creating a directory "FreeDATA" for saving settings in /home/$USER/.config/
```
cd /home/$USER/FreeDATA/gui
npx electron main.js
```
If you're starting the gui, it will have a look for the daemon, which is by default "localhost / 127.0.0.1". The main window will stay blured as long as it can't connect to the daemon. 
![gui disconnected](https://raw.githubusercontent.com/DJ2LS/FreeDATA/main/documentation/FreeDATA-no-daemon-connection.png "TNC disconnected")

If you want to connect to a daemon which is running on another host, just select it via the ethernet icon and enter the ip address.
![gui disconnected](https://raw.githubusercontent.com/DJ2LS/FreeDATA/main/documentation/FreeDATA-connect-to-remote-daemon.png "TNC disconnected")

As soon as the gui is able to connect to the daemon, the main window will be getting clear and you can see some settings like your audio devices and connected USB devices like a USB Interface III or the radio itself.
You can also set advanced hamlib settings or test them. Your settings will be saved, as soon as you start the tnc.
![gui connected](https://raw.githubusercontent.com/DJ2LS/FreeDATA/main/documentation/FreeDATA-settings.png "TNC connected")

If you set your radio settings correctly, you can start the TNC. The settings dialog will be hidden and you can control the TNC now.
![gui connected](https://raw.githubusercontent.com/DJ2LS/FreeDATA/main/documentation/FreeDATA-tnc-running.png "TNC connected")


# ------------------
# TEST AREA....
## Manual Installation macOS
### Install brew and python3
#### https://docs.python-guide.org/starting/install3/osx/

```
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
brew install python
pip3 install psutil crcengine ujson pyserial numpy

```
### Install protaudio dependencies
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
pip3 install psutil crcengine ujson pyserial numpy
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
