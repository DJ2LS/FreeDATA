#!/bin/bash
#
# Simple script to install FreeDATA in Linux
# Dj Merrill - 25 Apr 2024
#
# Currently supports Debian [11,12], Ubuntu [24.04]
# 
# args: nothing or "main" (use main branch of FreeDATA)
# 	"develop" (use develop branch of FreeDATA)
#

case $1 in
   "" | "main")
	args="main"
   ;;
   "develop")
	args="develop"
   ;;
   *)
	echo "Argument" $1 "not valid.  Exiting."
	exit 1
   ;;
esac

osname=`grep -E '^(NAME)=' /etc/os-release | cut -d\" -f2`
osversion=`grep -E '^(VERSION)=' /etc/os-release | cut -d\" -f2`

echo "Running on" $osname "version" $osversion

echo "*************************************************************************"
echo "Installing software prerequisites"
echo "*************************************************************************"

case $osname in
   "Debian GNU/Linux")
	case $osversion in
	   "11 (bullseye)" | "12 (bookworm)")
		sudo apt install --upgrade -y libhamlib-utils libhamlib-dev libhamlib4 fonts-noto-color-emoji git build-essential cmake python3 portaudio19-dev python3-pyaudio python3-pip python3-colorama python3-venv wget
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
	   "24.04 LTS (Noble Numbat)")
		sudo apt install --upgrade -y libhamlib-utils libhamlib-dev libhamlib4 fonts-noto-color-emoji git build-essential cmake python3 portaudio19-dev python3-pyaudio python3-pip python3-colorama python3-venv curl wget
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
	echo "Something went wrong.  npm install.sh not downloaded."
	exit 1
fi

if [ -f "$HOME/.nvm/bash_completion" ];
then
	export NVM_DIR="$HOME/.nvm"
	[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
	[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
	nvm install 20
	echo "nvm is version" `npm -v`
	echo "node is version" `node -v`
	rm install.sh
else
	echo "Something went wrong.  $HOME/.nvm environment not created properly."
	exit 1
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
git clone https://github.com/DJ2LS/FreeDATA.git

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

if [ "$args" == "develop" ];
then
	git checkout develop
fi

echo "*************************************************************************"
echo "Installing required Python programs into the virtual environment"
echo "*************************************************************************"
pip install --upgrade -r requirements.txt

echo "*************************************************************************"
echo "Changing into the server directory"
echo "*************************************************************************"
if [ "$args" == "develop" ];
then
	cd freedata_server/lib
else
	cd modem/lib
fi

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
	
if [ "$args" == "develop" ];
then
	git checkout dr-qam16-cport
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
if [ "$args" == "develop" ];
then
	cd freedata_gui
else
	cd gui
fi
npm i
npm audit fix --force
npm i

# Return to the directory we started in
cd ../..
