<script>
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { setActivePinia } from "pinia";
import pinia from "../store/index";

// Set the active Pinia store
setActivePinia(pinia);

// Export methods and computed properties for use in the template
export default {
  computed: {
    settings() {
      return settings;
    },
  },
  methods: {
    onChange,
  },
};
</script>

<template>
  <!-- Top Warning Area -->
  <div
    class="alert alert-danger"
    role="alert"
  >
    <strong><i class="bi bi-shield-exclamation me-1" /></strong> {{ $t('settings.exp.introduction') }}
  </div>


  <div
    class="alert alert-info d-none"
    role="alert"
  >
    <strong><i class="bi bi-info-circle me-1" /></strong>{{ $t('settings.exp.info') }}
  </div>

  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">

      {{ $t('settings.exp.enableringbuffer') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.exp.enableringbuffer_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          id="enable_ring_bufferSwitch"
          v-model="settings.remote.EXP.enable_ring_buffer"
          class="form-check-input"
          type="checkbox"
          @change="onChange"
        >
        <label
          class="form-check-label"
          for="enable_ring_bufferSwitch"
        >{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>

  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">

      {{ $t('settings.exp.enablevhf') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.exp.enablevhf_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          id="enable_vhfSwitch"
          v-model="settings.remote.EXP.enable_vhf"
          class="form-check-input"
          type="checkbox"
          @change="onChange"
        >
        <label
          class="form-check-label"
          for="enable_vhfSwitch"
        >{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>

</template>

