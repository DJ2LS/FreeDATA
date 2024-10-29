<script>
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { setActivePinia } from "pinia";
import pinia from "../store/index";

// Set the active Pinia store
setActivePinia(pinia);

// Export methods and computed properties for use in the template
export default {
  methods: {
    onChange,
  },
  computed: {
    settings() {
      return settings;
    },
  },
};
</script>

<template>
  <!-- Top Info Area for Messages Settings -->
  <div class="alert alert-info" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i>Messages</strong> related settings, like enabling <strong>message auto repeat</strong> and configuring <strong>ADIF log</strong> connection.
  </div>

  <!-- Enable Message Auto Repeat -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Enable message auto repeat
      <span id="enableAutoRepeatHelp" class="ms-2 badge bg-secondary text-wrap">
        Re-send message on beacon
      </span>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline ms-2">
        <input
          class="form-check-input"
          type="checkbox"
          id="enableMessagesAutoRepeatSwitch"
          aria-describedby="enableAutoRepeatHelp"
          @change="onChange"
          v-model="settings.remote.MESSAGES.enable_auto_repeat"
        />
        <label class="form-check-label" for="enableMessagesAutoRepeatSwitch">Enable</label>
      </div>
    </label>
  </div>

  <!-- ADIF Log Host -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      ADIF Log Host
      <span id="adifLogHostHelp" class="ms-2 badge bg-secondary text-wrap">
        ADIF server host, e.g., 127.0.0.1
      </span>
    </label>
    <input
      type="text"
      class="form-control"
      placeholder="Enter ADIF server host"
      id="adifLogHost"
      aria-describedby="adifLogHostHelp"
      @change="onChange"
      v-model="settings.remote.MESSAGES.adif_log_host"
    />
  </div>

  <!-- ADIF Log Port -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      ADIF Log Port
      <span id="adifLogPortHelp" class="ms-2 badge bg-secondary text-wrap">
        ADIF server port, e.g., 2237
      </span>
    </label>
    <input
      type="number"
      class="form-control"
      placeholder="Enter ADIF server port"
      id="adifLogPort"
      max="65534"
      min="1025"
      aria-describedby="adifLogPortHelp"
      @change="onChange"
      v-model.number="settings.remote.MESSAGES.adif_log_port"
    />
  </div>
</template>

