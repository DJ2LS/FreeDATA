#!/bin/bash
#
# Simple script to run FreeDATA in Linux
# Dj Merrill - N1JOV
#
# Run this script in the directory that contains the "FreeDATA", 
# "FreeDATA-venv", and "FreeDATA-hamlib" directories 
# created by the install-freedata-linux.sh script
#
# Two log files are created in this directory:
# FreeDATA-server.log: debug output from the server process
# FreeDATA-client.log: debug output from the GUI front end
# To view live, "tail -f FreeDATA-server.log" or "tail -f FreeDATA-client.log"
#
# We expect the config.ini file to be at $HOME/.config/FreeDATA/config.ini
# If it isn't found, we copy config.ini.example there
#
# 1.7:  22 May 2024
#	Slightly change the way we shutdown the server
# 1.6:  05 May 2024
#	Don't stop rigctld if it was started separate from FreeDATA
#	We only want to clean up FreeDATA initiated processes
# 1.5:  05 May 2024
#	Check for rigctld at exit and stop it if needed
# 1.4:  05 May 2024
#	Added comments on how to view log outputs in realtime
# 1.3:  02 May 2024
#	Add support for hamlib installed by FreeDATA install script
# 1.2:  30 Apr 2024
# 1.1:  26 Apr 2024
# 1.0:	25 Apr 2024 Initial release
#

# Set path to find our hamlib install
export PATH=./FreeDATA-hamlib/bin:$PATH
export LD_LIBRARY_PATH=./FreeDATA-hamlib/lib:$LD_LIBRARY_PATH

if [ ! -f "FreeDATA-hamlib/bin/rigctl" ];
then
	echo "Something went wrong.  FreeDATA-hamlib/bin/rigctl not found."
	exit 1
fi

# Activate the Python Virtual Environment
source ./FreeDATA-venv/bin/activate

# Check to see if there is an old server running, and stop it if there is
checkoldserver=`ps auxw | grep FreeDATA | grep server.py`

if [ ! -z "$checkoldserver" ];
then
	oldserverpid=`echo $checkoldserver | cut -d" " -f2`
	echo "*************************************************************************"
	echo "Found old FreeDATA server at PID" $oldserverpid "- stopping it"
	echo "*************************************************************************"
	kill $oldserverpid
	sleep 7s
fi

# Check for an already running rigctld process
# This was probably started by other means so we should leave this 
# alone when we exit
checkrigexist=`ps auxw | grep -i rigctld | grep -v grep`

echo "*************************************************************************"
echo "Running the FreeDATA server component"
echo "*************************************************************************"

# New versions use freedata_server, old version use modem
if [ -d "FreeDATA/freedata_server" ];
then
	serverdir="FreeDATA/freedata_server"
else
	serverdir="FreeDATA/modem"
fi

if [ ! -d "$HOME/.config/FreeDATA" ];
then
	mkdir -p $HOME/.config/FreeDATA
fi
if [ ! -f "$HOME/.config/FreeDATA/config.ini" ];
then
	echo "*************************************************************************"
	echo "No config file found.  Copying example config file to"
	echo $HOME/.config/FreeDATA/config.ini
	echo "*************************************************************************"
	cp $serverdir/config.ini.example $HOME/.config/FreeDATA/config.ini
fi

FREEDATA_CONFIG=$HOME/.config/FreeDATA/config.ini python3 $serverdir/server.py > FreeDATA-server.log 2>&1 &
serverpid=$!
echo "Process ID of FreeDATA server is" $serverpid

# Run the GUI front end
echo "*************************************************************************"
echo "Running the FreeDATA GUI front end"
echo "*************************************************************************"

# New versions use "freedata_gui", old versions use "gui"
if [ -d "FreeDATA/freedata_gui" ];
then
	guidir="FreeDATA/freedata_gui"
else
	guidir="FreeDATA/gui"
fi

cd $guidir

if [ -f "$HOME/.nvm/bash_completion" ];
then
	export NVM_DIR="$HOME/.nvm"
	[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
	[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
else
	echo "Something went wrong.  $HOME/.nvm environment not created properly."
	exit 1
fi

checknpm=`which npm`
if [ -z "$checknpm" ];
then
	echo "Something went wrong.  npm not found."
	exit 1
fi

npm start > ../../FreeDATA-client.log 2>&1

# If we are this far, then we have just quit the GUI, so let's clean up the
# server
echo "*************************************************************************"
echo "Stopping the server component"
echo "*************************************************************************"
kill -INT $serverpid

# Give time for the server to clean up rigctld if needed
sleep 5s

# If rigctld was already running before starting FreeDATA, leave it alone
# otherwise we should clean it up
if [ -z "$checkrigexist" ];
then
	# rigctld was started by FreeDATA and should have stopped when the 
	# server exited.  If it didn't, stop it now.
	checkrigctld=`ps auxw | grep -i rigctld | grep -v grep`
	if [ ! -z "$checkrigctld" ];
	then
		echo "*************************************************************************"
		echo "Stopping rigctld"
		echo "*************************************************************************"
		rigpid=`echo $checkrigctld | cut -f2 -d" "`
		kill $rigpid
	fi
fi

# Return to the directory we started in
cd ..
