<script setup>
import { setConfig } from "../js/api";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings } from "../store/settingsStore.js";
</script>

<template>
  <!-- Top Warning Area -->
  <div class="alert alert-danger" role="alert">
    <strong><i class="bi bi-shield-exclamation me-1"></i>WARNING:</strong> These features may be incomplete. They are for <u>experienced</u> users ONLY!
  </div>

  <!-- Enable MESH Protocol -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Enable MESH protocol
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Experimental feature"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
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
        <label class="form-check-label" for="enableMeshSwitch">Enable</label>
      </div>
    </label>
  </div>
</template>

