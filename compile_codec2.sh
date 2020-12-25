#/bin/bash

cd ~
rm -rf codec2
git clone https://github.com/drowe67/codec2.git
cd codec2 && mkdir build_linux && cd build_linux
cmake ../
make


cd ~
rm -rf LPCNet
git clone https://github.com/drowe67/LPCNet
cd LPCNet && mkdir build_linux && cd build_linux
cmake -DCODEC2_BUILD_DIR=~/codec2/build_linux ../ 
make

cd ~/codec2/build_linux && rm -Rf *
cmake -DLPCNET_BUILD_DIR=~/LPCNet/build_linux ..
make
