import sys
import time
import unittest
import unittest.mock
import queue
import threading
import random
import socket
import structlog
import numpy as np

sys.path.append('freedata_server')

from config import CONFIG
from data_frame_factory import DataFrameFactory
from state_manager import StateManager
from event_manager import EventManager
from frame_dispatcher import DISPATCHER
from socket_interface import SocketInterfaceHandler
import codec2

class TestModem:
    def __init__(self, event_q, state_q):
        self.data_queue_received = queue.Queue()
        self.demodulator = unittest.mock.Mock()
        self.event_manager = EventManager([event_q])
        self.logger = structlog.get_logger('Modem')
        self.states = StateManager(state_q)

    def getFrameTransmissionTime(self, mode):
        samples = 0
        c2instance = codec2.open_instance(mode.value)
        samples += codec2.api.freedv_get_n_tx_preamble_modem_samples(c2instance)
        samples += codec2.api.freedv_get_n_tx_modem_samples(c2instance)
        samples += codec2.api.freedv_get_n_tx_postamble_modem_samples(c2instance)
        return samples / 8000

    def transmit(self, mode, repeats: int, repeat_delay: int, frames: bytearray) -> bool:
        tx_time = self.getFrameTransmissionTime(mode) + 0.1
        self.logger.info(f"TX {tx_time} seconds...")
        threading.Event().wait(tx_time)
        self.data_queue_received.put({
            'mode': mode,
            'bytes': frames,
        })

class TestP2PConnectionSession(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_manager = CONFIG('freedata_server/config.ini.example')
        cls.config = config_manager.read()
        cls.logger = structlog.get_logger("TESTS")
        cls.channels_running = True

        # ISS Setup
        cls.iss_event_queue = queue.Queue()
        cls.iss_state_queue = queue.Queue()
        cls.iss_modem = TestModem(cls.iss_event_queue, cls.iss_state_queue)
        conf = config_manager.read()
        conf['SOCKET_INTERFACE']['cmd_port'] = 8000
        conf['SOCKET_INTERFACE']['data_port'] = 8001
        config_manager.write(conf)
        cls.iss_socket_interface_manager = SocketInterfaceHandler(cls.iss_modem, config_manager, StateManager(queue.Queue()), EventManager([queue.Queue()])).start_servers()

        cls.iss_socket_cmd_client = socket.create_connection(('127.0.0.1', 8000))
        cls.iss_socket_data_client = socket.create_connection(('127.0.0.1', 8001))

        # IRS Setup
        cls.irs_event_queue = queue.Queue()
        cls.irs_state_queue = queue.Queue()
        cls.irs_modem = TestModem(cls.irs_event_queue, cls.irs_state_queue)
        conf = config_manager.read()
        conf['SOCKET_INTERFACE']['cmd_port'] = 9000
        conf['SOCKET_INTERFACE']['data_port'] = 9001
        config_manager.write(conf)
        cls.irs_socket_interface_manager = SocketInterfaceHandler(cls.irs_modem, config_manager, StateManager(queue.Queue()), EventManager([queue.Queue()])).start_servers()

        cls.irs_socket_cmd_client = socket.create_connection(('127.0.0.1', 9000))
        cls.irs_socket_data_client = socket.create_connection(('127.0.0.1', 9001))

        # Channels
        cls.iss_frame_dispatcher = DISPATCHER(cls.config, EventManager([queue.Queue()]), StateManager(queue.Queue()), cls.iss_modem, cls.iss_socket_interface_manager)
        cls.irs_frame_dispatcher = DISPATCHER(cls.config, EventManager([queue.Queue()]), StateManager(queue.Queue()), cls.irs_modem, cls.irs_socket_interface_manager)

        cls.connected_event = threading.Event()
        cls.loss_probability = 0

        threading.Thread(target=cls.read_from_socket, args=(cls.iss_socket_cmd_client, 'CMD', 'ISS'), daemon=True).start()
        threading.Thread(target=cls.read_from_socket, args=(cls.iss_socket_data_client, 'DATA', 'ISS'), daemon=True).start()
        threading.Thread(target=cls.read_from_socket, args=(cls.irs_socket_cmd_client, 'CMD', 'IRS'), daemon=True).start()
        threading.Thread(target=cls.read_from_socket, args=(cls.irs_socket_data_client, 'DATA', 'IRS'), daemon=True).start()

    @staticmethod
    def read_from_socket(sock, type=None, direction=None):
        while True:
            try:
                data = sock.recv(48)
                if not data:
                    break
                print(f"\nReceived {type}-{direction}: {data.decode().strip()}\n")
            except Exception:
                break

    def channelWorker(self, modem_transmit_queue, frame_dispatcher):
        while self.channels_running:
            try:
                transmission = modem_transmit_queue.get(timeout=1)
                if random.randint(0, 100) < self.loss_probability:
                    continue
                frame_dispatcher.process_data(transmission['bytes'], None, len(transmission['bytes']), 0, 0, "test")
            except queue.Empty:
                continue

    def testConnect(self):
        self.channels_running = True

        self.iss_to_irs_channel = threading.Thread(target=self.channelWorker, args=(self.iss_modem.data_queue_received, self.irs_frame_dispatcher))
        self.iss_to_irs_channel.start()

        self.irs_to_iss_channel = threading.Thread(target=self.channelWorker, args=(self.irs_modem.data_queue_received, self.iss_frame_dispatcher))
        self.irs_to_iss_channel.start()

        time.sleep(2)

        cmd = 'CONNECT AA1AAA-1 BB2BBB-2 2300\r\n'
        self.iss_socket_cmd_client.sendall(cmd.encode('utf-8'))

        data = 'HELLO WORLD TEST\r\n'
        self.iss_socket_data_client.sendall(data.encode('utf-8'))

        time.sleep(5)  # wait for some packets to go through

        self.channels_running = False
        self.iss_to_irs_channel.join()
        self.irs_to_iss_channel.join()

    @classmethod
    def tearDownClass(cls):
        cls.iss_socket_cmd_client.close()
        cls.iss_socket_data_client.close()
        cls.irs_socket_cmd_client.close()
        cls.irs_socket_data_client.close()

if __name__ == '__main__':
    unittest.main()
