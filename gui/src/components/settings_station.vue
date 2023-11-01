<script setup lang="ts">
import { saveSettingsToFile } from "../js/settingsHandler";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import main_my_station from "./main_my_station.vue";
import main_updater from "./main_updater.vue";
import main_rig_control from "./main_rig_control.vue";

function saveSettings() {
  saveSettingsToFile();
}
</script>

<template>
  <main_my_station />
  <main_updater />
  <main_rig_control />
</template>
