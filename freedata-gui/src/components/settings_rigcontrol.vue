<script setup lang="ts">
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import settings_hamlib from "./settings_hamlib.vue";
import settings_tci from "./settings_tci.vue";
</script>

<template>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Rig Control</span>

    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="rigcontrol_radiocontrol"
      @change="onChange"
      v-model="settings.remote.RADIO.control"
    >
      <option selected value="disabled">
        Disabled / VOX (no rig control - use with VOX)
      </option>
      <option selected value="rigctld">Rigctld (external Hamlib)</option>
      <option selected value="rigctld_bundle">Rigctld (internal Hamlib)</option>
      <option selected value="tci">TCI</option>
    </select>
  </div>

  <hr class="m-2" />

  <nav>
    <div class="nav nav-tabs" id="nav-tab" role="tablist">
      <button
        class="nav-link active"
        id="nav-home-tab"
        data-bs-toggle="tab"
        data-bs-target="#nav-hamlib"
        type="button"
        role="tab"
        aria-controls="nav-home"
        aria-selected="true"
      >
        Hamlib
      </button>
      <button
        class="nav-link"
        id="nav-profile-tab"
        data-bs-toggle="tab"
        data-bs-target="#nav-tci"
        type="button"
        role="tab"
        aria-controls="nav-profile"
        aria-selected="false"
      >
        TCI
      </button>
    </div>
  </nav>
  <div class="tab-content" id="nav-tabContent">
    <div
      class="tab-pane fade show active"
      id="nav-hamlib"
      role="tabpanel"
      aria-labelledby="nav-hamlib-tab"
      tabindex="0"
    >
      <settings_hamlib />
    </div>
    <div
      class="tab-pane fade"
      id="nav-tci"
      role="tabpanel"
      aria-labelledby="nav-tci-tab"
      tabindex="0"
    >
      <settings_tci />
    </div>
  </div>

  <hr class="m-2" />
</template>
