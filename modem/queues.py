"""
Hold queues used by more than one module to eliminate cyclic imports.
"""
import queue

# Initialize FIFO queue to store received frames
MESH_RECEIVED_QUEUE = queue.Queue()
MESH_QUEUE_TRANSMIT = queue.Queue()
MESH_SIGNALLING_TABLE = []

# Commands we want to send to rigctld
RIGCTLD_COMMAND_QUEUE = queue.Queue()