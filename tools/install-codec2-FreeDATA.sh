#/bin/bash

cd ~
rm -rf codec2-FreeDATA
git clone https://github.com/DJ2LS/codec2-FreeDATA.git

cd ~/codec2-FreeDATA/tnc
rm -rf codec2
git clone https://github.com/drowe67/codec2.git
cd codec2 && mkdir build_linux && cd build_linux
cmake ../
make

cd ~/codec2-FreeDATA/gui
npm i
