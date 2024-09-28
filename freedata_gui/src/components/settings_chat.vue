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
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Enable message auto repeat</label>
    <div class="form-check form-switch form-check-inline ms-2">
      <input
        class="form-check-input"
        type="checkbox"
        @change="onChange"
        v-model="settings.remote.MESSAGES.enable_auto_repeat"
        id="enableMessagesAutoRepeatSwitch"
      />
      <label class="form-check-label" for="enableMessagesAutoRepeatSwitch">
        Re-send message on beacon
      </label>
    </div>
  </div>

  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50" for="adifLogHost">ADIF Log Host</label>
    <input
      type="text"
      class="form-control"
      placeholder="adif server host, e.g. 127.0.0.1"
      id="adifLogHost"
      @change="onChange"
      v-model="settings.remote.MESSAGES.adif_log_host"
    />
  </div>

  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50" for="adifLogPort">ADIF Log Port</label>
    <input
      type="number"
      class="form-control"
      placeholder="adif server port, e.g. 2237"
      id="adifLogPort"
      max="65534"
      min="1025"
      @change="onChange"
      v-model.number="settings.remote.MESSAGES.adif_log_port"
    />
  </div>

</template>
