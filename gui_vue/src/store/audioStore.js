import { defineStore } from "pinia";
import { ref, computed } from "vue";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

export const useAudioStore = defineStore("audioStore", () => {
  var inputDevices = ref([{ id: 0, name: "no input devices" }]);
  var outputDevices = ref([{ id: 0, name: "no output devices" }]);

  var startupInputDevice = ref(0)
  var startupOutputDevice = ref(0)


  function getInputDevices() {
    var html = "";
    for (var key in inputDevices.value) {

      let selected = ''
      if (inputDevices.value[key]["name"] == settings.rx_audio){
        selected = "selected"
      } else {
       selected = ''
      }

      html += `<option value=${inputDevices.value[key]["id"]} ${selected}>${inputDevices.value[key]["name"]}</option>`;
    }
    return html;
  }

  function getOutputDevices() {
    var html = "";
    for (var key in outputDevices.value) {

      let selected = ''
      if (outputDevices.value[key]["name"] == settings.tx_audio){
        selected = "selected"
      } else {
       selected = ''
      }
      html += `<option value=${outputDevices.value[key]["id"]} ${selected}>${outputDevices.value[key]["name"]}</option>`;
    }
    return html;
  }

  return { inputDevices, outputDevices, getInputDevices, getOutputDevices, startupInputDevice, startupOutputDevice };
});
