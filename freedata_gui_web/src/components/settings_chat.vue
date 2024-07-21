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
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline ms-2">
        <input
          class="form-check-input"
          type="checkbox"
          @change="onChange"
          v-model="settings.remote.MESSAGES.enable_auto_repeat"
        />
        <label class="form-check-label" for="enableMessagesAutoRepeatSwitch"
          >Re-send message on beacon</label
        >
      </div>
    </label>
  </div>
</template>
