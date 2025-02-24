<template>
  <!-- Top Info Area for GUI Settings -->
  <div class="alert alert-info" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i>GUI</strong> related settings, like customizing your <strong>waterfall theme</strong>, <strong>notifications</strong>, and <strong>browser behavior</strong>.
  </div>

  <!-- Waterfall Theme Selection -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      Waterfall theme
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Select color theme for waterfall display"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </span>
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

  <!-- Auto Launch Browser Toggle -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Auto launch browser
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Launch browser to GUI URL on server startup"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="autoLaunchBrowserSwitch"
          @change="onChange"
          v-model="settings.remote.GUI.auto_run_browser"
        />
        <label class="form-check-label" for="autoLaunchBrowserSwitch">Enable</label>
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
