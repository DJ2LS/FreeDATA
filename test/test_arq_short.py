#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

import sys

import codec2
import data_handler
import modem
import pytest
import static

bytes_out = b'{"dt":"f","fn":"zeit.txt","ft":"text\\/plain","d":"data:text\\/plain;base64,MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=","crc":"123123123"}'


@pytest.mark.parametrize("freedv_mode", ["datac0", "datac1", "datac3"])
@pytest.mark.parametrize("n_frames_per_burst", [1, 2, 3])
def test_highsnr_arq_short(freedv_mode: str, n_frames_per_burst: int):
    t_mode = t_repeats = t_repeat_delay = 0
    t_frames = []

    def t_tx_dummy(mode, repeats, repeat_delay, frames):
        """Replacement function for transmit"""
        print(f"t_tx_dummy: In transmit({mode}, {repeats}, {repeat_delay}, {frames})")
        nonlocal t_mode, t_repeats, t_repeat_delay, t_frames
        t_mode = mode
        t_repeats = repeats
        t_repeat_delay = repeat_delay
        t_frames = frames[:]
        static.TRANSMITTING = False

    # enable testmode
    modem.TESTMODE = True
    modem.RXCHANNEL = "/tmp/rxpipe"
    modem.TXCHANNEL = "/tmp/txpipe"
    data_handler.TESTMODE = True
    static.HAMLIB_RADIOCONTROL = "disabled"

    # start data handler
    data_handler.DATA()

    # start modem
    t_modem = modem.RF()

    # Replace transmit routine with our own, an effective No-Op.
    t_modem.transmit = t_tx_dummy

    mode = codec2.freedv_get_mode_value_by_name(freedv_mode)
    print(mode)

    # add command to data qeue
    data_handler.DATA_QUEUE_TRANSMIT.put(
        ["ARQ_FILE", bytes_out, mode, n_frames_per_burst]
    )


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-v", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
