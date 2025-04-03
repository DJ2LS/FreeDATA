import numpy as np
import threading

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
        """Pop samples from the buffer.

        Args:
            n: The number of samples to pop from the buffer.

        Returns:
            A NumPy array containing the popped samples.

        Blocks until there are enough samples in the buffer.
        """
        with self.cond:
            # Block until enough samples are available.
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
            self.head = (self.head + n) % self.size
            self.nbuffer -= n
            self.cond.notify_all()
            return result