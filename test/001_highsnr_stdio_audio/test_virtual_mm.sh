#!/bin/bash -x
# Run a test using the virtual sound cards

function check_alsa_loopback {
    lsmod | grep snd_aloop >> /dev/null
    if [ $? -eq 1 ]; then
      echo "ALSA loopback device not present.  Please install with:"
      echo
      echo "  sudo modprobe snd-aloop index=1,2 enable=1,1 pcm_substreams=1,1 id=CHAT1,CHAT2"
      exit 1
    fi  
}

myInterruptHandler()
{
    exit 1
}

check_alsa_loopback

RX_LOG=$(mktemp)

trap myInterruptHandler SIGINT

# make sure all child processes are killed when we exit
trap 'jobs -p | xargs -r kill' EXIT

python3 test_multimode_rx.py --timeout 60 --framesperburst 2 --bursts 2 --audiodev -2 &
rx_pid=$!
sleep 1
python3 test_multimode_tx.py --framesperburst 2 --bursts 2 --audiodev -2 --delay 500
wait ${rx_pid}
