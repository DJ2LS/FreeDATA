# -*- coding: UTF-8 -*-
"""
Created on Sun Dec 27 20:43:40 2020

@author: DJ2LS
"""
# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init
# pylint: disable=fixme


import threading
import helpers
import structlog
from modem_frametypes import FRAME_TYPE as FR_TYPE
import event_manager



TESTMODE = False


class DATA:
    """Terminal Node Controller for FreeDATA"""

    log = structlog.get_logger("DATA")

    def __init__(self, config, event_queue, states):

        self.config = config
        self.event_queue = event_queue
        self.states = states



