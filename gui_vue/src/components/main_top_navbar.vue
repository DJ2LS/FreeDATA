<script setup lang="ts">

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import { useAudioStore } from "../store/audioStore.js";
const audioStore = useAudioStore(pinia);

import { startModem, stopModem } from "../js/daemon.js";
import { saveSettingsToFile } from "../js/settingsHandler";

function startStopModem() {
  switch (state.modem_running_state) {
    case "stopped":

      let startupInputDeviceValue = parseInt((<HTMLSelectElement>document.getElementById("audio_input_selectbox")).value);
      let startupOutputDeviceValue = parseInt((<HTMLSelectElement>document.getElementById("audio_output_selectbox")).value);

      let startupInputDeviceIndex = (<HTMLSelectElement>document.getElementById("audio_input_selectbox")).selectedIndex;
      let startupOutputDeviceIndex = (<HTMLSelectElement>document.getElementById("audio_output_selectbox")).selectedIndex;


      audioStore.startupInputDevice = startupInputDeviceValue
      audioStore.startupOutputDevice = startupOutputDeviceValue

      // get full name of audio device
      settings.rx_audio = (<HTMLSelectElement>document.getElementById("audio_input_selectbox")).options[startupInputDeviceIndex].text;
      settings.tx_audio = (<HTMLSelectElement>document.getElementById("audio_output_selectbox")).options[startupOutputDeviceIndex].text;


      saveSettingsToFile();

      startModem();

      break;
    case "running":
      stopModem();

      break;
    default:
  }
}
</script>

<template>
  <nav class="navbar bg-body-tertiary border-bottom">
    <div class="mx-auto">
      <span class="badge bg-secondary me-4"
        >Modem location | {{ settings.modem_host }}</span
      >

      <span class="badge bg-secondary me-4"
        >Service | {{ state.modem_running_state }}</span
      >

      <div class="btn-group" role="group"></div>
      <div class="btn-group me-4" role="group">
        <button
          type="button"
          id="startModem"
          class="btn btn-sm btn-outline-success"
          data-bs-toggle="tooltip"
          data-bs-trigger="hover"
          data-bs-html="false"
          title="Start the Modem. Please set your audio and radio settings first!"
          @click="startStopModem()"
          v-bind:class="{ disabled: state.modem_running_state === 'running' }"
        >
          <i class="bi bi-play-fill"></i>
          <span class="ms-2">start modem</span>
        </button>
        <button
          type="button"
          id="stopModem"
          class="btn btn-sm btn-outline-danger"
          data-bs-toggle="tooltip"
          data-bs-trigger="hover"
          data-bs-html="false"
          title="Stop the Modem."
          @click="startStopModem()"
          v-bind:class="{ disabled: state.modem_running_state === 'stopped' }"
        >
          <i class="bi bi-stop-fill"></i>
          <span class="ms-2">stop modem</span>
        </button>
      </div>

      <button
        type="button"
        id="openHelpModalStartStopModem"
        data-bs-toggle="modal"
        data-bs-target="#startStopModemHelpModal"
        class="btn me-4 p-0 border-0"
      >
        <i class="bi bi-question-circle" style="font-size: 1rem"></i>
      </button>
    </div>

    <!--
	<div class="btn-toolbar" role="toolbar">

<span data-bs-placement="bottom"  data-bs-toggle="tooltip" data-bs-trigger="hover" data-bs-html="false"
			title="View the received files. This is currently under development!">


	   <button class="btn btn-sm btn-primary me-2" data-bs-toggle="offcanvas" data-bs-target="#receivedFilesSidebar" id="openReceivedFiles" type="button" > <strong>Files </strong>
	   <i class="bi bi-file-earmark-arrow-up-fill" style="font-size: 1rem; color: white;"></i>
	   <i class="bi bi-file-earmark-arrow-down-fill" style="font-size: 1rem; color: white;"></i>
	   </button>
	   </span> <span data-bs-placement="bottom"  data-bs-toggle="tooltip" data-bs-trigger="hover" data-bs-html="false" title="Send files through HF. This is currently under development!">
	   <button class="btn btn-sm btn-primary me-2" id="openDataModule" data-bs-toggle="offcanvas" data-bs-target="#transmitFileSidebar" type="button" style="display: None;"> <strong>TX File </strong>
	   <i class="bi bi-file-earmark-arrow-up-fill" style="font-size: 1rem; color: white;"></i>
	   </button>

		</span> <span data-bs-placement="bottom"  data-bs-toggle="tooltip" data-bs-trigger="hover" data-bs-html="true"
			title="Settings and Info">

		</span>
	</div>
	 --></nav>
</template>
