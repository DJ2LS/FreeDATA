import numpy as np
import threading
import structlog
log = structlog.get_logger("buffer")

class CircularBuffer:
    """A circular buffer for storing audio samples.

    The buffer is implemented as a NumPy array of a fixed size.  The push()
    method adds samples to the buffer, and the pop() method removes samples
    from the buffer.  Both methods block if the buffer is full or empty,
    respectively.
    """
    def __init__(self, size):
        self.size = size
        self.buffer = np.zeros(size, dtype=np.int16)
        self.head = 0  # Read pointer.
        self.tail = 0  # Write pointer.
        self.nbuffer = 0  # Number of samples stored.
        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)
        log.debug("[BUF] Creating ring buffer", size=size)

    def push(self, samples):
        """Push samples onto the buffer.

        Args:
            samples: The samples to push onto the buffer.

        Blocks until there is enough space in the buffer.
        """
        with self.cond:
            samples_len = len(samples)
            # Block until there is room.
            while self.nbuffer + samples_len > self.size:
                self.cond.wait()
            end_space = self.size - self.tail
            if samples_len <= end_space:
                self.buffer[self.tail:self.tail + samples_len] = samples
            else:
                self.buffer[self.tail:] = samples[:end_space]
                self.buffer[:samples_len - end_space] = samples[end_space:]
            self.tail = (self.tail + samples_len) % self.size
            self.nbuffer += samples_len
            self.cond.notify_all()

    def pop(self, n):
        with self.cond:
            while self.nbuffer < n:
                self.cond.wait()
            end_space = self.size - self.head
            if n <= end_space:
                result = self.buffer[self.head:self.head + n].copy()
            else:
                result = np.concatenate((
                    self.buffer[self.head:].copy(),
                    self.buffer[:n - end_space].copy()
                ))
            # Update head and count.
            self.head = (self.head + n) % self.size
            self.nbuffer -= n
            if self.nbuffer > 0:
                # Reassemble the valid data contiguously at the start.
                if self.head + self.nbuffer <= self.size:
                    self.buffer[:self.nbuffer] = self.buffer[self.head:self.head + self.nbuffer]
                else:
                    part1 = self.size - self.head
                    self.buffer[:part1] = self.buffer[self.head:]
                    self.buffer[part1:self.nbuffer] = self.buffer[:self.nbuffer - part1]
                self.head = 0
                self.tail = self.nbuffer
            self.cond.notify_all()
            return result
