#!/bin/bash -x
# Run a test using the virtual sound cards, tx sound I/O performed by aplay,
# rx sound I/O by Python, Fs=48000Hz.

MAX_RUN_TIME=2600

# make sure all child processes are killed when we exit
trap 'jobs -p | xargs -r kill' EXIT

python3 test_rx.py --mode datac0 --frames 2 --bursts 5 --debug --audiodev -2 &
rx_pid=$!
sleep 1
python3 test_tx.py --mode datac0 --frames 2 --bursts 5 | \
    aplay -r 48000 --device="plughw:CARD=CHAT1,DEV=1" -f S16_LE
wait ${rx_pid}
