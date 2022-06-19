#!/bin/bash -x
# Run a test using the virtual sound cards, tx sound I/O performed by Python,
# rx using arecord, Fs=48000Hz

MAX_RUN_TIME=2600

# make sure all child processes are killed when we exit
trap 'jobs -p | xargs -r kill' EXIT

arecord -r 48000 --device="plughw:CARD=CHAT1,DEV=0" -f S16_LE -d $MAX_RUN_TIME | \
    python3 util_rx.py --mode datac0 --frames 2 --bursts 5 --debug --timeout 20 &
rx_pid=$!
sleep 1
python3 util_tx.py --mode datac0 --frames 2 --bursts 5 --delay 2000 --audiodev -2
wait ${rx_pid}
