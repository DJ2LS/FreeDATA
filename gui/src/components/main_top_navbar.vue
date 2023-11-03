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

import { saveSettingsToFile } from "../js/settingsHandler";

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
    </div>
	 </nav>
</template>
