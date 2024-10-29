<template>

  <!-- TCI IP Address Input -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      TCI IP Address
      <span id="tciIpHelp" class="ms-2 badge bg-secondary text-wrap">
        Enter the IP address of your TCI device
      </span>
    </label>
    <input
      type="text"
      class="form-control"
      placeholder="Enter TCI IP Address"
      id="tciIpAddress"
      aria-label="TCI IP Address"
      aria-describedby="tciIpHelp"
      @change="onChange"
      v-model="settings.remote.TCI.tci_ip"
    />
  </div>

  <!-- TCI Port Input -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      TCI Port
      <span id="tciPortHelp" class="ms-2 badge bg-secondary text-wrap">
        Enter the port number for TCI communication
      </span>
    </label>
    <input
      type="text"
      class="form-control"
      placeholder="Enter TCI Port"
      id="tciPort"
      aria-label="TCI Port"
      aria-describedby="tciPortHelp"
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
