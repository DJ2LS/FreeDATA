<script setup lang="ts">
import { saveSettingsToFile } from "../js/settingsHandler";

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
    <label class="input-group-text w-50">Enable autotune</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline ms-2">
        <input
          class="form-check-input"
          type="checkbox"
          id="autoTuneSwitch"
          @change="saveSettings"
          v-model="settings.auto_tune"
          true-value="True"
          false-value="False"
        />
        <label class="form-check-label" for="autoTuneSwitch"
          >adjust ALC on TX</label
        >
      </div>
    </label>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Enable FSK mode</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline ms-2">
        <input
          class="form-check-input"
          type="checkbox"
          id="fskModeSwitch"
          @change="saveSettings"
          v-model="settings.enable_fsk"
          true-value="True"
          false-value="False"
        />
        <label class="form-check-label" for="fskModeSwitch"
          >not available, yet</label
        >
      </div>
    </label>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Enable MESH protocol</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline ms-2">
        <input
          class="form-check-input"
          type="checkbox"
          id="enableMeshSwitch"
          @change="saveSettings"
          v-model="settings.enable_mesh_features"
          true-value="True"
          false-value="False"
        />
        <label class="form-check-label" for="enableMeshSwitch"
          >experimental! REALLY!</label
        >
      </div>
    </label>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Database maintenance</label>
    <label class="input-group-text w-50">
      <button
        class="btn btn-outline-secondary btn-sm w-50"
        id="btnCleanDB"
        type="button"
      >
        Clean</button
      >&nbsp;
      <div
        class="spinner-border text-warning invisible"
        role="status"
        id="divCleanDBSpinner"
      ></div>
    </label>
  </div>
  <div class="center">
    <div class="badge text-bg-danger">
      <i class="bi bi-shield-exclamation"></i> These options may not work and
      are for experienced users only!
    </div>
  </div>
</template>
