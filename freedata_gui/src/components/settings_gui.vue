<template>
  <!-- Top Info Area for GUI Settings -->
  <div
    class="alert alert-info"
    role="alert"
  >
    <strong><i class="bi bi-gear-wide-connected me-1" /></strong> {{ $t('settings.gui.introduction') }}
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
        <i class="bi bi-question-circle" />
      </button>
    </span>
    <select
      v-model="settings.local.language"
      class="form-select form-select-sm w-50"
      @change="updateLanguage"
    >
      <option
        v-for="lang in availableLanguages"
        :key="lang.iso"
        :value="lang.iso"
      >
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
        <i class="bi bi-question-circle" />
      </button>
    </span>
    <select
      id="colormode_selector"
      v-model="settings.local.colormode"
      class="form-select form-select-sm w-50"
      @change="updateColormode"
    >
      <option value="light">
        {{ $t('settings.gui.colormodelight') }}
      </option>
      <option value="dark">
        {{ $t('settings.gui.colormodedark') }}
      </option>
      <option value="auto">
        {{ $t('settings.gui.colormodeauto') }}
      </option>
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
        <i class="bi bi-question-circle" />
      </button>
    </span>
    <select
      id="wftheme_selector"
      v-model="settings.local.wf_theme"
      class="form-select form-select-sm w-50"
      @change="saveSettings"
    >
      <option value="2">
        {{ $t('settings.default') }}
      </option>
      <option value="0">
        Turbo
      </option>
      <option value="1">
        Fosphor
      </option>
      <option value="3">
        Inferno
      </option>
      <option value="4">
        Magma
      </option>
      <option value="5">
        Jet
      </option>
      <option value="6">
        Binary
      </option>
      <option value="7">
        Plasma
      </option>
      <option value="8">
        Rainbow
      </option>
      <option value="9">
        Ocean
      </option>
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
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          id="autoLaunchBrowserSwitch"
          v-model="settings.remote.GUI.auto_run_browser"
          class="form-check-input"
          type="checkbox"
          @change="onChange"
        >
        <label
          class="form-check-label"
          for="autoLaunchBrowserSwitch"
        >{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>

  <!-- Distance Unit Setting -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      {{ $t('settings.gui.distanceunit') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.gui.distanceunit_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </span>
    <select
      id="distance_unit_selector"
      v-model="settings.remote.GUI.distance_unit"
      class="form-select form-select-sm w-50"
      @change="onChange"
    >
      <option value="km">
        {{ $t('settings.gui.distanceunitkilometers') }}
      </option>
      <option value="mi">
        {{ $t('settings.gui.distanceunitmiles') }}
      </option>
      <option value="nm">
        {{ $t('settings.gui.distanceunitnauticalmiles') }}
      </option>
    </select>
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
    // Ensure distance_unit has a default value
    if (settings.remote.GUI.distance_unit !== "km" || settings.remote.GUI.distance_unit !== "mi") {
      settings.remote.GUI.distance_unit = "km";
    }
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
