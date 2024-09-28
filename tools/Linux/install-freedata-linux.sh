#!/bin/bash
#
# Simple script to install FreeDATA in Linux
# Dj Merrill - N1JOV
#
# Currently supports Debian [11, 12], Ubuntu [22.04, 24.04]
# 
# Run this script by typing in the terminal (without the quotes):
# "bash install-freedata-linux.sh" to install from the main branch 
# "bash install-freedata-linux.sh develop" to install from the develop branch
#
# This script creates three subdirectories in the directory it is run
# FreeDATA: Contains the FreeDATA software
# FreeDATA-venv: Contains the Python virtual environment
# FreeDATA-hamlib: Contains the hamlib libraries
#
# FreeDATA config file is stored in $HOME/.config/FreeDATA/config.ini
# See the run-freedata-linux.sh for more details
#
#
# Changelog:
# 1.9:	14 Sep 2024 (deej)
# 	Tweak OS version checking section to handle minor OS revisions better

# 1.8:	23 July 2024 ( DJ2LS )
# 	Add support for browser based gui
#
# 1.7:	31 May 2024 ( DJ2LS )
# 	Add support for version specific setup
#
# 1.6:	22 May 2024
#	Reflect directory name changes in prep for merging develop to main
#
# 1.5:	12 May 2024
#	"dr-freedata-001" branch of codec2 merged to main so we don't
#	need to checkout that branch specifically
#
# 1.4:	05 May 2024
#	Change to "dr-freedata-001" branch of codec2 for develop mode
#	Added comments in scripts and README.txt for config file location
#	If hamlib 4.5.5 is already in FreeDATA-hamlib, don't reinstall
#
# 1.3:	02 May 2024
#	Remove dependency on distro supplied hamlib library which can be old
#	Download and install hamlib 4.5.5 into ./FreeDATA-hamlib
#	Add support for Debian 11 and Ubuntu 22.04
#
# 1.2:	30 Apr 2024
#	Remove dependency on distro supplied nodejs which can be too old
#	Install nodejs version 20 into ~/.nvm
#
# 1.1:	26 Apr 2024
#	Add support for installing from FreeDATA develop branch
#	Add support for Ubuntu 24.04
#	
# 1.0:	Initial release 25 Apr 2024 supporting Debian 12
#

case $1 in
   "" | "main")
	args="main"
   ;;
   "develop")
	args="develop"
   ;;
  v*)
  args=$1
  ;;
  *)
	echo "Argument" $1 "not valid.  Exiting."
	exit 1
   ;;
esac

osname=`grep -E '^(NAME)=' /etc/os-release | cut -d\" -f2`
osversion=`grep -E '^(VERSION_ID)=' /etc/os-release | cut -d\" -f2`

echo "Running on" $osname "version" $osversion

echo "*************************************************************************"
echo "Installing software prerequisites"
echo "If prompted, enter your password to run the sudo command"
echo "*************************************************************************"

case $osname in
   "Debian GNU/Linux")
	case $osversion in
	   "11" | "12")
		sudo apt install --upgrade -y fonts-noto-color-emoji git build-essential cmake python3 portaudio19-dev python3-pyaudio python3-pip python3-colorama python3-venv wget
	   ;;

	   *)
	   	echo "*************************************************************************"
	   	echo "This version of Linux is not yet supported by this script."
	   	echo $osname $osversion
	   	echo "*************************************************************************"
		exit 1
	   ;;

	esac

   ;;

   "Ubuntu")
	case $osversion in
	   "22.04" | "24.04")
		sudo apt install --upgrade -y fonts-noto-color-emoji git build-essential cmake python3 portaudio19-dev python3-pyaudio python3-pip python3-colorama python3-venv wget
	   ;;

	   *)
	   	echo "*************************************************************************"
	   	echo "This version of Linux is not yet supported by this script."
	   	echo $osname $osversion
	   	echo "*************************************************************************"
		exit 1
	   ;;
	esac
   ;;

   *)
	echo "*************************************************************************"
	echo "This version of Linux is not yet supported by this script."
	echo $osname $osversion
	echo "*************************************************************************"
	exit 1
   ;;
esac

echo "*************************************************************************"
echo "Installing nvm and node v 20 into ~/.nvm"
echo "*************************************************************************"
wget https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh
if [ -f "install.sh" ];
then
	XDG_CONFIG_HOME=""
	chmod 750 install.sh
	./install.sh
else
	echo "Something went wrong.  nvm install.sh not downloaded."
	exit 1
fi

