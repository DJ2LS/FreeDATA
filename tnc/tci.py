#!/usr/bin/env python3
# class taken from darksidelemm
# rigctl - https://github.com/darksidelemm/rotctld-web-gui/blob/master/rotatorgui.py#L35
#
# modified and adjusted to FreeDATA needs by DJ2LS

import socket
import structlog
import threading
import static
import numpy as np

class TCI:
    """TCI (hamlib) communication class"""

    log = structlog.get_logger("radio (TCI)")

    def __init__(self, hostname="localhost", port=9000, poll_rate=5, timeout=5):
        """Open a connection to TCI, and test it for validity"""
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
            tci_ip,
            tci_port
    ):
        """

        Args:
          tci_ip:
          tci_port:

        Returns:

        """
        self.hostname = tci_ip
        self.port = int(tci_port)

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
            "[TCI] Can't connect!", ip=self.hostname, port=self.port
        )
        return False

    def ptt_connect(self):
        """Connect to TCI instance"""
        while True:

            if not self.ptt_connected:
                try:
                    self.ptt_connection = socket.create_connection((self.hostname, self.port))
                    self.ptt_connected = True
                    self.log.info(
                        "[TCI] Connected PTT instance to TCI!", ip=self.hostname, port=self.port
                    )
                except Exception as err:
                    # ConnectionRefusedError: [Errno 111] Connection refused
                    self.close_rig()
                    self.log.warning(
                        "[TCI] PTT Reconnect...",
                        ip=self.hostname,
                        port=self.port,
                        e=err,
                    )

            threading.Event().wait(0.5)

    def data_connect(self):
        """Connect to TCI instance"""
        while True:
            if not self.data_connected:
                try:
                    self.data_connection = socket.create_connection((self.hostname, self.port))
                    self.data_connected = True
                    self.log.info(
                        "[TCI] Connected DATA instance to TCI!", ip=self.hostname, port=self.port
                    )
                except Exception as err:
                    # ConnectionRefusedError: [Errno 111] Connection refused
                    self.close_rig()
                    self.log.warning(
                        "[TCI] DATA Reconnect...",
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
                self.ptt_connection.sendall(command)
            except Exception:
                self.log.warning(
                    "[TCI] Command not executed!",
                    command=command,
                    ip=self.hostname,
                    port=self.port,
                )
                self.ptt_connected = False
        return b""

    def send_data_command(self, command, expect_answer) -> bytes:
        """Send a command to the connected tci instance,
            and return the return value.

        Args:
          command:

        """
        if self.data_connected:
            self.data_connection.setblocking(False)
            self.data_connection.settimeout(0.05)
            try:
                self.data_connection.sendall(command)


            except Exception:
                self.log.warning(
                    "[TCI] Command not executed!",
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

                        data = self.data_connection.recv(64)

                    except socket.timeout:
                        recv = False

                return data

                # return self.data_connection.recv(64) if expect_answer else True
            except Exception:
                self.log.warning(
                    "[TCI] No command response!",
                    command=command,
                    ip=self.hostname,
                    port=self.port,
                )
                self.data_connected = False
        return b""

    def init_audio(self):
        try:
            self.send_data_command(b"IQ_SAMPLERATE:48000;", False)
            self.send_data_command(b"audio_samplerate:8;", False)
            self.send_data_command(b"audio_start: 0;", False)

            return True
        except Exception:
            return False

    def get_audio(self):
        """"""
        # generate random audio data
        if not self.data_connected:
            return np.random.uniform(-1, 1, 48000)

        try:
            return self.data_connection.recv(4800)
        except Exception:
            return False


    def push_audio(self):
        """ """
        try:
            return self.send_data_command(b"PUSH AUDIO COMMAND ", True)
        except Exception:
            return False

