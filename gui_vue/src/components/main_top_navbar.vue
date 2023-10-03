<script setup lang="ts">
import { saveSettingsToFile } from "../js/settingsHandler";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import { startTNC, stopTNC } from "../js/daemon.js";

function startStopTNC() {
  switch (state.tnc_running_state) {
    case "stopped":
      // todo: is there another way of doing this, maybe more VueJS like?
      settings.rx_audio = document.getElementById(
        "audio_input_selectbox",
      ).value;
      settings.tx_audio = document.getElementById(
        "audio_output_selectbox",
      ).value;

      startTNC();

      break;
    case "running":
      stopTNC();

      break;
    default:
  }
}
</script>

<template>
  <nav class="navbar bg-body-tertiary border-bottom">
    <div class="mx-auto">
      <span class="badge bg-secondary me-4"
        >TNC location | {{ settings.tnc_host }}</span
      >

      <span class="badge bg-secondary me-4"
        >Service | {{ state.tnc_running_state }}</span
      >

      <div class="btn-group" role="group"></div>
      <div class="btn-group me-4" role="group">
        <button
          type="button"
          id="startTNC"
          class="btn btn-sm btn-outline-success"
          data-bs-toggle="tooltip"
          data-bs-trigger="hover"
          data-bs-html="false"
          title="Start the TNC. Please set your audio and radio settings first!"
          @click="startStopTNC()"
          v-bind:class="{ disabled: state.tnc_running_state === 'running' }"
        >
          <i class="bi bi-play-fill"></i>
          <span class="ms-2">start tnc</span>
        </button>
        <button
          type="button"
          id="stopTNC"
          class="btn btn-sm btn-outline-danger"
          data-bs-toggle="tooltip"
          data-bs-trigger="hover"
          data-bs-html="false"
          title="Stop the TNC."
          @click="startStopTNC()"
          v-bind:class="{ disabled: state.tnc_running_state === 'stopped' }"
        >
          <i class="bi bi-stop-fill"></i>
          <span class="ms-2">stop tnc</span>
        </button>
      </div>

      <button
        type="button"
        id="openHelpModalStartStopTNC"
        data-bs-toggle="modal"
        data-bs-target="#startStopTNCHelpModal"
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
