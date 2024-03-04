<script setup lang="ts">
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import pinia from "../store/index";

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { startModem, stopModem } from "../js/api.js";

import { useAudioStore } from "../store/audioStore";
const audioStore = useAudioStore();
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
      v-model.number="settings.local.port"
    />
  </div>

  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Modem host</span>
    <input
      type="text"
      class="form-control"
      placeholder="modem host"
      id="modem_port"
      v-model="settings.local.host"
    />
  </div>

  <!-- Audio Input Device -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Audio Input device</label>
    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      @change="onChange"
      v-model="settings.remote.AUDIO.input_device"
    >
      <option v-for="device in audioStore.audioInputs" :value="device.id">
        {{ device.name }} [{{ device.api }}]
      </option>
    </select>
  </div>

  <!-- Audio Output Device -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Audio Output device</label>
    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      @change="onChange"
      v-model="settings.remote.AUDIO.output_device"
    >
      <option v-for="device in audioStore.audioOutputs" :value="device.id">
        {{ device.name }} [{{ device.api }}]
      </option>
    </select>
  </div>

  <!-- Audio rx level-->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-25">RX Audio Level</span>
    <span class="input-group-text w-25">{{
      settings.remote.AUDIO.rx_audio_level
    }}</span>
    <span class="input-group-text w-50">
      <input
        type="range"
        class="form-range"
        min="-30"
        max="20"
        step="1"
        id="audioLevelRX"
        @change="onChange"
        v-model.number="settings.remote.AUDIO.rx_audio_level"
    /></span>
  </div>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-25">TX Audio Level</span>
    <span class="input-group-text w-25">{{
      settings.remote.AUDIO.tx_audio_level
    }}</span>
    <span class="input-group-text w-50">
      <input
        type="range"
        class="form-range"
        min="-30"
        max="20"
        step="1"
        id="audioLevelTX"
        @change="onChange"
        v-model.number="settings.remote.AUDIO.tx_audio_level"
    /></span>
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">TX delay in ms</label>
    <select
      class="form-select form-select-sm"
      id="tx_delay"
      @change="onChange"
      v-model.number="settings.remote.MODEM.tx_delay"
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
      @change="onChange"
      v-model.number="settings.remote.MODEM.tuning_range_fmin"
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
      @change="onChange"
      v-model.number="settings.remote.MODEM.tuning_range_fmax"
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
      @change="onChange"
      v-model.number="settings.remote.MODEM.beacon_interval"
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
    <label class="input-group-text w-50">Enable 250Hz bandwidth mode</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="250HzModeSwitch"
          v-model="settings.remote.MODEM.enable_low_bandwidth_mode"
          @change="onChange"
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
          v-model="settings.remote.MODEM.respond_to_cq"
          @change="onChange"
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
        @change="onChange"
        v-model.number="settings.remote.MODEM.rx_buffer_size"
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
