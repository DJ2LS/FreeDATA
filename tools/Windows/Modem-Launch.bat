REM Place this batch file in FreeData/freedata_server and then run it
REM ie. c:\FD-Src\freedata_server

REM Set environment variable to let modem know where to find config, change if you need to specify a different config
set FREEDATA_CONFIG=.\config.ini 

REM launch freedata_server
python server.py

pause
