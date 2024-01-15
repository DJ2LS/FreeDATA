@echo off
REM This will copy the helper batch files to the approriate places for you

echo Copying GUI scripts to GUI directory
copy GUI* ..\..\gui\

echo Copying Modem scripts to Modem directory
copy MODEM* ..\..\modem\

pause