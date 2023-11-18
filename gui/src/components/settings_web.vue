<script setup lang="ts">
import { saveModemConfig } from "../js/api";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings} from "../store/settingsStore.js";

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
          @change="saveModemConfig"
          v-model="settings.enable_explorer"
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
          @change="saveModemConfig"
          v-model="settings.explorer_stats"
        />
        <label class="form-check-label" for="ExplorerStatsSwitch"
          >Publish stats</label
        >
      </div>
    </label>
  </div>
</template>
