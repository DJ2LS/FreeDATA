<template>

    <div class="alert alert-warning" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i></strong> {{ $t('settings.radio.tciinfo') }}
  </div>

  <!-- TCI IP Address Input -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.radio.tcihost') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.radio.tcihost_help')"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <input
      type="text"
      class="form-control"
      placeholder="Enter TCI IP Address"
      id="tciIpAddress"
      aria-label="TCI IP Address"
      @change="onChange"
      v-model="settings.remote.TCI.tci_ip"
    />
  </div>

  <!-- TCI Port Input -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.radio.tciport') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.radio.tciport_help')"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <input
      type="text"
      class="form-control"
      placeholder="Enter TCI Port"
      id="tciPort"
      aria-label="TCI Port"
      @change="onChange"
      v-model="settings.remote.TCI.tci_port"
    />
  </div>
</template>



<script>
import { settingsStore as settings, onChange } from "../store/settingsStore.js";

export default {
  data() {
    return {
      settings
    };
  },
  methods: {
    onChange(event) {
      // Handle the change event here
      onChange(event);
    }
  }
};
</script>
