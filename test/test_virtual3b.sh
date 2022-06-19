#!/bin/bash -x
# Run a test using the virtual sound cards, Python audio I/O

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

# make sure all child processes are killed when we exit
trap 'jobs -p | xargs -r kill' EXIT

python3 util_callback_rx_outside.py --mode datac0 --frames 2 --bursts 3 --audiodev -2 --debug &
rx_pid=$!
#sleep 1
python3 util_tx.py --mode datac0 --frames 2 --bursts 3 --audiodev -2
wait ${rx_pid}
