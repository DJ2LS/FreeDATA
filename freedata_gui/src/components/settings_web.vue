<script setup>

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings, onChange } from "../store/settingsStore.js";
</script>

<template>
  <!-- Top Info Area for Explorer Settings -->
  <div class="alert alert-info" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i>Explorer</strong> related settings, including enabling <strong>Explorer publishing</strong> and <strong>Explorer stats publishing</strong>.
  </div>

  <!-- Explorer Publishing -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Explorer publishing
      <span id="explorerPublishingHelp" class="ms-2 badge bg-secondary text-wrap">
        Share your station's data with the Explorer network
      </span>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="ExplorerSwitch"
          aria-describedby="explorerPublishingHelp"
          @change="onChange"
          v-model="settings.remote.STATION.enable_explorer"
        />
        <label class="form-check-label" for="ExplorerSwitch">Enable</label>
      </div>
    </label>
  </div>

  <!-- Explorer Stats Publishing -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Explorer stats publishing
      <span id="explorerStatsPublishingHelp" class="ms-2 badge bg-secondary text-wrap">
        Share your station's statistics with the Explorer network
      </span>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="ExplorerStatsSwitch"
          aria-describedby="explorerStatsPublishingHelp"
          @change="onChange"
          v-model="settings.remote.STATION.enable_stats"
        />
        <label class="form-check-label" for="ExplorerStatsSwitch">Enable</label>
      </div>
    </label>
  </div>
</template>

