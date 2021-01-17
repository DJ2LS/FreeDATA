#/bin/bash

cd ~
rm -rf FreeDV-JATE
git clone --branch dev https://github.com/DJ2LS/FreeDV-JATE.git


cd ~/FreeDV-JATE
rm -rf codec2
git clone https://github.com/drowe67/codec2.git
cd codec2 && mkdir build_linux && cd build_linux
cmake ../
make


cd ~/FreeDV-JATE
rm -rf LPCNet
git clone https://github.com/drowe67/LPCNet
cd LPCNet && mkdir build_linux && cd build_linux
cmake -DCODEC2_BUILD_DIR=~/FreeDV-JATE/codec2/build_linux ../ 
make


cd ~/FreeDV-JATE/codec2/build_linux && rm -Rf *
cmake -DLPCNET_BUILD_DIR=~/FreeDV-JATE/LPCNet/build_linux ..
make
