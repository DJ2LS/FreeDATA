#!/bin/bash -x
# Run a test using the virtual sound cards, tx sound I/O performed by aplay
# and arecord at Fs=48000Hz, we pipe to Python utilities

MAX_RUN_TIME=2600

# make sure all child processes are killed when we exit
trap 'jobs -p | xargs -r kill' EXIT

arecord -r 48000 --device="plughw:CARD=CHAT1,DEV=0" -f S16_LE -d $MAX_RUN_TIME | \
    python3 util_rx.py --mode datac13 --frames 2 --bursts 5 --debug &
rx_pid=$!
sleep 1
python3 util_tx.py --mode datac13 --frames 2 --bursts 5 --delay 500 | \
    aplay -r 48000 --device="plughw:CARD=CHAT1,DEV=1" -f S16_LE
wait ${rx_pid}
