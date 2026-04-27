#!/bin/bash
#
# Simple script to install and also update FreeDATA in Linux
# To update FreeDATA, simply re-run the script in the same location
#
# Please note this script is not meant to cover all possible installations
# but hopefully can be used as a guide if you are installing on other 
# flavours of Linux
#
# Currently tested in Debian [11, 12], Ubuntu [22.04, 24.04], Fedora [40,41]
# Untested additions for Linux Mint [21.3]
# 
# First option passed is the branch of FreeDATA to run.  Defaults to main.
# Second option passed is the version of Hamlib to use.  Defaults to 4.6.5.
#
# Run this script by typing in the terminal (without the quotes):
# "bash install-freedata-linux.sh (FreeDATA-branch) (hamlib-version)"
#
# Examples:
#
# Install FreeDATA main branch and default Hamlib version:
# "bash install-freedata-linux.sh"
#
# Install FreeDATA develop branch and default Hamlib version:
# "bash install-freedata-linux.sh develop"
#
# Install FreeDATA develop branch and Hamlib version 4.6.2:
# "bash install-freedata-linux.sh develop 4.6.2"
#
# Install FreeDATA main branch and Hamlib version 4.6.2:
# "bash install-freedata-linux.sh main 4.6.2"
#
# This script creates three subdirectories in the directory it is run
# FreeDATA: Contains the FreeDATA software
# FreeDATA-venv: Contains the Python virtual environment
# FreeDATA-hamlib: Contains the hamlib libraries
#
# It also installs nvm and node into $HOME/.nvm
#
# FreeDATA config file is stored in $HOME/.config/FreeDATA/config.ini
# See the run-freedata-linux.sh for more details
#
# Dj Merrill - N1JOV
#
#
# Changelog:
# 2.9:	10 Jan Sep 2026
#	Add Ubuntu 24.10 and 25.04
#	Change hamlib default version to 4.6.5
#	Add pyproject.toml support
#
# 2.8:	16 Sep 2025
#	Add initial support for Debian 13
#
# 2.7:	14 Sep 2025 (deej)
#	Add comment that this script will also update FreeDATA
#
# 2.6:	02 May 2025 (deej)
# 	Allow any Hamlib released version as a second command line argument.
#	Note this requires specifying the FreeDATA branch as the
#	first argument
#
# 2.5:	29 Apr 2025 (deej)
# 	Allow any FreeDATA branch
#
# 2.4:	26 Apr 2025 (petrkr)
# 	Add python3-dev package for debian based distros. Fixes build PyAudio
#
# 2.3:	01 Feb 2025 (deej)
# 	Add untested additions for Linux Mint 21.3
#
# 2.2:	01 Feb 2025 (deej)
# 	Check if account is in the dialout group
#	Add a warning about account needing to be in sudoers
#
# 2.1:	01 Feb 2025 (deej)
# 	Add support for Fedora 41
#
# 2.0:	04 Oct 2024 (deej)
# 	Add support for Fedora 40
#
# 1.9:	14 Sep 2024 (deej)
# 	Tweak OS version checking section to handle minor OS revisions better
#
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

# Account needs to be in the dialout group for some radios to work
checkdial=`grep -i $USER /etc/group | grep -i dialout`

if [ -z "$checkdial" ];
then
	echo "Please add your account" $USER "to the dialout group in /etc/group and then re-run this script."
	exit 1;
fi

case $1 in
   "" | "main")
	branch="main"
   ;;
   *)
   branch=$1
   ;;
esac

if [ ! -z "$2" ];
then
	hamlibver=$2
else
	hamlibver="4.6.5"
fi

osname=`grep -E '^(NAME)=' /etc/os-release | cut -d\" -f2`
osversion=`grep -E '^(VERSION_ID)=' /etc/os-release | cut -d\" -f2`

echo ""
echo "Running on" $osname "version" $osversion
echo "Installing FreeDATA from branch" $branch "with Hamlib version" $hamlibver
echo ""

echo "*************************************************************************"
echo "*************************************************************************"
echo "Installing software prerequisites"
echo "If prompted, enter your password to run the sudo command"
echo ""
echo "If the sudo command gives an error saying Sorry, or not in sudoers file,"
echo "or something to that effect, check to make sure your account has sudo"
echo "privileges.  This generally means a listing in /etc/sudoers or in a file"
echo "in the directory /etc/sudoers.d"
echo "*************************************************************************"

case $osname in
   "Debian GNU/Linux")
	case $osversion in
	   "11" | "12" | "13")
		sudo apt install --upgrade -y fonts-noto-color-emoji git build-essential cmake python3 portaudio19-dev python3-pyaudio python3-pip python3-colorama python3-venv wget python3-dev
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

   "Ubuntu" | "Linux Mint")
	case $osversion in
	   "21.3" | "22.04" | "24.04" | "24.10" | "25.04" )
		sudo apt install --upgrade -y fonts-noto-color-emoji git build-essential cmake python3 portaudio19-dev python3-pyaudio python3-pip python3-colorama python3-venv wget python3-dev
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
   "Fedora Linux")
	case $osversion in
	   "VERSION_ID=40" | "VERSION_ID=41")
		sudo dnf install -y git cmake make automake gcc gcc-c++ kernel-devel wget portaudio-devel python3-pyaudio python3-pip python3-colorama python3-virtualenv google-noto-emoji-fonts python3-devel
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
echo "Checking for hamlib" $hamlibver "FreeDATA-hamlib"
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
		if [ "$checkhamlibver" != "$hamlibver" ];
		then
			mv FreeDATA-hamlib FreeDATA-hamlib.old
		else
			echo "Hamlib" $hamlibver "found, no installation needed."
		fi
	else
		mv FreeDATA-hamlib FreeDATA-hamlib.old
	fi
fi

if [ ! -d "FreeDATA-hamlib" ];
then
	echo "Installing hamlib" $hamlibver "into FreeDATA-hamlib"
	curdir=`pwd`
	wget https://github.com/Hamlib/Hamlib/releases/download/$hamlibver/hamlib-$hamlibver.tar.gz
	if [ -f "hamlib-$hamlibver.tar.gz" ];
	then
		tar -xplf hamlib-$hamlibver.tar.gz
	else
		echo "Something went wrong.  hamlib-"$hamlibver".tar.gz not downloaded."
		exit 1
	fi
	if [ -d "hamlib-$hamlibver" ];
	then
		cd hamlib-$hamlibver
		./configure --prefix=$curdir/FreeDATA-hamlib
		make
		make install
		cd ..
	else
		echo "Something went wrong.  hamlib-"$hamlibver" directory not found."
		exit 1
	fi
	if [ ! -f "$curdir/FreeDATA-hamlib/bin/rigctl" ];
	then
		echo "Something went wrong." $curdir"/FreeDATA.hamlib/bin/rigctl not found."
                exit 1
	else
		echo "Cleaning up files from hamlib build."
		rm -f hamlib-$hamlibver.tar.gz
		rm -rf hamlib-$hamlibver
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
if [ "$branch" == "develop" ];
then
  echo "Downloading development version"
  git clone https://github.com/DJ2LS/FreeDATA.git -b develop
else 
    echo "Downloading specific version: $branch"
    git clone https://github.com/DJ2LS/FreeDATA.git -b $branch
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
python -m pip install .

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
