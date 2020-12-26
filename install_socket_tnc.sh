#/bin/bash

cd ~
rm -rf FreeDV-Socket-TNC
git clone --branch dev https://github.com/DJ2LS/FreeDV-Socket-TNC.git


cd ~/FreeDV-Socket-TNC
rm -rf codec2
git clone https://github.com/drowe67/codec2.git
cd codec2 && mkdir build_linux && cd build_linux
cmake ../
make


cd ~/FreeDV-Socket-TNC
rm -rf LPCNet
git clone https://github.com/drowe67/LPCNet
cd LPCNet && mkdir build_linux && cd build_linux
cmake -DCODEC2_BUILD_DIR=~/FreeDV-Socket-TNC/codec2/build_linux ../ 
make


cd ~/FreeDV-Socket-TNC/codec2/build_linux && rm -Rf *
cmake -DLPCNET_BUILD_DIR=~/FreeDV-Socket-TNC/LPCNet/build_linux ..
make
