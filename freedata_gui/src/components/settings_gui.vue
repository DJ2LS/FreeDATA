<template>
  <!-- Top Info Area for GUI Settings -->
  <div class="alert alert-info" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i></strong> {{ $t('settings.gui.introduction') }}
  </div>



  <!-- Language Selector -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      {{ $t('settings.gui.selectlanguage') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.gui.selectlanguage_help')"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </span>
    <select class="form-select form-select-sm w-50" v-model="settings.local.language" @change="updateLanguage">
      <option v-for="lang in availableLanguages" :key="lang.iso" :value="lang.iso">
        {{ lang.iso.toUpperCase() }} - {{ lang.name }}
      </option>
    </select>
  </div>

    <!-- Colormode Selector -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      {{ $t('settings.gui.colormode') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.gui.colormode_help')"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </span>
     <select
      class="form-select form-select-sm w-50"
      id="colormode_selector"
      @change="updateColormode"
      v-model="settings.local.colormode"
    >
      <option value="light">{{ $t('settings.gui.colormodelight') }}</option>
      <option value="dark">{{ $t('settings.gui.colormodedark') }}</option>
      <option value="auto">{{ $t('settings.gui.colormodeauto') }}</option>

    </select>
  </div>

  <!-- Waterfall Theme Selection -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      {{ $t('settings.gui.waterfalltheme') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.gui.waterfalltheme_help')"
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
      <option value="2">{{ $t('settings.default') }}</option>
      <option value="0">Turbo</option>
      <option value="1">Fosphor</option>
      <option value="3">Inferno</option>
      <option value="4">Magma</option>
      <option value="5">Jet</option>
      <option value="6">Binary</option>
      <option value="7">Plasma</option>
      <option value="8">Rainbow</option>
      <option value="9">Ocean</option>
    </select>
  </div>

  <!-- Auto Launch Browser Toggle -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">

      {{ $t('settings.gui.browserautolaunch') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.gui.browserautolaunch_help')"
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
        <label class="form-check-label" for="autoLaunchBrowserSwitch">{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>
</template>

<script>
import { setColormap } from "../js/waterfallHandler";
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { setActivePinia } from "pinia";
import pinia from "../store/index";
import { availableLanguages } from '../js/i18n';
import i18next from '../js/i18n';
import {applyColorMode} from '../js/freedata.js'

// Set the active Pinia store
setActivePinia(pinia);

// Function to save settings and update colormap
function saveSettings() {
  setColormap();
}

export default {
  data() {
    return {
      availableLanguages, // imported from i18next configuration
      settings,
    };
  },
  methods: {
    saveSettings,
    onChange,
    updateLanguage() {
      saveSettings();
      // Update the language in i18next
      i18next.changeLanguage(this.settings.local.language);
      this.$forceUpdate();
    },
    updateColormode() {
      saveSettings();
      applyColorMode(this.settings.local.colormode);

    },
  },
};
</script>
