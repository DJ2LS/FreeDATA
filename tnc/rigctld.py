#!/usr/bin/env python3
# class taken from darksidelemm
# rigctl - https://github.com/darksidelemm/rotctld-web-gui/blob/master/rotatorgui.py#L35
#
# modified and adjusted to FreeDATA needs by DJ2LS

import contextlib
import socket
import time
import structlog
import threading
import static

# set global hamlib version
hamlib_version = 0


class radio:
    """rigctld (hamlib) communication class"""

    log = structlog.get_logger("radio (rigctld)")

    def __init__(self, hostname="localhost", port=4532, poll_rate=5, timeout=5):
        """Open a connection to rigctld, and test it for validity"""
        self.ptt_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.ptt_connected = False
        self.data_connected = False
        self.hostname = hostname
        self.port = port
        self.connection_attempts = 5

        # class wide variable for some parameters
        self.bandwidth = ''
        self.frequency = ''
        self.mode = ''
        self.alc = ''
        self.strength = ''
        self.rf = ''

    def open_rig(
            self,
            rigctld_ip,
            rigctld_port
    ):
        """

        Args:
          rigctld_ip:
          rigctld_port:

        Returns:

        """
        self.hostname = rigctld_ip
        self.port = int(rigctld_port)

        # _ptt_connect = self.ptt_connect()
        # _data_connect = self.data_connect()

        ptt_thread = threading.Thread(target=self.ptt_connect, args=[], daemon=True)
        ptt_thread.start()

        data_thread = threading.Thread(target=self.data_connect, args=[], daemon=True)
        data_thread.start()

        # wait some time
        threading.Event().wait(0.5)

        if self.ptt_connected and self.data_connected:
            self.log.debug("Rigctl DATA/PTT initialized")
            return True

        self.log.error(
            "[RIGCTLD] Can't connect!", ip=self.hostname, port=self.port
        )
        return False

    def ptt_connect(self):
        """Connect to rigctld instance"""
        while True:

            if not self.ptt_connected:
                try:
                    self.ptt_connection = socket.create_connection((self.hostname, self.port))
                    self.ptt_connected = True
                    self.log.info(
                        "[RIGCTLD] Connected PTT instance to rigctld!", ip=self.hostname, port=self.port
                    )
                except Exception as err:
                    # ConnectionRefusedError: [Errno 111] Connection refused
                    self.close_rig()
                    self.log.warning(
                        "[RIGCTLD] PTT Reconnect...",
                        ip=self.hostname,
                        port=self.port,
                        e=err,
                    )

            threading.Event().wait(0.5)

    def data_connect(self):
        """Connect to rigctld instance"""
        while True:
            if not self.data_connected:
                try:
                    self.data_connection = socket.create_connection((self.hostname, self.port))
                    self.data_connected = True
                    self.log.info(
                        "[RIGCTLD] Connected DATA instance to rigctld!", ip=self.hostname, port=self.port
                    )
                except Exception as err:
                    # ConnectionRefusedError: [Errno 111] Connection refused
                    self.close_rig()
                    self.log.warning(
                        "[RIGCTLD] DATA Reconnect...",
                        ip=self.hostname,
                        port=self.port,
                        e=err,
                    )
            threading.Event().wait(0.5)

    def close_rig(self):
        """ """
        self.ptt_sock.close()
        self.data_sock.close()
        self.ptt_connected = False
        self.data_connected = False

    def send_ptt_command(self, command, expect_answer) -> bytes:
        """Send a command to the connected rotctld instance,
            and return the return value.

        Args:
          command:

        """
        if self.ptt_connected:
            try:
                self.ptt_connection.sendall(command + b"\n")
            except Exception:
                self.log.warning(
                    "[RIGCTLD] Command not executed!",
                    command=command,
                    ip=self.hostname,
                    port=self.port,
                )
                self.ptt_connected = False
        return b""

    def send_data_command(self, command, expect_answer) -> bytes:
        """Send a command to the connected rotctld instance,
            and return the return value.

        Args:
          command:

        """
        if self.data_connected:
            self.data_connection.setblocking(False)
            self.data_connection.settimeout(0.05)
            try:
                self.data_connection.sendall(command + b"\n")


            except Exception:
                self.log.warning(
                    "[RIGCTLD] Command not executed!",
                    command=command,
                    ip=self.hostname,
                    port=self.port,
                )
                self.data_connected = False

            try:
                # recv seems to be blocking so in case of ptt we don't need the response
                # maybe this speeds things up and avoids blocking states
                recv = True
                data = b''

                while recv:
                    try:

                        data = self.data_connection.recv(4800)

                    except socket.timeout:
                        recv = False

                return data

                # return self.data_connection.recv(64) if expect_answer else True
            except Exception:
                self.log.warning(
                    "[RIGCTLD] No command response!",
                    command=command,
                    ip=self.hostname,
                    port=self.port,
                )
                self.data_connected = False
        return b""

    def get_status(self):
        """ """
        return "connected" if self.data_connected and self.ptt_connected else "unknown/disconnected"

    def get_level(self):
        try:
            data = self.send_data_command(b"l RF", True)
            data = data.split(b"\n")
            rf = data[0].decode("utf-8")
            if 'RPRT' not in rf:
                try:
                    self.rf = str(rf)
                except ValueError:
                    self.rf = str(rf)

            return self.rf
        except Exception:
            return self.rf

    def get_strength(self):
        try:
            data = self.send_data_command(b"l STRENGTH", True)
            data = data.split(b"\n")
            strength = data[0].decode("utf-8")
            if 'RPRT' not in strength:
                try:
                    self.strength = str(strength)
                except ValueError:
                    self.strength = str(strength)

            return self.strength
        except Exception:
            return self.strength

    def get_alc(self):
        try:
            data = self.send_data_command(b"l ALC", True)
            data = data.split(b"\n")
            alc = data[0].decode("utf-8")
            if 'RPRT' not in alc:
                try:
                    alc = float(alc)
                    self.alc = alc if alc != 0.0 else static.HAMLIB_ALC
                except ValueError:
                    self.alc = 0.0

            return self.alc
        except Exception:
            return self.alc

    def get_mode(self):
        """ """
        try:
            data = self.send_data_command(b"m", True)
            data = data.split(b"\n")
            data = data[0].decode("utf-8")
            if 'RPRT' not in data:
                try:
                    data = int(data)
                except ValueError:
                    self.mode = str(data)

            return self.mode
        except Exception:
            return self.mode

    def get_bandwidth(self):
        """ """
        try:
            data = self.send_data_command(b"m", True)
            data = data.split(b"\n")
            data = data[1].decode("utf-8")

            if 'RPRT' not in data and data not in ['']:
                with contextlib.suppress(ValueError):
                    self.bandwidth = int(data)
            return self.bandwidth
        except Exception:
            return self.bandwidth

    def get_frequency(self):
        """ """
        try:
            data = self.send_data_command(b"f", True)
            data = data.decode("utf-8")
            if 'RPRT' not in data and data not in [0, '0', '']:
                with contextlib.suppress(ValueError):
                    data = int(data)
                    # make sure we have a frequency and not bandwidth
                    if data >= 10000:
                        self.frequency = data
            return self.frequency
        except Exception:
            return self.frequency

    def get_ptt(self):
        """ """
        try:
            return self.send_data_command(b"t", True)
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
                self.send_ptt_command(b"T 1", False)
            else:
                self.send_ptt_command(b"T 0", False)
            return state
        except Exception:
            return False

    def set_frequency(self, frequency):
        """

        Args:
          frequency:

        Returns:

        """
        try:
            command = bytes(f"F {frequency}", "utf-8")
            self.send_data_command(command, False)
        except Exception:
            return False

    def set_mode(self, mode):
        """

        Args:
          mode:

        Returns:

        """
        try:
            command = bytes(f"M {mode} {self.bandwidth}", "utf-8")
            self.send_data_command(command, False)
        except Exception:
            return False