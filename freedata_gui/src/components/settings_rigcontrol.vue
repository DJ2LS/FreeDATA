<template>
  <!-- Top Info Area for Rig Control Settings -->
  <div
    class="alert alert-info"
    role="alert"
  >
    <strong><i class="bi bi-gear-wide-connected me-1" /></strong>{{ $t('settings.radio.introduction') }}
  </div>

  <div
    class="alert alert-warning"
    role="alert"
  >
    {{ $t('settings.radio.info') }}
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
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <select
      id="rigcontrol_radiocontrol"
      v-model="settings.remote.RADIO.control"
      class="form-select form-select-sm w-50"
      @change="onChange"
    >
      <option value="disabled">
        Disabled / VOX (no rig control - use with VOX)
      </option>
      <option value="serial_ptt">
        Serial PTT via DTR/RTS
      </option>
      <option value="rigctld">
        Rigctld (external Hamlib)
      </option>
      <option value="rigctld_bundle">
        Rigctld (internal Hamlib)
      </option>
      <option value="flrig">
        flrig
      </option>
    </select>
  </div>


  <hr class="m-2">

  <!-- Tab Navigation -->
  <nav>
    <div
      id="nav-tab"
      class="nav nav-tabs"
      role="tablist"
    >
      <button
        id="nav-hamlib-tab"
        class="nav-link active"
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
        id="nav-serial-tab"
        class="nav-link"
        data-bs-toggle="tab"
        data-bs-target="#nav-serial"
        type="button"
        role="tab"
        aria-controls="nav-serial"
        aria-selected="false"
      >
        {{ $t('settings.radio.tabserial') }}
      </button>

      <button
        id="nav-flrig-tab"
        class="nav-link"
        data-bs-toggle="tab"
        data-bs-target="#nav-flrig"
        type="button"
        role="tab"
        aria-controls="nav-flrig"
        aria-selected="false"
      >
        {{ $t('settings.radio.tabflrig') }}
      </button>
    </div>
  </nav>

  <!-- Tab Content -->
  <div
    id="nav-tabContent"
    class="tab-content mt-2"
  >
    <!-- Hamlib Settings -->
    <div
      id="nav-hamlib"
      class="tab-pane fade show active"
      role="tabpanel"
      aria-labelledby="nav-hamlib-tab"
      tabindex="0"
    >
      <settings_hamlib />
    </div>

    <!-- Serial PTT Settings -->
    <div
      id="nav-serial"
      class="tab-pane fade"
      role="tabpanel"
      aria-labelledby="nav-serial-tab"
      tabindex="2"
    >
      <settings_serial_ptt />
    </div>

    <!-- Flrig settings -->
    <div
      id="nav-flrig"
      class="tab-pane fade"
      role="tabpanel"
      aria-labelledby="nav-flrig-tab"
      tabindex="2"
    >
      <settings_flrig />
    </div>


  </div>

  <hr class="m-2">
</template>

<script>
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import settings_hamlib from "./settings_hamlib.vue";
import settings_serial_ptt from "./settings_serial_ptt.vue";
import settings_flrig from "./settings_flrig.vue";

export default {
  components: {
    settings_hamlib,
    settings_serial_ptt,
    settings_flrig
  },
  computed: {
    settings() {
      return settings;
    }
  },
  methods: {
    onChange
  }
};
</script>
