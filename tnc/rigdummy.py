#!/usr/bin/env python3

import structlog

hamlib_version = 0


class radio:
    """ """

    def __init__(self):
        pass

    def open_rig(self, **kwargs):
        """

        Args:
          **kwargs:

        Returns:

        """
        return True

    def get_frequency(self):
        """ """
        return None

    def get_mode(self):
        """ """
        return None

    def get_bandwith(self):
        """ """
        return None

    def set_mode(self, mode):
        """

        Args:
          mode:

        Returns:

        """
        return None

    def get_ptt(self):
        """ """
        return None

    def set_ptt(self, state):
        """

        Args:
          state:

        Returns:

        """
        return state

    def close_rig(self):
        """ """
        return
