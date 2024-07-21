<script setup>

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings, onChange } from "../store/settingsStore.js";
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
          @change="onChange"
          v-model="settings.remote.STATION.enable_explorer"
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
          @change="onChange"
          v-model="settings.remote.STATION.enable_stats"
          disabled
        />
        <label class="form-check-label" for="ExplorerStatsSwitch">Publish stats</label>
      </div>
    </label>
  </div>
</template>
