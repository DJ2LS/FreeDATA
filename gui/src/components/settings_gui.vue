<script setup lang="ts">
import { saveSettingsToFile } from "../js/settingsHandler";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

function saveSettings() {
  saveSettingsToFile();
}
</script>
<template>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50">GUI theme</span>
    <select
      class="form-select form-select-sm w-50"
      id="theme_selector"
      @change="saveSettings"
      v-model="settings.theme"
      disabled
    >
      <option value="default_light">Default (light)</option>
      <option value="default_dark">Default (dark)</option>
      <option value="default_auto">Default (auto)</option>
      <option value="cerulean">Cerulean</option>
      <option value="cosmo">Cosmo</option>
      <option value="cyborg">Cyborg</option>
      <option value="darkly">Darkly</option>
      <option value="flatly">Flatly</option>
      <option value="journal">Journal</option>
      <option value="litera">Litera</option>
      <option value="lumen">Lumen</option>
      <option value="lux">Lux</option>
      <option value="materia">Materia</option>
      <option value="minty">Minty</option>
      <option value="morph">Morhp</option>
      <option value="pulse">Pulse</option>
      <option value="quartz">Quartz</option>
      <option value="sandstone">Sandstone</option>
      <option value="simplex">Simplex</option>
      <option value="sketchy">Sketchy</option>
      <option value="slate">Slate</option>
      <option value="solar">Solar</option>
      <option value="spacelab">Spacelab</option>
      <option value="superhero">Superhero</option>
      <option value="united">United</option>
      <option value="vapor">Vapor</option>
      <option value="yeti">Yeti</option>
      <option value="zephyr">Zephyr</option>
    </select>
  </div>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50">Waterfall theme</span>
    <select
      class="form-select form-select-sm w-50"
      id="wftheme_selector"
      @change="saveSettings"
      v-model="settings.wftheme"
      disabled
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
    <label class="input-group-text w-50">Enable fancy GUI</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="GraphicsSwitch"
          @change="saveSettings"
          v-model="settings.high_graphics"
          true-value="True"
          false-value="False"
          disabled
        />
        <label class="form-check-label" for="GraphicsSwitch"
          >Higher CPU Usage</label
        >
      </div>
    </label>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50" for="inputGroupFile02"
      >Received files folder</label
    >
    <input
      type="text"
      class="form-control w-50"
      id="received_files_folder"
      disabled
    />
  </div>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50">Update channel</span>
    <select
      class="form-select form-select-sm w-50"
      id="update_channel_selector"
      @change="saveSettings"
      v-model="settings.update_channel"
      disabled
    >
      <option value="latest">stable</option>
      <option value="beta">beta</option>
      <option value="alpha">alpha</option>
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
          v-model="settings.enable_sys_notification"
          true-value="True"
          false-value="False"
          disabled
        />
        <label class="form-check-label" for="NotificationSwitch"
          >Show system pop-ups</label
        >
      </div>
    </label>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Auto-start Modem/rigctld</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="AutoStartSwitch"
          @change="saveSettings"
          v-model="settings.auto_start"
          true-value="True"
          false-value="False"
          disabled
        />
        <label class="form-check-label" for="AutoStartSwitch"
          >Start on app launch</label
        >
      </div>
    </label>
  </div>
</template>
