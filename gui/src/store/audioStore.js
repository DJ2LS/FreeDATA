import { defineStore } from "pinia";
import { getAudioDevices } from "../js/api";
import { ref } from "vue";


// Define skel fallback data
const skel = [{
  "api": "ERR",
  "id": "0000",
  "name": "No devices received from modem",
  "native_index": 0
}];

export const useAudioStore = defineStore("audioStore", () => {
  const audioInputs = ref([]);
  const audioOutputs = ref([]);

  const loadAudioDevices = async () => {
    try {
      const devices = await getAudioDevices();
      // Check if devices are valid and have entries, otherwise use skel
      audioInputs.value = devices && devices.in.length > 0 ? devices.in : skel;
      audioOutputs.value = devices && devices.out.length > 0 ? devices.out : skel;
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
  };
});