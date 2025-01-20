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
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Share your station's data with the Explorer network"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="ExplorerSwitch"
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
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Share your station's statistics with the Explorer network"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="ExplorerStatsSwitch"
          @change="onChange"
          v-model="settings.remote.STATION.enable_stats"
        />
        <label class="form-check-label" for="ExplorerStatsSwitch">Enable</label>
      </div>
    </label>
  </div>
</template>


