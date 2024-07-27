<template>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50">Waterfall theme</span>
    <select
      class="form-select form-select-sm w-50"
      id="wftheme_selector"
      @change="saveSettings"
      v-model="settings.local.wf_theme"
    >
      <option value="2">Default</option>
      <option value="0">Turbo</option>
      <option value="1">Fosphor</option>
      <option value="3">Inferno</option>
      <option value="4">Magma</option>
      <option value="5">Jet</option>
      <option value="6">Binary</option>
    </select>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Auto launch browser</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="NotificationSwitch"
          @change="onChange"
          v-model="settings.remote.GUI.auto_run_browser"
        />
        <label class="form-check-label" for="NotificationSwitch">On server statrup, launch a browser to GUI URL</label>
      </div>
    </label>
  </div>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50">Update channel</span>
    <select
      class="form-select form-select-sm w-50"
      id="update_channel_selector"
      @change="saveSettings"
      v-model="settings.local.update_channel"
    >
      <option value="latest">Stable</option>
      <option value="beta">Beta</option>
      <option value="alpha">Alpha</option>
    </select>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Enable notifications</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="NotificationSwitch"
          @change="saveSettings"
          v-model="settings.local.enable_sys_notification"
        />
        <label class="form-check-label" for="NotificationSwitch">Show system pop-ups</label>
      </div>
    </label>
  </div>
</template>

<script>
import { setColormap } from "../js/waterfallHandler";
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { setActivePinia } from "pinia";
import pinia from "../store/index";

// Set the active Pinia store
setActivePinia(pinia);

// Function to save settings and update colormap
function saveSettings() {
  // Save settings to file if needed
  setColormap();
}

// Export methods for use in the template
export default {
  methods: {
    saveSettings,
    onChange,
  },
  computed: {
    settings() {
      return settings;
    },
  },
};
</script>
