<script setup>
import { setActivePinia } from 'pinia';
import pinia from '../../store/index';
setActivePinia(pinia);

import { useAudioStore } from '@/store/audioStore';
const audio = useAudioStore(pinia);

let audioCtx = null;
let isPlaying = false;

function playRxStream() {
  if (isPlaying) return;

  const SAMPLE_RATE = 8000;
  const BLOCK_SIZE = 600;
  const BLOCK_DURATION_MS = (BLOCK_SIZE / SAMPLE_RATE) * 1000;  // z. B. 75ms

  audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: SAMPLE_RATE });
  isPlaying = true;
  scheduledTime = audioCtx.currentTime;



  function loop() {
    if (!isPlaying) return;

    const block = audio.getNextBlock();

    if (block) {
      const float32 = Float32Array.from(block, s => s / 32768);
      const buffer = audioCtx.createBuffer(1, float32.length, SAMPLE_RATE);
      buffer.copyToChannel(float32, 0);

      const source = audioCtx.createBufferSource();
      source.buffer = buffer;
      source.connect(audioCtx.destination);

      const now = audioCtx.currentTime;
      const playAt = Math.max(now, scheduledTime);
      source.start(playAt);
      scheduledTime = playAt + buffer.duration;


    } else {
      console.warn("Buffer underrun");
    }

    setTimeout(loop, 4);  
  }

  if (audioCtx.state === 'suspended') {
    audioCtx.resume().then(loop);
  } else {
    loop();
  }
}

function stopRxStream() {
  if (audioCtx) {
    isPlaying = false;
    audioCtx.close();
    console.log("Playback stopped");
  }
}
</script>

<template>
  <button @click="playRxStream">Start Audio</button>
  <button @click="stopRxStream">Stop Audio</button>
</template>
