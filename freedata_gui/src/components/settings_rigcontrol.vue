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
      <option value="disabled">Disabled / VOX (no rig control - use with VOX)</option>
      <option value="serial_ptt">Serial PTT via DTR/RTS</option>
      <option value="rigctld">Rigctld (external Hamlib)</option>
      <option value="rigctld_bundle">Rigctld (internal Hamlib)</option>
      <option value="tci">TCI</option>
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
      <button
        class="nav-link"
        id="nav-profile-tab"
        data-bs-toggle="tab"
        data-bs-target="#nav-serial"
        type="button"
        role="tab"
        aria-controls="nav-serial"
        aria-selected="false"
      >
        Serial
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
      tabindex="1"
    >
      <settings_tci />
    </div>
    <div
      class="tab-pane fade"
      id="nav-serial"
      role="tabpanel"
      aria-labelledby="nav-serial-tab"
      tabindex="2"
    >
      <settings_serial_ptt />

    </div>
  </div>

  <hr class="m-2" />
</template>
<script>
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import settings_hamlib from "./settings_hamlib.vue";
import settings_tci from "./settings_tci.vue";
import settings_serial_ptt from "./settings_serial_ptt.vue";

export default {
  components: {
    settings_hamlib,
    settings_tci,
    settings_serial_ptt
  },
  methods: {
    onChange
  },
  computed: {
    settings() {
      return settings;
    }
  }
};
</script>
