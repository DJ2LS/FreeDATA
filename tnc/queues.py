"""
Hold queues used by more than one module to eliminate cyclic imports.
"""
import queue
import static
from static import ARQ, AudioParam, Beacon, Channel, Daemon, HamlibParam, ModemParam, Station, TCIParam, TNC

DATA_QUEUE_TRANSMIT = queue.Queue()
DATA_QUEUE_RECEIVED = queue.Queue()

# Initialize FIFO queue to store received frames
MODEM_RECEIVED_QUEUE = queue.Queue()
MODEM_TRANSMIT_QUEUE = queue.Queue()

# Initialize FIFO queue to store received frames
MESH_RECEIVED_QUEUE = queue.Queue()

# Initialize FIFO queue to store audio frames
AUDIO_RECEIVED_QUEUE = queue.Queue()
AUDIO_TRANSMIT_QUEUE = queue.Queue()

# Initialize FIFO queue to finally store received data
RX_BUFFER = queue.Queue(maxsize=ARQ.rx_buffer_size)

# Commands we want to send to rigctld
RIGCTLD_COMMAND_QUEUE = queue.Queue()