#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import static
import modem
#modem = modem.RF()
import helpers



def transmit_cq():
    cq_frame = b'CQCQCQ'
    modem.RF.transmit_signalling(cq_frame)
    pass
    

