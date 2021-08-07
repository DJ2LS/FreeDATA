#/bin/bash

cd ~
rm -rf codec2-FreeDATA
#git clone --branch master https://github.com/DJ2LS/codec2-FreeDATA.git
git clone https://github.com/DJ2LS/codec2-FreeDATA.git

cd ~/codec2-FreeDATA/tnc
rm -rf codec2
git clone https://github.com/drowe67/codec2.git
cd codec2 && mkdir build_linux && cd build_linux
cmake ../
make


cd ~/codec2-FreeDATA/tnc
rm -rf LPCNet
git clone https://github.com/drowe67/LPCNet
cd LPCNet && mkdir build_linux && cd build_linux
cmake -DCODEC2_BUILD_DIR=~/codec2-FreeDATA/tnc/codec2/build_linux ../ 
make


cd ~/codec2-FreeDATA/codec2/build_linux && rm -Rf *
cmake -DLPCNET_BUILD_DIR=~/codec2-FreeDATA/tnc/LPCNet/build_linux ..
make
