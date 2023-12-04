"""
Hold queues used by more than one module to eliminate cyclic imports.
"""
import queue

DATA_QUEUE_TRANSMIT = queue.Queue()
DATA_QUEUE_RECEIVED = queue.Queue()

# Initialize FIFO queue to store received frames
MESH_RECEIVED_QUEUE = queue.Queue()
MESH_QUEUE_TRANSMIT = queue.Queue()
MESH_SIGNALLING_TABLE = []

# Initialize FIFO queue to finally store received data
# TODO Fix rx_buffer_size
RX_BUFFER = queue.Queue(maxsize=16)

# Commands we want to send to rigctld
RIGCTLD_COMMAND_QUEUE = queue.Queue()