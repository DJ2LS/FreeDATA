#!/usr/bin/env python3

import sys
import re
import structlog
import atexit
import subprocess
import os

# set global hamlib version
hamlib_version = 0

# append local search path
# check if we are running in a pyinstaller environment
if hasattr(sys, "_MEIPASS"):
    sys.path.append(getattr(sys, "_MEIPASS"))
else:
    sys.path.append(os.path.abspath("."))

# try importing hamlib
try:
    # get python version
    python_version = f"{str(sys.version_info[0])}.{str(sys.version_info[1])}"

    # installation path for Ubuntu 20.04 LTS python modules
    # sys.path.append('/usr/local/lib/python'+ python_version +'/site-packages')

    # installation path for Ubuntu 20.10 +
    sys.path.append('/usr/local/lib/')

    # installation path for Suse
    sys.path.append(f'/usr/local/lib64/python{python_version}/site-packages')

    # everything else... not nice, but an attempt to see how its running within app bundle
    # this is not needed as python will be shipped with app bundle
    sys.path.append('/usr/local/lib/python3.6/site-packages')
    sys.path.append('/usr/local/lib/python3.7/site-packages')
    sys.path.append('/usr/local/lib/python3.8/site-packages')
    sys.path.append('/usr/local/lib/python3.9/site-packages')
    sys.path.append('/usr/local/lib/python3.10/site-packages')

    sys.path.append('lib/hamlib/linux/python3.8/site-packages')
    import Hamlib

    # https://stackoverflow.com/a/4703409
    hamlib_version = re.findall(r"[-+]?\d*\.?\d+|\d+", Hamlib.cvar.hamlib_version)
    hamlib_version = float(hamlib_version[0])

    min_hamlib_version = 4.1
    if hamlib_version > min_hamlib_version:
        structlog.get_logger("structlog").info("[RIG] Hamlib found", version=hamlib_version)
    else:
        structlog.get_logger("structlog").warning("[RIG] Hamlib outdated", found=hamlib_version, recommend=min_hamlib_version)
