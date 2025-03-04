<template>
  <!-- Top Info Area for Rig Control Settings -->
  <div class="alert alert-info" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i></strong>{{ $t('settings.radio.introduction') }}
  </div>

    <div class="alert alert-warning" role="alert">
    {{ $t('settings.radio.introduction') }}
  </div>


  <!-- Rig Control Selection -->
<div class="input-group mb-1">
  <label class="input-group-text w-50 text-wrap">
    {{ $t('settings.radio.rigcontroltype') }}
    <button
      type="button"
      class="btn btn-link p-0 ms-2"
      data-bs-toggle="tooltip"
      :title="$t('settings.radio.rigcontroltype_help')"
    >
      <i class="bi bi-question-circle"></i>
    </button>
  </label>
  <select
    class="form-select form-select-sm w-50"
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

  <!-- Tab Navigation -->
  <nav>
    <div class="nav nav-tabs" id="nav-tab" role="tablist">
      <button
        class="nav-link active"
        id="nav-hamlib-tab"
        data-bs-toggle="tab"
        data-bs-target="#nav-hamlib"
        type="button"
        role="tab"
        aria-controls="nav-hamlib"
        aria-selected="true"
      >
        {{ $t('settings.radio.tabhamlib') }}
      </button>
      <button
        class="nav-link"
        id="nav-tci-tab"
        data-bs-toggle="tab"
        data-bs-target="#nav-tci"
        type="button"
        role="tab"
        aria-controls="nav-tci"
        aria-selected="false"
      >
        {{ $t('settings.radio.tabtci') }}
      </button>
      <button
        class="nav-link"
        id="nav-serial-tab"
        data-bs-toggle="tab"
        data-bs-target="#nav-serial"
        type="button"
        role="tab"
        aria-controls="nav-serial"
        aria-selected="false"
      >
        {{ $t('settings.radio.tabserial') }}
      </button>
    </div>
  </nav>

  <!-- Tab Content -->
  <div class="tab-content mt-2" id="nav-tabContent">
    <!-- Hamlib Settings -->
    <div
      class="tab-pane fade show active"
      id="nav-hamlib"
      role="tabpanel"
      aria-labelledby="nav-hamlib-tab"
      tabindex="0"
    >
      <settings_hamlib />
    </div>

    <!-- TCI Settings -->
    <div
      class="tab-pane fade"
      id="nav-tci"
      role="tabpanel"
      aria-labelledby="nav-tci-tab"
      tabindex="1"
    >
      <settings_tci />
    </div>

    <!-- Serial PTT Settings -->
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
