#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

import sys
sys.path.insert(0,'..')
sys.path.insert(0,'../tnc')
import data_handler


teststring = b'HELLO WORLD'

data_handler.arq_transmit(teststring, 10, 1)





