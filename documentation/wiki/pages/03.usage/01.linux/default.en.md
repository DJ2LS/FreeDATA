---
title: Linux
---

!!! Tested with Ubuntu 20.04 LTS

## 1. Starting the TNC daemon
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


## 2. Starting the GUI
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
