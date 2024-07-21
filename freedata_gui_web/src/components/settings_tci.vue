<template>
  <div>
    <hr class="m-2" />

    <!-- TCI IP Address Input -->
    <div class="input-group input-group-sm mb-1">
      <span class="input-group-text" style="width: 180px">TCI IP Address</span>
      <input
        type="text"
        class="form-control"
        placeholder="TCI IP"
        id="rigcontrol_tci_ip"
        aria-label="Device IP"
        @change="onChange"
        v-model="settings.remote.TCI.tci_ip"
      />
    </div>

    <!-- TCI Port Input -->
    <div class="input-group input-group-sm mb-1">
      <span class="input-group-text" style="width: 180px">TCI port</span>
      <input
        type="text"
        class="form-control"
        placeholder="TCI port"
        id="rigcontrol_tci_port"
        aria-label="Device Port"
        @change="onChange"
        v-model="settings.remote.TCI.tci_port"
      />
    </div>
  </div>
</template>

<script>
import { settingsStore } from "../store/settingsStore.js";
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
