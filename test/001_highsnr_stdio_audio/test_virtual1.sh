#!/bin/bash -x
# Run a test using the virtual sound cards, but sound I/O performed by aplay/arecord, and
# we pipe to Python utilities

function check_alsa_loopback {
    lsmod | grep snd_aloop >> /dev/null
    if [ $? -eq 1 ]; then
      echo "ALSA loopback device not present.  Please install with:"
      echo
      echo "  sudo modprobe snd-aloop index=1,2 enable=1,1 pcm_substreams=1,1 id=CHAT1,CHAT2"
      exit 1
    fi  
}

check_alsa_loopback

RX_LOG=$(mktemp)
MAX_RUN_TIME=2600

# make sure all child processes are killed when we exit
trap 'jobs -p | xargs -r kill' EXIT

arecord --device="plughw:CARD=CHAT2,DEV=0" -f S16_LE -d $MAX_RUN_TIME | python3 test_rx.py --mode datac0 --frames 2 --bursts 5 --debug &
rx_pid=$!
sleep 1
python3 test_tx.py --mode datac0 --frames 2 --bursts 5 --delay 500 | aplay --device="plughw:CARD=CHAT2,DEV=1" -f S16_LE
wait ${rx_pid}
