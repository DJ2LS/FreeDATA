#!/usr/bin/env python3

import sys
import re
import logging, structlog, log_handler
import atexit


# try importing hamlib    
try:
    # get python version
    python_version = str(sys.version_info[0]) + "." + str(sys.version_info[1])

    # installation path for Ubuntu 20.04 LTS python modules
    sys.path.append('/usr/local/lib/python'+ python_version +'/site-packages')
    # installation path for Ubuntu 20.10 +
    sys.path.append('/usr/local/lib/')
    import Hamlib
            
    # https://stackoverflow.com/a/4703409
    hamlib_version = re.findall(r"[-+]?\d*\.?\d+|\d+", Hamlib.cvar.hamlib_version)    
    hamlib_version = float(hamlib_version[0])
            
    min_hamlib_version = 4.1
    if hamlib_version > min_hamlib_version:
        structlog.get_logger("structlog").info("[TNC] Hamlib found", version=hamlib_version)
    else:
        structlog.get_logger("structlog").warning("[TNC] Hamlib outdated", found=hamlib_version, recommend=min_hamlib_version)
except Exception as e:
    structlog.get_logger("structlog").critical("[TNC] Hamlib not found", error=e)

               
               
class radio:
    def __init__(self):
    
        self.devicename = ''
        self.devicenumber = ''
        self.deviceport = ''
        self.serialspeed = 0
        self.hamlib_ptt_type = ''
        self.my_rig = ''
    

    def open_rig(self, devicename, deviceport, hamlib_ptt_type, serialspeed):    
        
        self.devicename = devicename
        self.deviceport = deviceport
        self.serialspeed = str(serialspeed) # we need to ensure this is a str, otherwise set_conf functions are crashing
        self.hamlib_ptt_type = hamlib_ptt_type
        
        # try to init hamlib
        try:
            Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)

            # get devicenumber by looking for deviceobject in Hamlib module
            try:
                self.devicenumber = int(getattr(Hamlib, self.devicename))
            except:
                structlog.get_logger("structlog").error("[DMN] Hamlib: rig not supported...")
                self.devicenumber = 0
            
            
            self.my_rig = Hamlib.Rig(self.devicenumber)
            self.my_rig.set_conf("rig_pathname", self.deviceport)
            self.my_rig.set_conf("retry", "5")
            self.my_rig.set_conf("serial_speed", self.serialspeed)
            self.my_rig.set_conf("serial_handshake", "None")
            self.my_rig.set_conf("stop_bits", "1")
            self.my_rig.set_conf("data_bits", "8")
            
            if self.hamlib_ptt_type == 'RIG':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_RIG
                self.my_rig.set_conf("ptt_type", 'RIG')

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

            else: #self.hamlib_ptt_type == 'RIG_PTT_NONE':
                self.hamlib_ptt_type = Hamlib.RIG_PTT_NONE

            
            self.my_rig.open()
            atexit.register(self.my_rig.close)
            
            try:
                # lets determine the error message when opening rig
                error = str(Hamlib.rigerror(my_rig.error_status)).splitlines()
                error = error[1].split('err=')
                error = error[1]
                            
                if error == 'Permission denied':
                    structlog.get_logger("structlog").error("[DMN] Hamlib has no permissions", e = error)
                    help_url = 'https://github.com/DJ2LS/FreeDATA/wiki/UBUNTU-Manual-installation#1-permissions'
                    structlog.get_logger("structlog").error("[DMN] HELP:", check = help_url)
            except:
                structlog.get_logger("structlog").info("[DMN] Hamlib device openend", status='SUCCESS')


            # set ptt to false if ptt is stuck for some reason
            self.set_ptt(False)

            # set rig mode to USB
            self.my_rig.set_mode(Hamlib.RIG_MODE_USB)
            return True

        except Exception as e:
            structlog.get_logger("structlog").error("[TNC] Hamlib - can't open rig", error=e, e=sys.exc_info()[0])
            return False
            
    def get_frequency(self):
        return int(self.my_rig.get_freq())
        
    def get_mode(self):
        (hamlib_mode, bandwith) = self.my_rig.get_mode()
        return Hamlib.rig_strrmode(hamlib_mode)
    
    def get_bandwith(self):
        (hamlib_mode, bandwith) = self.my_rig.get_mode()
        return bandwith

    def set_mode(self, mode):
        return 0
      
    def get_ptt(self):
        return self.my_rig.get_ptt()
                  
    def set_ptt(self, state):
        if state:
            self.my_rig.set_ptt(self.hamlib_ptt_type, 1)
        else:
            self.my_rig.set_ptt(self.hamlib_ptt_type, 0)
        return state
        
    def close_rig(self):
        self.my_rig.close()
