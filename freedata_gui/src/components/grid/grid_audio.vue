<script setup>
import { setActivePinia } from 'pinia';
import { ref } from 'vue';

import pinia from '../../store/index';
setActivePinia(pinia);

import { useAudioStore } from '@/store/audioStore';
const audio = useAudioStore(pinia);




var audioCtx = null;
var isPlaying = ref(false);

function playRxStream() {
  if (isPlaying.value) return;


  const SAMPLE_RATE = 8000;

  audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: SAMPLE_RATE });
  //let scheduledTime = audioCtx.currentTime;
  isPlaying.value = true;

  console.log("audio playback");

  function loop() {
    if (!isPlaying.value) return;

    const block = audio.getNextBlock();
    if (block) {
      const float32 = Float32Array.from(block, s => s / 32768);
      const buffer = audioCtx.createBuffer(1, float32.length, SAMPLE_RATE);
      buffer.copyToChannel(float32, 0);

      const source = audioCtx.createBufferSource();
      source.buffer = buffer;
      source.connect(audioCtx.destination);
      source.start(0);
    } else {
      //console.warn("⛔ Audio buffer underrun");
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
    isPlaying.value = false;
    audioCtx.close();
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
