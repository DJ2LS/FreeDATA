@echo off
REM This will copy the helper batch files to the approriate places for you

echo Copying GUI scripts to GUI directory
copy GUI* ..\..\freedata_gui\

echo Copying Modem scripts to Modem directory
copy MODEM* ..\..\freedata_server\

pause