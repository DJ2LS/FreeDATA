import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useAudioStore } from "../store/audioStore.js";
const audio = useAudioStore(pinia);

const MAX_BLOCKS = 10;

export function addDataToAudio(data) {
  const int16 = new Int16Array(data);
  const copy = new Int16Array(int16);  // Kopie für Sicherheit

  const stream = audio.rxStream;

  if (stream.length >= MAX_BLOCKS) {
    stream.shift();
  }

  stream.push(copy);
}
