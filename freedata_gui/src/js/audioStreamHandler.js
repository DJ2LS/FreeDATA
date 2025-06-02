import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useAudioStore } from "../store/audioStore.js";
const audio = useAudioStore(pinia);

export function addDataToAudio(data) {
    const int16 = new Int16Array(data);  // ArrayBuffer → Int16 PCM
    const copied = new Int16Array(int16);
    audio.rxStream.push(copied);
}
