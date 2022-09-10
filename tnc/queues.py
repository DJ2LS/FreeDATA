"""
Hold queues used by more than one module to eliminate cyclic imports.
"""
import queue
import static

DATA_QUEUE_TRANSMIT = queue.Queue()
DATA_QUEUE_RECEIVED = queue.Queue()

# Initialize FIFO queue to store received frames
MODEM_RECEIVED_QUEUE = queue.Queue()
MODEM_TRANSMIT_QUEUE = queue.Queue()

# Initialize FIFO queue to finally store received data
RX_BUFFER = queue.Queue(maxsize=static.RX_BUFFER_SIZE)
