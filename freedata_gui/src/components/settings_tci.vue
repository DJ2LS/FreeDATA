<template>

    <div class="alert alert-warning" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i>TCI</strong> is currently broken. Re-Implementation is a work in progress.
  </div>

  <!-- TCI IP Address Input -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      TCI IP Address
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Enter the IP address of your TCI device"
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
      TCI Port
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Enter the port number for TCI communication"
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
