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

  console.log("Start Playback");
  audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 8000 });
  isPlaying = true;

  if (audioCtx.state === 'suspended') {
    audioCtx.resume().then(() => {
      console.log("AudioContext resumed");
    });
  }

  //const BLOCK_DURATION_MS = 1024 / 8000 * 1000;
  const BLOCK_DURATION_MS = 10
  const MIN_BLOCKS_TO_START = 5
  function loop() {
    if (!isPlaying) return;
    if (audio.rxStream.length < MIN_BLOCKS_TO_START){
      setTimeout(loop, 5);
      return;
    }
    if (audio.rxStream.length > 0) {
      const block = audio.rxStream.shift();  // Nächstes Audioblock holen
      const float32 = Float32Array.from(block, s => s / 32768);
      const buffer = audioCtx.createBuffer(1, float32.length, 8000);
      buffer.copyToChannel(float32, 0);

      const source = audioCtx.createBufferSource();
      source.buffer = buffer;
      source.connect(audioCtx.destination);
      source.start();
    } else {
      console.log("Buffer empty, waiting...");
    }
    setTimeout(loop, BLOCK_DURATION_MS);
  }

  loop();
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
