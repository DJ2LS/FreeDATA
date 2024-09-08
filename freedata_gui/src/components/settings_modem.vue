<script setup>

import { settingsStore as settings, onChange } from "../store/settingsStore.js";


// Pinia setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { startModem, stopModem } from "../js/api.js";

import { useAudioStore } from "../store/audioStore";
const audioStore = useAudioStore(pinia);
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
    <label class="input-group-text w-50">Modem port (server restart required!)</label>

    <input
      type="number"
      class="form-control"
      placeholder="modem port"
      id="modem_port"
      maxlength="5"
      max="65534"
      min="1025"
      @change="onChange"
      v-model.number="settings.remote.NETWORK.modemport"
    />
  </div>

  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Modem host (server restart required!)</label>
    <select
      class="form-select form-select-sm"
      id="modem_port"
      v-model="settings.remote.NETWORK.modemaddress"
      @change="onChange"
    >
      <option value="127.0.0.1">127.0.0.1 ( Local operation )</option>
      <option value="localhost">localhost ( Local operation )</option>
      <option value="0.0.0.0">0.0.0.0 ( Remote operation )</option>
    </select>
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
      <option v-for="device in audioStore.audioInputs" :key="device.id" :value="device.id">
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
      <option v-for="device in audioStore.audioOutputs" :key="device.id" :value="device.id">
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
      />
    </span>
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
      />
    </span>
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
    <label class="input-group-text w-50">Maximum used bandwidth</label>
    <select
      class="form-select form-select-sm"
      id="maximum_bandwidth"
      @change="onChange"
      v-model.number="settings.remote.MODEM.maximum_bandwidth"
    >
      <option value="250">250 Hz</option>
      <option value="500">500 Hz</option>
      <option value="1700">1700 Hz</option>
      <option value="2438">2438 Hz</option>
    </select>
  </div>


</template>
