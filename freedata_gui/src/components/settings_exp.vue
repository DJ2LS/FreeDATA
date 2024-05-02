<script setup lang="ts">
import { setConfig } from "../js/api";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings } from "../store/settingsStore.js";
</script>

<template>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Enable MESH protocol</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline ms-2">
        <input
          class="form-check-input"
          type="checkbox"
          id="enableMeshSwitch"
          @change="setConfig"
          v-model="settings.remote.MESH.enable_protocol"
          disabled
        />
        <label class="form-check-label" for="enableMeshSwitch"
          >experimental! REALLY!</label
        >
      </div>
    </label>
  </div>
  <div class="center">
    <div class="badge text-bg-danger">
      <i class="bi bi-shield-exclamation"></i> These options may not work and
      are for experienced users only!
    </div>
  </div>
</template>
