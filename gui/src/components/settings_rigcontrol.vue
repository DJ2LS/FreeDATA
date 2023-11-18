<script setup lang="ts">
import { settingsStore as settings } from "../store/settingsStore.js";
import { handleFieldValueChange } from "../js/settingsHandler";
</script>

<template>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Rig Control</span>

    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="rigcontrol_radiocontrol"
      @change="handleFieldValueChange"
      data-section="RADIO"
      data-setting="radiocontrol"
      v-model="settings.remote.RADIO.radiocontrol"
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
      @change="handleFieldValueChange"
      data-section="TCI"
      data-setting="tci_ip"
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
      @change="handleFieldValueChange"
      data-section="TCI"
      data-setting="tci_port"
      v-model="settings.remote.TCI.tci_port"
    />
  </div>
</template>
