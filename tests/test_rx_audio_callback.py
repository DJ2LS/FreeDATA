"""Tests for the real-time-safe RX audio callback / worker split.

modem.RF.sd_input_audio_callback no longer runs the RX DSP inline; it copies the
captured block onto rx_audio_in_queue and returns, and rx_audio_processing_worker
drains that queue and runs the DSP (resample 48->8 kHz, FFT, demod-buffer push).

The stream is opened with blocksize=0, so the captured block size is whatever
PortAudio has available: device specific, variable, and not a multiple of
anything. rx_audio_processing_worker therefore re-blocks the captured stream to
RX_DSP_BLOCK_48K before any DSP runs on it.

These tests exercise that split directly with synthetic blocks, so they need no
audio hardware (CI has none). They cover:
  - the worker actually performs the relocated DSP on an enqueued block,
  - odd capture sizes are re-blocked rather than passed to the DSP short, and
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

# A capture size PortAudio really does hand us, and deliberately NOT a multiple of
# codec2's FDMDV_OS_48 (6) -- 512 % 6 == 2. Passing this straight to
# resample48_to_8 trips its "multiple of 6" assertion, which is what made the RX
# chain deaf (every block raising AssertionError) once blocksize=0 was used.
CAPTURE_FRAMES = 512


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


def _block(frames=CAPTURE_FRAMES):
    # sounddevice delivers indata as shape (frames, channels); int16 mono here.
    return (np.random.randn(frames, 1) * 3000).astype(np.int16)


class TestRxAudioCallbackWorkerSplit(unittest.TestCase):
    def test_worker_processes_enqueued_blocks(self):
        """Blocks handed to the callback are drained and DSP'd by the worker."""
        rf = _rf()
        rf.rx_audio_worker_running = True
        worker = threading.Thread(target=rf.rx_audio_processing_worker, daemon=True)
        worker.start()
        try:
            # status=None -> the block is enqueued (a truthy status is an
            # over/underflow and is dropped by the callback, unchanged by this PR).
            # Feed enough captured blocks to complete at least one DSP block.
            for _ in range(rf.RX_DSP_BLOCK_48K // CAPTURE_FRAMES + 1):
                rf.sd_input_audio_callback(_block(), CAPTURE_FRAMES, None, None)

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
        rf.sd_input_audio_callback(_block(), CAPTURE_FRAMES, None, None)
        elapsed = time.perf_counter() - t0

        self.assertEqual(rf.rx_audio_dropped_blocks, 1, "a full queue must drop the block and count it")
        self.assertLess(elapsed, 0.05, "callback must not block on a full queue (real-time safety)")


class TestRxAudioReblocking(unittest.TestCase):
    """The capture block size must never reach the DSP chain.

    blocksize=0 means PortAudio picks the size, and real devices hand back sizes
    that are not multiples of codec2's FDMDV_OS_48 (6). resample48_to_8 asserts on
    those, so process_rx_audio_block must accumulate instead of resampling short.
    These call process_rx_audio_block directly (no worker thread) so a failure is
    a raised exception rather than a swallowed, logged one.
    """

    def test_odd_capture_size_does_not_reach_the_resampler(self):
        """A 512-frame capture (512 % 6 == 2) must not raise AssertionError."""
        rf = _rf()
        # One short block: not enough for a DSP block, so it is carried, not resampled.
        rf.process_rx_audio_block(_block(CAPTURE_FRAMES))
        self.assertEqual(len(rf.rx_audio_carry_48k), CAPTURE_FRAMES)
        self.assertEqual(rf.ctx.audio_rx_queue.qsize(), 0, "a partial DSP block must not be processed short")

    def test_carry_reassembles_whole_dsp_blocks(self):
        """Odd captures are accumulated into exact RX_DSP_BLOCK_48K blocks."""
        rf = _rf()
        processed = []
        rf.run_rx_audio_dsp = lambda audio_48k: processed.append(len(audio_48k))

        # A spread of sizes a real device might deliver, none a multiple of 6.
        sizes = [512, 1024, 441, 512, 2048, 1024, 512, 940, 512, 1024]
        for size in sizes:
            rf.process_rx_audio_block(_block(size))

        total = sum(sizes)
        self.assertEqual(
            processed,
            [rf.RX_DSP_BLOCK_48K] * (total // rf.RX_DSP_BLOCK_48K),
            "every DSP invocation must get exactly one whole block",
        )
        self.assertEqual(len(rf.rx_audio_carry_48k), total % rf.RX_DSP_BLOCK_48K, "remainder must be carried over")

    def test_reblocking_preserves_the_sample_stream(self):
        """No sample is dropped, duplicated or reordered by the re-blocking.

        The resampler's filter memory spans blocks, so the stream it sees has to be
        the captured stream exactly.
        """
        rf = _rf()
        seen = []
        rf.run_rx_audio_dsp = lambda audio_48k: seen.append(np.array(audio_48k))

        sizes = [700, 1300, 512, 4800, 441]
        captured = [np.arange(s, dtype=np.int16).reshape(-1, 1) for s in sizes]
        for block in captured:
            rf.process_rx_audio_block(block)

        expected = np.concatenate([b.reshape(-1) for b in captured])
        got = np.concatenate(seen + [rf.rx_audio_carry_48k])
        np.testing.assert_array_equal(got, expected)

    def test_real_resampler_accepts_every_reblocked_block(self):
        """End to end with the real codec2 resampler: odd captures, no assertion."""
        rf = _rf()
        for size in (512, 1024, 441, 2048, 512, 1024, 512, 4800):
            rf.process_rx_audio_block(_block(size))  # raises AssertionError if short
        self.assertGreater(rf.ctx.audio_rx_queue.qsize(), 0, "DSP should have run on the reassembled blocks")


if __name__ == "__main__":
    unittest.main()
