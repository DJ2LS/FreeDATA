<script>
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { setActivePinia } from "pinia";
import pinia from "../store/index";

// Set the active Pinia store
setActivePinia(pinia);

// Export methods and computed properties for use in the template
export default {
  computed: {
    settings() {
      return settings;
    },
  },
  methods: {
    onChange,
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
      @change="onChange"
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
      type="text"
      class="form-control"
      :placeholder="$t('settings.chat.adifloggingwavelogapi_placeholder')"
      @change="onChange"
    >
  </div>
</template>

