<script setup lang="ts">
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
</script>

<template>
  <hr class="m-2" />

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
</template>