except Exception as e:
    structlog.get_logger("structlog").warning("[RIG] Python Hamlib binding not found", error=e)

    try:
        structlog.get_logger("structlog").warning("[RIG] Trying to open rigctl")
        rigctl = subprocess.Popen("rigctl -V", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

        hamlib_version = rigctl.stdout.readline()
        hamlib_version = hamlib_version.split(' ')
        if hamlib_version[1] != 'Hamlib':
            raise Exception from e
        structlog.get_logger("structlog").warning("[RIG] Rigctl found! Please try using this", version=hamlib_version[2])

        sys.exit()
    except Exception as e:
        structlog.get_logger("structlog").critical("[RIG] HAMLIB NOT INSTALLED", error=e)

        hamlib_version = 0
        sys.exit()


class radio:
    """ """
    def __init__(self):
        self.devicename = ''
        self.devicenumber = ''
        self.deviceport = ''
        self.serialspeed = ''
        self.hamlib_ptt_type = ''
        self.my_rig = ''
        self.pttport = ''
        self.data_bits = ''
        self.stop_bits = ''
        self.handshake = ''

    def open_rig(self, devicename, deviceport, hamlib_ptt_type, serialspeed, pttport, data_bits, stop_bits, handshake, rigctld_port, rigctld_ip):
        """

        Args:
          devicename:
          deviceport:
          hamlib_ptt_type:
          serialspeed:
          pttport:
          data_bits:
          stop_bits:
          handshake:
          rigctld_port:
          rigctld_ip:

        Returns:

        """
        self.devicename = devicename
        self.deviceport = str(deviceport)
        self.serialspeed = str(serialspeed) # we need to ensure this is a str, otherwise set_conf functions are crashing
        self.hamlib_ptt_type = str(hamlib_ptt_type)
        self.pttport = str(pttport)
        self.data_bits = str(data_bits)
        self.stop_bits = str(stop_bits)
        self.handshake = str(handshake)

        # try to init hamlib
        try:
            Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)

            # get devicenumber by looking for deviceobject in Hamlib module
            try:
                self.devicenumber = int(getattr(Hamlib, self.devicename))
            except Exception:
                structlog.get_logger("structlog").error("[RIG] Hamlib: rig not supported...")
                self.devicenumber = 0

            self.my_rig = Hamlib.Rig(self.devicenumber)
            self.my_rig.set_conf("rig_pathname", self.deviceport)
            self.my_rig.set_conf("retry", "5")
            self.my_rig.set_conf("serial_speed", self.serialspeed)
            self.my_rig.set_conf("serial_handshake", self.handshake)
            self.my_rig.set_conf("stop_bits", self.stop_bits)
            self.my_rig.set_conf("data_bits", self.data_bits)
            self.my_rig.set_conf("ptt_pathname", self.pttport)

            if self.hamlib_ptt_type == 'RIG':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_RIG
                self.my_rig.set_conf("ptt_type", 'RIG')

            elif self.hamlib_ptt_type == 'USB':
                self.hamlib_ptt_type = Hamlib.RIG_PORT_USB
                self.my_rig.set_conf("ptt_type", 'USB')

            elif self.hamlib_ptt_type == 'DTR-H':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_SERIAL_DTR
                self.my_rig.set_conf("dtr_state", "HIGH")
                self.my_rig.set_conf("ptt_type", "DTR")

            elif self.hamlib_ptt_type == 'DTR-L':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_SERIAL_DTR
                self.my_rig.set_conf("dtr_state", "LOW")
                self.my_rig.set_conf("ptt_type", "DTR")

            elif self.hamlib_ptt_type == 'RTS':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_SERIAL_RTS
                self.my_rig.set_conf("dtr_state", "OFF")
                self.my_rig.set_conf("ptt_type", "RTS")

            elif self.hamlib_ptt_type == 'PARALLEL':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_PARALLEL

            elif self.hamlib_ptt_type == 'MICDATA':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_RIG_MICDATA

            elif self.hamlib_ptt_type == 'CM108':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_CM108

            elif self.hamlib_ptt_type == 'RIG_PTT_NONE':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_NONE

            else:  # self.hamlib_ptt_type == 'RIG_PTT_NONE':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_NONE

            structlog.get_logger("structlog").info("[RIG] Opening...", device=self.devicenumber, path=self.my_rig.get_conf("rig_pathname"), serial_speed=self.my_rig.get_conf("serial_speed"), serial_handshake=self.my_rig.get_conf("serial_handshake"), stop_bits=self.my_rig.get_conf("stop_bits"), data_bits=self.my_rig.get_conf("data_bits"), ptt_pathname=self.my_rig.get_conf("ptt_pathname"))

            self.my_rig.open()
            atexit.register(self.my_rig.close)

            try:
                # lets determine the error message when opening rig
                error = str(Hamlib.rigerror(my_rig.error_status)).splitlines()
                error = error[1].split('err=')
                error = error[1]

                if error == 'Permission denied':
                    structlog.get_logger("structlog").error("[RIG] Hamlib has no permissions", e = error)
                    help_url = 'https://github.com/DJ2LS/FreeDATA/wiki/UBUNTU-Manual-installation#1-permissions'
                    structlog.get_logger("structlog").error("[RIG] HELP:", check = help_url)
            except Exception:
                structlog.get_logger("structlog").info("[RIG] Hamlib device opened", status='SUCCESS')

            # set ptt to false if ptt is stuck for some reason
            self.set_ptt(False)

            # set rig mode to USB
            # temporarly outcommented because of possible problems.
            # self.my_rig.set_mode(Hamlib.RIG_MODE_USB)
            # self.my_rig.set_mode(Hamlib.RIG_MODE_PKTUSB)
            return True

        except Exception as e:
            structlog.get_logger("structlog").error("[RIG] Hamlib - can't open rig", error=e, e=sys.exc_info()[0])
            return False

    def get_frequency(self):
        """ """
        return int(self.my_rig.get_freq())

    def get_mode(self):
        """ """
        (hamlib_mode, bandwith) = self.my_rig.get_mode()
        return Hamlib.rig_strrmode(hamlib_mode)

    def get_bandwith(self):
        """ """
        (hamlib_mode, bandwith) = self.my_rig.get_mode()
        return bandwith

    # not needed yet beacuse of some possible problems
    # def set_mode(self, mode):
    #    return 0

    def get_ptt(self):
        """ """
        return self.my_rig.get_ptt()

    def set_ptt(self, state):
        """

        Args:
          state:

        Returns:

        """
        if state:
            self.my_rig.set_ptt(Hamlib.RIG_VFO_CURR, 1)
        else:
            self.my_rig.set_ptt(Hamlib.RIG_VFO_CURR, 0)
        return state

    def close_rig(self):
        """ """
        self.my_rig.close()