if [ -f "$HOME/.nvm/bash_completion" ];
then
	export NVM_DIR="$HOME/.nvm"
	[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
	[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
	nvm install 20
	echo "npm is version" `npm -v`
	echo "node is version" `node -v`
	rm -f install.sh
else
	echo "Something went wrong.  $HOME/.nvm environment not created properly."
	exit 1
fi

echo "*************************************************************************"
echo "Checking for hamlib 4.5.5 in FreeDATA-hamlib"
echo "*************************************************************************"

if [ -d "FreeDATA-hamlib.old" ];
then
	rm -rf FreeDATA-hamlib.old
fi

if [ -d "FreeDATA-hamlib" ];
then
	if [ -f "./FreeDATA-hamlib/bin/rigctl" ];
	then
		checkhamlibver=`./FreeDATA-hamlib/bin/rigctl --version | cut -f3 -d" "`
		if [ "$checkhamlibver" != "4.5.5" ];
		then
			mv FreeDATA-hamlib FreeDATA-hamlib.old
		else
			echo "Hamlib 4.5.5 found, no installation needed."
		fi
	else
		mv FreeDATA-hamlib FreeDATA-hamlib.old
	fi
fi

if [ ! -d "FreeDATA-hamlib" ];
then
	echo "Installing hamlib 4.5.5 into FreeDATA-hamlib"
	curdir=`pwd`
	wget https://github.com/Hamlib/Hamlib/releases/download/4.5.5/hamlib-4.5.5.tar.gz
	if [ -f "hamlib-4.5.5.tar.gz" ];
	then
		tar -xplf hamlib-4.5.5.tar.gz
	else
		echo "Something went wrong.  hamlib-4.5.5.tar.gz not downloaded."
		exit 1
	fi
	if [ -d "hamlib-4.5.5" ];
	then
		cd hamlib-4.5.5
		./configure --prefix=$curdir/FreeDATA-hamlib
		make
		make install
		cd ..
	else
		echo "Something went wrong.  hamlib-4.5.5 directory not found."
		exit 1
	fi
	if [ ! -f "$curdir/FreeDATA-hamlib/bin/rigctl" ];
	then
		echo "Something went wrong." $curdir"/FreeDATA.hamlib/bin/rigctl not found."
                exit 1
	else
		echo "Cleaning up files from hamlib build."
		rm -f hamlib-4.5.5.tar.gz
		rm -rf hamlib-4.5.5
        fi
fi

echo "*************************************************************************"
echo "Checking for old FreeDATA directories"
echo "*************************************************************************"
if [ -d "FreeDATA.old" ];
then
	rm -rf FreeDATA.old
fi
if [ -d "FreeDATA-venv.old" ];
then
	rm -rf FreeDATA-venv.old
fi
if [ -d "FreeDATA" ];
then
	mv FreeDATA FreeDATA.old
fi
if [ -d "FreeDATA-venv" ];
then
	mv FreeDATA-venv FreeDATA-venv.old
fi

echo "*************************************************************************"
echo "Creating Python Virtual Environment FreeDATA-venv"
echo "*************************************************************************"
python3 -m venv FreeDATA-venv

echo "*************************************************************************"
echo "Activating the Python Virtual Environment"
echo "*************************************************************************"
if [ -f "./FreeDATA-venv/bin/activate" ];
then
	source ./FreeDATA-venv/bin/activate
else
	echo "Something went wrong.  FreeDATA-venv virtual environment not created properly."
	exit 1
fi

echo "*************************************************************************"
echo "Updating pip and wheel"
echo "*************************************************************************"
pip install --upgrade pip wheel

echo "*************************************************************************"
echo "Downloading the FreeDATA software from the git repo"
echo "*************************************************************************"
if [ "$args" == "develop" ];
then
  echo "Downloading development version"
  git clone https://github.com/DJ2LS/FreeDATA.git -b develop
	git checkout develop
elif [[ $args == v* ]];
then
    echo "Downloading specific version: $args"
    git clone https://github.com/DJ2LS/FreeDATA.git -b $args
else
    echo "Downloading regular version"
  git clone https://github.com/DJ2LS/FreeDATA.git

fi

echo "*************************************************************************"
echo "Changing Directory into FreeDATA"
echo "*************************************************************************"
if [ -d "FreeDATA" ];
then
	cd FreeDATA
else
	echo "Something went wrong.  FreeDATA software not downloaded from git."
	exit 1
fi

echo "*************************************************************************"
echo "Installing required Python programs into the virtual environment"
echo "*************************************************************************"
pip install --upgrade -r requirements.txt

echo "*************************************************************************"
echo "Changing into the server directory"
echo "*************************************************************************"
cd freedata_server/lib

echo "*************************************************************************"
echo "Checking and removing any old codec2 libraries"
echo "*************************************************************************"
if [ -d "codec2" ];
then
	mv codec2 codec2.old
fi

echo "*************************************************************************"
echo "Downloading the latest codec library"
echo "*************************************************************************"
git clone https://github.com/drowe67/codec2.git

echo "*************************************************************************"
echo "Changing into the codec2 library directory"
echo "*************************************************************************"
if [ -d "codec2" ];
then
	cd codec2
else
	echo "Something went wrong.  Codec2 software not downloaded from git."
	exit 1
fi
	
echo "*************************************************************************"
echo "Setting up the codec2 build"
echo "*************************************************************************"
mkdir build_linux
cd build_linux

echo "*************************************************************************"
echo "Building the codec2 library"
echo "*************************************************************************"
cmake ..
make -j4

if [ ! -f "src/libcodec2.so.1.2" ];
then
	echo "Something went wrong.  Codec2 software not built."
	exit 1
fi

echo "*************************************************************************"
echo "Building the FreeDATA GUI frontend"
echo "*************************************************************************"
cd ../../../..
cd freedata_gui
npm i
#npm audit fix --force
#npm i
npm run build

# Return to the directory we started in
cd ../..
