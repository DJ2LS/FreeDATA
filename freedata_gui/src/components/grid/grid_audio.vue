<script setup>
import { setActivePinia } from 'pinia';
import { ref, onBeforeUnmount } from 'vue';

import pinia from '../../store/index';
setActivePinia(pinia);

import { useAudioStore } from '@/store/audioStore';
const audio = useAudioStore(pinia);

const SAMPLE_RATE = 8000;
// Poll interval for new blocks
const POLL_MS = 20;
// Headroom added when (re)starting after an underrun, absorbs network jitter
const START_DELAY_S = 0.1;
// Drop blocks if more than this much audio is already scheduled (bounds latency)
const MAX_QUEUED_S = 1.0;

var audioCtx = null;
var loopTimer = null;
var nextStartTime = 0;
var isPlaying = ref(false);

function scheduleBlock(ctx, block) {
  if (!block || block.length === 0) return;

  const now = ctx.currentTime;
  if (nextStartTime < now) {
    // Underrun or first block: start slightly in the future
    nextStartTime = now + START_DELAY_S;
  } else if (nextStartTime - now > MAX_QUEUED_S) {
    // Too much audio queued already; drop this block to keep latency bounded
    return;
  }

  const float32 = Float32Array.from(block, s => s / 32768);
  const buffer = ctx.createBuffer(1, float32.length, SAMPLE_RATE);
  buffer.copyToChannel(float32, 0);

  const source = ctx.createBufferSource();
  source.buffer = buffer;
  source.connect(ctx.destination);
  source.start(nextStartTime);
  nextStartTime += buffer.duration;
}

function loop(ctx) {
  // A newer Start (or Stop) replaced this context; let this loop end
  if (!isPlaying.value || ctx !== audioCtx) return;

  let block = audio.getNextBlock();
  while (block) {
    try {
      scheduleBlock(ctx, block);
    } catch (err) {
      console.warn("Skipping audio block", err);
    }
    block = audio.getNextBlock();
  }

  loopTimer = setTimeout(() => loop(ctx), POLL_MS);
}

function playRxStream() {
  if (isPlaying.value) return;

  // Discard audio buffered while nobody was listening
  audio.resetBuffer();

  const ctx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: SAMPLE_RATE });
  audioCtx = ctx;
  nextStartTime = 0;
  isPlaying.value = true;

  console.log("audio playback");

  if (ctx.state === 'suspended') {
    ctx.resume().then(() => loop(ctx)).catch((err) => {
      console.error("Could not resume audio context", err);
      stopRxStream();
    });
  } else {
    loop(ctx);
  }
}

function stopRxStream() {
  isPlaying.value = false;
  if (loopTimer !== null) {
    clearTimeout(loopTimer);
    loopTimer = null;
  }
  if (audioCtx) {
    const ctx = audioCtx;
    audioCtx = null;
    ctx.close().catch(() => {});
    console.log("Playback stopped");
  }
}


function toggleRxStream() {
  if (isPlaying.value) {
    stopRxStream()
  } else {
    playRxStream()
  }
}

onBeforeUnmount(() => {
  stopRxStream();
});

</script>

<template>

   <div class="card h-100">
    <div class="card-header">

      <strong>{{ $t('grid.components.audiostream') }}</strong>
    </div>
    <div class="card-body overflow-auto m-0" style="align-items: start">
 <button :class="isPlaying ? 'btn btn-sm btn-danger' : 'btn btn-sm btn-success'" @click="toggleRxStream">
            <i :class="isPlaying ? 'bi bi-stop-fill' : 'bi bi-play-fill'"/>&nbsp;
   {{isPlaying ? 'Stop' : 'Start'}}
          </button>

    </div>
  </div>


</template>
