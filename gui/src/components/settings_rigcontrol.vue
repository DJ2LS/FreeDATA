<script setup lang="ts">
import { saveSettings } from "../js/settingsHandler";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);
</script>

<template>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Rig Control</span>

    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="rigcontrol_radiocontrol"
      @change="saveSettings"
      v-model="settings.radiocontrol"
    >
      <option selected value="disabled">
        Disabled / VOX (no rig control - use with VOX)
      </option>
      <option selected value="rigctld">Rigctld (Hamlib)</option>
      <option selected value="tci">TCI</option>
    </select>
  </div>

  <hr class="m-2" />

  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">TCI IP Address</span>
    <input
      type="text"
      class="form-control"
      placeholder="TCI IP"
      id="rigcontrol_tci_ip"
      aria-label="Device IP"
      v-model="settings.tci_ip"
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
      v-model="settings.tci_port"
    />
  </div>
</template>
