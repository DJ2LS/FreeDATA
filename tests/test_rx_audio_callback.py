"""Tests for the real-time-safe RX audio callback / worker split.

modem.RF.sd_input_audio_callback no longer runs the RX DSP inline; it copies the
captured block onto rx_audio_in_queue and returns, and rx_audio_processing_worker
drains that queue and runs the DSP (resample 48->8 kHz, FFT, demod-buffer push).

These tests exercise that split directly with synthetic blocks, so they need no
audio hardware (CI has none). They cover:
  - the worker actually performs the relocated DSP on an enqueued block, and
  - the callback drops (and counts) instead of blocking when the queue is full,
    which is the real-time-safety property the change exists to provide.
"""

import threading
import time
import unittest

import numpy as np

from freedata_server.context import AppContext
from freedata_server import modem, codec2

CONFIG = "freedata_server/config.ini.example"
BLOCK_FRAMES = 4800  # one 48 kHz input block, matching sd.InputStream(blocksize=4800)


def _rf():
    """A real RF wired to a real AppContext, without opening audio devices.

    start_modem() would normally create the resampler (and, in TESTMODE, start
    the demodulator decode threads); we only need the resampler here, so we set
    it directly and leave the demod buffers as None -- the worker's buffer-push
    is guarded by `if audiobuffer` and is intentionally not under test.
    """
    ctx = AppContext(CONFIG)
    ctx.TESTMODE = True
    rf = modem.RF(ctx)
    rf.resampler = codec2.resampler()
    return rf


def _block():
    # sounddevice delivers indata as shape (frames, channels); int16 mono here.
    return (np.random.randn(BLOCK_FRAMES, 1) * 3000).astype(np.int16)


class TestRxAudioCallbackWorkerSplit(unittest.TestCase):
    def test_worker_processes_enqueued_block(self):
        """A block handed to the callback is drained and DSP'd by the worker."""
        rf = _rf()
        rf.rx_audio_worker_running = True
        worker = threading.Thread(target=rf.rx_audio_processing_worker, daemon=True)
        worker.start()
        try:
            # status=None -> the block is enqueued (a truthy status is an
            # over/underflow and is dropped by the callback, unchanged by this PR).
            rf.sd_input_audio_callback(_block(), BLOCK_FRAMES, None, None)

            # The worker resamples to 8 kHz and feeds enqueue_streaming_audio_chunks,
            # which lands on ctx.audio_rx_queue -- our deterministic "DSP ran" signal.
            deadline = time.time() + 5
            while rf.ctx.audio_rx_queue.qsize() == 0 and time.time() < deadline:
                time.sleep(0.02)

            self.assertGreater(rf.ctx.audio_rx_queue.qsize(), 0, "worker did not process the enqueued RX audio block")
            self.assertTrue(rf.rx_audio_in_queue.empty(), "worker should have drained the input queue")
            self.assertEqual(rf.rx_audio_dropped_blocks, 0, "no block should be dropped under normal operation")
        finally:
            rf.rx_audio_worker_running = False
            rf.rx_audio_in_queue.put_nowait(None)  # release the worker's get()
            worker.join(timeout=2)

    def test_callback_drops_and_does_not_block_when_queue_full(self):
        """With the worker stalled and the queue full, the callback drops the
        block (counted) and returns immediately -- it must never block the
        real-time audio thread."""
        rf = _rf()  # worker intentionally NOT started -> queue never drains
        for _ in range(rf.rx_audio_in_queue.maxsize):
            rf.rx_audio_in_queue.put_nowait(object())
        self.assertTrue(rf.rx_audio_in_queue.full())

        t0 = time.perf_counter()
        rf.sd_input_audio_callback(_block(), BLOCK_FRAMES, None, None)
        elapsed = time.perf_counter() - t0

        self.assertEqual(rf.rx_audio_dropped_blocks, 1, "a full queue must drop the block and count it")
        self.assertLess(elapsed, 0.05, "callback must not block on a full queue (real-time safety)")


if __name__ == "__main__":
    unittest.main()
