# codec2 | FreeDATA
My attempt to create a free and opensource TNC with a GUI for [codec2](https://github.com/drowe67/codec2) to send data over HF channels. 
The TNC itself will be completely controllable via network.

## Under development
The project is still a prototype and not usable at this time.

## Manual Installation Ubuntu
```
wget https://raw.githubusercontent.com/DJ2LS/codec2-FreeDATA/main/tools/install-codec2-FreeDATA.sh
chmod +x install-codec2-FreeDATA.sh
./install-codec2-FreeDATA.sh
sudo apt install npm
cd gui
npm i
sudo apt install python3
pip3 install psutil
pip3 install crcengine
pip3 install ujson
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
```
### Install dependencies
```
xcode-select --install
brew remove portaudio
brew install portaudio
pip3 install pyaudio
```






## GUI Preview
![alt text](https://github.com/DJ2LS/FreeDATA/blob/main/documentation/FreeDATA_GUI_Preview.png "GUI Preview")

## TNC Preview
![alt text](https://github.com/DJ2LS/FreeDATA/blob/main/documentation/FreeDATA_TNC_Preview.png "TNC Preview")

## Credits
David Rowe and the FreeDV team for developing the modem and libraries
FreeDV Codec 2 : https://github.com/drowe67/codec2
