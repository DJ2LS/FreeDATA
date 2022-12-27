#!/usr/bin/env python3
# class taken from darksidelemm
# rigctl - https://github.com/darksidelemm/rotctld-web-gui/blob/master/rotatorgui.py#L35
#
# modified and adjusted to FreeDATA needs by DJ2LS

import socket
import time
import structlog
import threading

# set global hamlib version
hamlib_version = 0


class radio:
    """rigctld (hamlib) communication class"""

    log = structlog.get_logger("radio (rigctld)")

    def __init__(self, hostname="localhost", port=4532, poll_rate=5, timeout=5):
        """Open a connection to rigctld, and test it for validity"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.connected = False
        self.hostname = hostname
        self.port = port
        self.connection_attempts = 5

        # class wide variable for some parameters
        self.bandwidth = ''
        self.frequency = ''
        self.mode = ''


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
        self.hostname = rigctld_ip
        self.port = int(rigctld_port)

        if self.connect():
            self.log.debug("Rigctl initialized")
            return True

        self.log.error(
            "[RIGCTLD] Can't connect!", ip=self.hostname, port=self.port
        )
        return False

    def connect(self):
        """Connect to rigctld instance"""
        if not self.connected:
            try:
                self.connection = socket.create_connection((self.hostname, self.port))
                self.connected = True
                self.log.info(
                    "[RIGCTLD] Connected to rigctld!", ip=self.hostname, port=self.port
                )
                return True
            except Exception as err:
                # ConnectionRefusedError: [Errno 111] Connection refused
                self.close_rig()
                self.log.warning(
                    "[RIGCTLD] Reconnect...",
                    ip=self.hostname,
                    port=self.port,
                    e=err,
                )
                return False

    def close_rig(self):
        """ """
        self.sock.close()
        self.connected = False

    def send_command(self, command) -> bytes:
        """Send a command to the connected rotctld instance,
            and return the return value.

        Args:
          command:

        """
        if self.connected:
            try:
                self.connection.sendall(command + b"\n")
            except Exception:
                self.log.warning(
                    "[RIGCTLD] Command not executed!",
                    command=command,
                    ip=self.hostname,
                    port=self.port,
                )
                self.connected = False

            try:
                return self.connection.recv(16)
            except Exception:
                self.log.warning(
                    "[RIGCTLD] No command response!",
                    command=command,
                    ip=self.hostname,
                    port=self.port,
                )
                self.connected = False
        else:

            # reconnecting....
            threading.Event().wait(0.5)
            self.connect()

        return b""

    def get_status(self):
        """ """
        return "connected" if self.connected else "unknown/disconnected"

    def get_mode(self):
        """ """
        try:
            data = self.send_command(b"m")
            data = data.split(b"\n")
            data = data[0].decode("utf-8")
            if 'RPRT' not in data:
                self.mode = data

            return self.mode
        except Exception:
            return self.mode

    def get_bandwidth(self):
        """ """
        try:
            data = self.send_command(b"m")
            data = data.split(b"\n")
            data = data[1].decode("utf-8")

            if 'RPRT' not in data:
                self.bandwidth = int(data)
            return self.bandwidth
        except Exception:
            return self.bandwidth

    def get_frequency(self):
        """ """
        try:
            data = self.send_command(b"f")
            data = data.decode("utf-8")
            if 'RPRT' not in data:
                self.frequency = data

            return self.frequency
        except Exception:
            return self.frequency

    def get_ptt(self):
        """ """
        try:
            return self.send_command(b"t")
        except Exception:
            return False

    def set_ptt(self, state):
        """

        Args:
          state:

        Returns:

        """
        try:
            if state:
                self.send_command(b"T 1")
            else:
                self.send_command(b"T 0")
            return state
        except Exception:
            return False
