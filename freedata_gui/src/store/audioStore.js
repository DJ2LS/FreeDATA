import { defineStore } from "pinia";
import { getAudioDevices } from "../js/api";
import { ref } from "vue";

// Define skel fallback data
const skel = [
  {
    api: "ERR",
    id: "0000",
    name: "No devices received from modem",
    native_index: 0,
  },
];

export const useAudioStore = defineStore("audioStore", () => {
  const audioInputs = ref([]);
  const audioOutputs = ref([]);
  const rxStream = ref([]);

  const BUFFER_SIZE = 1024;
  const rxStreamBuffer = new Array(BUFFER_SIZE).fill(null);

  let writePtr = 0;
  let readPtr = 0;
  let readyBlocks = 0;

  function addBlock(block) {
    rxStreamBuffer[writePtr] = block;
    writePtr = (writePtr + 1) % BUFFER_SIZE;

    if (readyBlocks < BUFFER_SIZE) {
      readyBlocks++;
    } else {
      readPtr = (readPtr + 1) % BUFFER_SIZE;
    }
  }

  function getNextBlock() {
    if (readyBlocks === 0) return null;

    const block = rxStreamBuffer[readPtr];
    readPtr = (readPtr + 1) % BUFFER_SIZE;
    readyBlocks--;
    return block;
  }

  function resetBuffer() {
    writePtr = 0;
    readPtr = 0;
    readyBlocks = 0;
    for (let i = 0; i < BUFFER_SIZE; i++) {
      rxStreamBuffer[i] = null;
    }
  }

  




  const loadAudioDevices = async () => {
    try {
      const devices = await getAudioDevices();
      // Check if devices are valid and have entries, otherwise use skel
      audioInputs.value = devices && devices.in.length > 0 ? devices.in : skel;
      audioOutputs.value =
        devices && devices.out.length > 0 ? devices.out : skel;
    } catch (error) {
      console.error("Failed to load audio devices:", error);
      // Use skel as fallback in case of error
      audioInputs.value = skel;
      audioOutputs.value = skel;
    }
  };

  return {
    audioInputs,
    audioOutputs,
    loadAudioDevices,
    rxStream,
    addBlock,
    getNextBlock,
    resetBuffer,
    get bufferedBlockCount() {
      return readyBlocks;
    }, 
    
  };
});
