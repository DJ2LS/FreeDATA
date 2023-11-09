<script setup lang="ts">
import { saveModemConfig } from "../js/api";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);
</script>
<template>
  <!-- station callsign -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px"
      >Your station callsign</span
    >
    <input
      type="text"
      class="form-control"
      placeholder="Enter your callsign and save it"
      id="myCall"
      aria-label="Station Callsign"
      aria-describedby="basic-addon1"
      @change="saveModemConfig"
      v-model="settings.mycall"
    />
  </div>

  <!-- station ssid -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Call SSID</span>
    <select
      class="form-select form-select-sm w-50"
      id="myCallSSID"
      @change="saveModemConfig"
      v-model="settings.myssid"
    >
      <option selected value="0">0</option>
      <option value="1">1</option>
      <option value="2">2</option>
      <option value="3">3</option>
      <option value="4">4</option>
      <option value="5">5</option>
      <option value="6">6</option>
      <option value="7">7</option>
      <option value="8">8</option>
      <option value="9">9</option>
      <option value="10">10</option>
      <option value="11">11</option>
      <option value="12">12</option>
      <option value="13">13</option>
      <option value="14">14</option>
      <option value="15">15</option>
    </select>
  </div>

  <!-- station grid locator -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Grid Locator</span>
    <input
      type="text"
      class="form-control"
      placeholder="Your grid locator"
      id="myGrid"
      maxlength="6"
      aria-label="Station Grid Locator"
      aria-describedby="basic-addon1"
      @change="saveModemConfig"
      v-model="settings.mygrid"
    />
  </div>
</template>
