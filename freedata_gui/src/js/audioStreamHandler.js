import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useAudioStore } from "../store/audioStore.js";
const audio = useAudioStore(pinia);

// Server sends int16 mono PCM (8 kHz). Any number of samples is accepted.
export function addDataToAudio(data) {
  if (!(data instanceof ArrayBuffer)) return;
  // Drop a trailing odd byte instead of letting Int16Array throw a RangeError
  const sampleCount = Math.floor(data.byteLength / 2);
  if (sampleCount === 0) return;
  // slice() copies, so the block does not share memory with the socket buffer
  const copy = new Int16Array(data.slice(0, sampleCount * 2));
  audio.addBlock(copy);
}
