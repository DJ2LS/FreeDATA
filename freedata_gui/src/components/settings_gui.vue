<template>
  <!-- Top Info Area for GUI Settings -->
  <div class="alert alert-info" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i>GUI</strong> related settings, like customizing your <strong>waterfall theme</strong>, <strong>notifications</strong>, and <strong>browser behavior</strong>.
  </div>

  <!-- Waterfall Theme Selection -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      Waterfall theme
      <span id="wfThemeHelp" class="ms-2 badge bg-secondary text-wrap">
        Select color theme for waterfall display
      </span>
    </span>
    <select
      class="form-select form-select-sm w-50"
      id="wftheme_selector"
      aria-describedby="wfThemeHelp"
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

  <!-- Auto Launch Browser Toggle -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Auto launch browser
      <span id="autoLaunchBrowserHelp" class="ms-2 badge bg-secondary text-wrap">
        Launch browser to GUI URL on server startup
      </span>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="autoLaunchBrowserSwitch"
          aria-describedby="autoLaunchBrowserHelp"
          @change="onChange"
          v-model="settings.remote.GUI.auto_run_browser"
        />
        <label class="form-check-label" for="autoLaunchBrowserSwitch">Enable</label>
      </div>
    </label>
  </div>

  <!-- Enable Notifications Toggle -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Enable notifications
      <span id="enableNotificationsHelp" class="ms-2 badge bg-secondary text-wrap">
        Show system pop-ups
      </span>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="enableNotificationsSwitch"
          aria-describedby="enableNotificationsHelp"
          @change="saveSettings"
          v-model="settings.local.enable_sys_notification"
        />
        <label class="form-check-label" for="enableNotificationsSwitch">Enable</label>
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
