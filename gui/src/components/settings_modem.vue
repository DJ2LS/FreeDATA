<script setup lang="ts">
import { saveModemConfig } from "../js/api";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import { useAudioStore } from "../store/audioStore.js";
const audio = useAudioStore(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { startModem, stopModem } from "../js/api";
</script>

<template>
  <div>
    <button
      type="button"
      id="startModem"
      class="btn btn-sm btn-outline-success"
      data-bs-toggle="tooltip"
      data-bs-trigger="hover"
      data-bs-html="false"
      title="Start the Modem. Please set your audio and radio settings first!"
      @click="startModem"
      v-bind:class="{ disabled: state.is_modem_running === true }"
    >
      <i class="bi bi-play-fill"></i>
      <span class="ms-2">start modem</span>
    </button>
    <button
      type="button"
      id="stopModem"
      class="btn btn-sm btn-outline-danger"
      data-bs-toggle="tooltip"
      data-bs-trigger="hover"
      data-bs-html="false"
      title="Stop the Modem."
      @click="stopModem"
      v-bind:class="{ disabled: state.is_modem_running === false }"
    >
      <i class="bi bi-stop-fill"></i>
      <span class="ms-2">stop modem</span>
    </button>
  </div>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Modem port</span>
    <input
      type="number"
      class="form-control"
      placeholder="modem port"
      id="modem_port"
      maxlength="5"
      max="65534"
      min="1025"
      @change="saveModemConfig()"
      v-model.number="settings.modem_port"
    />
  </div>

  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Modem host</span>
    <input
      type="text"
      class="form-control"
      placeholder="modem host"
      id="modem_port"
      @change="saveModemConfig"
      v-model="settings.modem_host"
    />
  </div>

  <!-- Audio Input Device -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Audio Input device</label>
    <select
      class="form-select form-select-sm"
      id="rx_audio"
      aria-label=".form-select-sm"
      @change="saveModemConfig"
      v-model="settings.input_device"
      v-html="audio.getInputDevices()"
    ></select>
  </div>

  <!-- Audio Output Device -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Audio Output device</label>
    <select
      class="form-select form-select-sm"
      id="tx_audio"
      aria-label=".form-select-sm"
      @change="saveModemConfig"
      v-model="settings.output_device"
      v-html="audio.getOutputDevices()"
    ></select>
  </div>

  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">TX delay in ms</label>
    <select
      class="form-select form-select-sm"
      id="tx_delay"
      @change="saveModemConfig"
      v-model.number="settings.tx_delay"
    >
      <option value="0">0</option>
      <option value="50">50</option>
      <option value="100">100</option>
      <option value="150">150</option>
      <option value="200">200</option>
      <option value="250">250</option>
      <option value="300">300</option>
      <option value="350">350</option>
      <option value="400">400</option>
      <option value="450">450</option>
      <option value="500">500</option>
      <option value="550">550</option>
      <option value="600">600</option>
      <option value="650">650</option>
      <option value="700">700</option>
      <option value="750">750</option>
      <option value="800">800</option>
      <option value="850">850</option>
      <option value="900">900</option>
      <option value="950">950</option>
      <option value="1000">1000</option>
    </select>
  </div>

  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-25">Tuning range</label>
    <label class="input-group-text">fmin</label>
    <select
      class="form-select form-select-sm"
      id="tuning_range_fmin"
      @change="saveModemConfig"
      v-model.number="settings.tuning_range_fmin"
    >
      <option value="-50">-50</option>
      <option value="-100">-100</option>
      <option value="-150">-150</option>
      <option value="-200">-200</option>
      <option value="-250">-250</option>
    </select>
    <label class="input-group-text">fmax</label>
    <select
      class="form-select form-select-sm"
      id="tuning_range_fmax"
      @change="saveModemConfig"
      v-model.number="settings.tuning_range_fmax"
    >
      <option value="50">50</option>
      <option value="100">100</option>
      <option value="150">150</option>
      <option value="200">200</option>
      <option value="250">250</option>
    </select>
  </div>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50">Beacon interval</span>
    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="beaconInterval"
      style="width: 6rem"
      @change="saveModemConfig"
      v-model="settings.beacon_interval"
    >
      <option value="60">60 secs</option>
      <option value="90">90 secs</option>
      <option value="120">2 mins</option>
      <option selected value="300">5 mins</option>
      <option value="600">10 mins</option>
      <option value="900">15 mins</option>
      <option value="1800">30 mins</option>
      <option value="3600">60 mins</option>
    </select>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Enable waterfall data</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="fftSwitch"
          @change="saveModemConfig"
          v-model="settings.enable_fft"
        />
        <label class="form-check-label" for="fftSwitch">Waterfall</label>
      </div>
    </label>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Enable scatter diagram data</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="scatterSwitch"
          @change="saveModemConfig"
          v-model="settings.enable_scatter"
        />
        <label class="form-check-label" for="scatterSwitch">Scatter</label>
      </div>
    </label>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Enable 250Hz bandwidth mode</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="250HzModeSwitch"
          v-model="settings.low_bandwidth_mode"
          @change="saveModemConfig"
        />
        <label class="form-check-label" for="250HzModeSwitch">250Hz</label>
      </div>
    </label>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Respond to CQ</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="respondCQSwitch"
          v-model="settings.respond_to_cq"
          @change="saveModemConfig"
        />
        <label class="form-check-label" for="respondCQSwitch">QRV</label>
      </div>
    </label>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">RX buffer size</label>
    <label class="input-group-text w-50">
      <select
        class="form-select form-select-sm"
        id="rx_buffer_size"
        @change="saveModemConfig"
        v-model.number="settings.rx_buffer_size"
      >
        <option value="1">1</option>
        <option value="2">2</option>
        <option value="4">4</option>
        <option value="8">8</option>
        <option value="16">16</option>
        <option value="32">32</option>
        <option value="64">64</option>
        <option value="128">128</option>
        <option value="256">256</option>
        <option value="512">512</option>
        <option value="1024">1024</option>
      </select>
    </label>
  </div>
</template>
