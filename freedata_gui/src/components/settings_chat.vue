<script>
import { settingsStore as settings, onChange, getRemote } from "../store/settingsStore.js";
import { setActivePinia } from "pinia";
import pinia from "../store/index";

// Set the active Pinia store
setActivePinia(pinia);

// Export methods and computed properties for use in the template
export default {
  data() {
    return {
      showWavelogApiKey: false,
    };
  },
  computed: {
    settings() {
      return settings;
    },
  },
  created() {
    // Not reactive on purpose: values remembered on focus of number inputs
    this.previousNumbers = {};
  },
  methods: {
    onChange,
    rememberNumber(section, key) {
      this.previousNumbers[`${section}.${key}`] = settings.remote[section][key];
    },
    // Number inputs: v-model.number yields "" when a field is cleared, which the
    // server rejects (it expects an int). Restore the previous value instead of
    // saving, round to an integer and clamp to the input's min/max before saving.
    onNumberChange(event, section, key) {
      const el = event.target;
      let value = settings.remote[section][key];
      if (typeof value !== "number" || !Number.isFinite(value)) {
        const previous = this.previousNumbers[`${section}.${key}`];
        if (previous !== "" && previous !== null && previous !== undefined && Number.isFinite(Number(previous))) {
          settings.remote[section][key] = Number(previous);
        } else {
          getRemote(); // reload the last saved config from the server
        }
        return;
      }
      value = Math.round(value);
      if (el.min !== "" && value < Number(el.min)) value = Number(el.min);
      if (el.max !== "" && value > Number(el.max)) value = Number(el.max);
      settings.remote[section][key] = value;
      this.previousNumbers[`${section}.${key}`] = value;
      onChange();
    },
  },
};
</script>

<template>
  <!-- Top Info Area for Messages Settings -->
  <div
    class="alert alert-info"
    role="alert"
  >
    <strong><i class="bi bi-gear-wide-connected me-1" /></strong> {{ $t('settings.chat.introduction') }}
  </div>

  <!-- Enable Message Auto Repeat -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.chat.enablemessageautorepeat') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.chat.enablemessageautorepeat_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline ms-2">
        <input
          id="enableMessagesAutoRepeatSwitch"
          v-model="settings.remote.MESSAGES.enable_auto_repeat"
          class="form-check-input"
          type="checkbox"
          @change="onChange"
        >
        <label
          class="form-check-label"
          for="enableMessagesAutoRepeatSwitch"
        >{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>

  <!-- Enable ADIF export -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.chat.enableadifloggingudp') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.chat.enableadifloggingudp_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline ms-2">
        <input
          id="enableADIFSwitch"
          v-model="settings.remote.QSO_LOGGING.enable_adif_udp"
          class="form-check-input"
          type="checkbox"
          @change="onChange"
        >
        <label
          class="form-check-label"
          for="enableADIFSwitch"
        >{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>

  <!-- ADIF Log Host -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.chat.adifloggingudphost') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.chat.adifloggingudphost_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <input
      id="adifLogHost"
      v-model="settings.remote.QSO_LOGGING.adif_udp_host"
      type="text"
      class="form-control"
      :placeholder="$t('settings.chat.adifloggingudphost_placeholder')"
      @change="onChange"
    >
  </div>

  <!-- ADIF Log Port -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.chat.adifloggingudpport') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title=" $t('settings.chat.adifloggingudpport_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <input
      id="adifLogPort"
      v-model.number="settings.remote.QSO_LOGGING.adif_udp_port"
      type="number"
      class="form-control"
      :placeholder=" $t('settings.chat.adifloggingudpport_placeholder')"
      max="65534"
      min="1025"
      @focus="rememberNumber('QSO_LOGGING', 'adif_udp_port')"
      @change="onNumberChange($event, 'QSO_LOGGING', 'adif_udp_port')"
    >
  </div>

  <!-- Enable Wavelog API -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">

      {{ $t('settings.chat.adifloggingwavelog') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.chat.enableadifloggingwavelog_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline ms-2">
        <input
          id="enableWavelogSwitch"
          v-model="settings.remote.QSO_LOGGING.enable_adif_wavelog"
          class="form-check-input"
          type="checkbox"
          @change="onChange"
        >
        <label
          class="form-check-label"
          for="enableWavelogSwitch"
        >{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>

  <!-- Wavelog Host -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.chat.adifloggingwaveloghost') }}

      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.chat.adifloggingwaveloghost_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <input
      id="wavelogHost"
      v-model="settings.remote.QSO_LOGGING.adif_wavelog_host"
      type="text"
      class="form-control"
      :placeholder="$t('settings.chat.adifloggingwaveloghost_placeholder')"
      @change="onChange"
    >
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.chat.adifloggingwavelogapi') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.chat.adifloggingwavelogapi_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <input
      id="wavelogApiKey"
      v-model="settings.remote.QSO_LOGGING.adif_wavelog_api_key"
      :type="showWavelogApiKey ? 'text' : 'password'"
      class="form-control"
      :placeholder="$t('settings.chat.adifloggingwavelogapi_placeholder')"
      autocomplete="off"
      @change="onChange"
    >
    <button
      type="button"
      class="btn btn-outline-secondary"
      :aria-label="showWavelogApiKey ? 'Hide API key' : 'Show API key'"
      @click="showWavelogApiKey = !showWavelogApiKey"
    >
      <i :class="showWavelogApiKey ? 'bi bi-eye-slash' : 'bi bi-eye'" />
    </button>
  </div>
</template>

