import { defineStore } from "pinia";
import { ref, computed } from "vue";

export const useAudioStore = defineStore("audioStore", () => {
  var inputDevices = ref([{ id: 0, name: "no input devices" }]);
  var outputDevices = ref([{ id: 0, name: "no output devices" }]);

  function getInputDevices() {
    var html = "";
    for (var key in inputDevices.value) {
      html += `<option value=${inputDevices.value[key]["id"]}>${inputDevices.value[key]["name"]}</option>`;
    }
    return html;
  }

  function getOutputDevices() {
    var html = "";
    for (var key in outputDevices.value) {
      html += `<option value="${outputDevices.value[key]["id"]}">${outputDevices.value[key]["name"]}</option>`;
    }
    return html;
  }

  return { inputDevices, outputDevices, getInputDevices, getOutputDevices };
});
