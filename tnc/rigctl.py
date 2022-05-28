# Intially created by Franco Spinelli, IW2DHW, 01/2022
# Updated by DJ2LS
#
# versione mia di rig.py per gestire Ft897D tramite rigctl e senza
# fare alcun riferimento alla configurazione
#
# e' una pezza clamorosa ma serve per poter provare on-air il modem
#
import os
import subprocess
import sys
import time

import structlog

# for rig_model -> rig_number only

# set global hamlib version
hamlib_version = 0


class radio:
    """ """

    log = structlog.get_logger(__name__)

    def __init__(self):
        self.devicename = ""
        self.devicenumber = ""
        self.deviceport = ""
        self.serialspeed = ""
        self.hamlib_ptt_type = ""
        self.my_rig = ""
        self.pttport = ""
        self.data_bits = ""
        self.stop_bits = ""
        self.handshake = ""
        self.cmd = ""

    def open_rig(
        self,
        devicename,
        deviceport,
        hamlib_ptt_type,
        serialspeed,
        pttport,
        data_bits,
        stop_bits,
        handshake,
        rigctld_ip,
        rigctld_port,
    ):
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
          rigctld_ip:
          rigctld_port:

        Returns:

        """
        self.devicename = devicename
        self.deviceport = deviceport
        # we need to ensure this is a str, otherwise set_conf functions are crashing
        self.serialspeed = str(serialspeed)
        self.hamlib_ptt_type = hamlib_ptt_type
        self.pttport = pttport
        self.data_bits = data_bits
        self.stop_bits = stop_bits
        self.handshake = handshake

        # check if we are running in a pyinstaller environment
        if hasattr(sys, "_MEIPASS"):
            sys.path.append(getattr(sys, "_MEIPASS"))
        else:
            sys.path.append(os.path.abspath("."))

        # get devicenumber by looking for deviceobject in Hamlib module
        try:
            import Hamlib

            self.devicenumber = int(getattr(Hamlib, self.devicename))
        except Exception as err:
            if int(self.devicename):
                self.devicenumber = int(self.devicename)
            else:
                self.devicenumber = 6  # dummy
                self.log.warning("[RIGCTL] Radio not found. Using DUMMY!", error=err)

        # set deviceport to dummy port, if we selected dummy model
        if self.devicenumber in {1, 6}:
            self.deviceport = "/dev/ttyUSB0"

        print(self.devicenumber, self.deviceport, self.serialspeed)

        # select precompiled executable for win32/win64 rigctl
        # this is really a hack...somewhen we need a native hamlib integration for windows
        if sys.platform in ["win32", "win64"]:
            self.cmd = (
                app_path
                + "lib\\hamlib\\"
                + sys.platform
                + (
                    f"\\rigctl -m {self.devicenumber} "
                    f"-r {self.deviceport} "
                    f"-s {int(self.serialspeed)} "
                )
            )

        else:
            self.cmd = "rigctl -m %d -r %s -s %d " % (
                self.devicenumber,
                self.deviceport,
                int(self.serialspeed),
            )

        # eseguo semplicemente rigctl con il solo comando T 1 o T 0 per
        # il set e t per il get

        # set ptt to false if ptt is stuck for some reason
        self.set_ptt(False)
        return True

    def get_frequency(self):
        """ """
        cmd = f"{self.cmd} f"
        sw_proc = subprocess.Popen(
            cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
        )
        time.sleep(0.5)
        freq = sw_proc.communicate()[0]
        # print("get_frequency", freq, sw_proc.communicate())
        try:
            return int(freq)
        except Exception:
            return False

    def get_mode(self):
        """ """
        # (hamlib_mode, bandwidth) = self.my_rig.get_mode()
        # return Hamlib.rig_strrmode(hamlib_mode)
        try:
            return "PKTUSB"
        except Exception:
            return False

    def get_bandwidth(self):
        """ """
        # (hamlib_mode, bandwidth) = self.my_rig.get_mode()
        bandwidth = 2700

        try:
            return bandwidth
        except Exception:
            return False

    def set_mode(self, mode):
        """

        Args:
          mode:

        Returns:

        """
        # non usata
        return 0

    def get_ptt(self):
        """ """
        cmd = f"{self.cmd} t"
        sw_proc = subprocess.Popen(
            cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
        )
        time.sleep(0.5)
        status = sw_proc.communicate()[0]

        try:
            return status
        except Exception:
            return False

    def set_ptt(self, state):
        """

        Args:
          state:

        Returns:

        """
        cmd = f"{self.cmd} T "
        print("set_ptt", state)
        cmd = f"{cmd}1" if state else f"{cmd}0"
        print("set_ptt", cmd)

        sw_proc = subprocess.Popen(cmd, shell=True, text=True)
        try:
            return state
        except Exception:
            return False

    def close_rig(self):
        """ """
        # self.my_rig.close()
        return
