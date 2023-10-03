<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

function saveSettings() {
  saveSettingsToFile();
}
</script>

<template>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Explorer publishing</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="ExplorerSwitch"
          @change="saveSettings"
          v-model="settings.enable_explorer"
          true-value="True"
          false-value="False"
        />
        <label class="form-check-label" for="ExplorerSwitch">Publish</label>
      </div>
    </label>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Explorer stats publishing</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="ExplorerStatsSwitch"
          @change="saveSettings"
          v-model="settings.enable_stats"
          true-value="True"
          false-value="False"
        />
        <label class="form-check-label" for="ExplorerStatsSwitch"
          >Publish stats</label
        >
      </div>
    </label>
  </div>
</template>
