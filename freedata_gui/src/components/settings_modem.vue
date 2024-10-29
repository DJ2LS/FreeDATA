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
  <!-- Top Info Area for Modem and Audio Settings -->
  <div class="alert alert-info" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i>Modem and Audio</strong> related settings, including starting/stopping the modem, configuring audio devices, and adjusting audio levels.
  </div>

  <!-- Start and Stop Modem Buttons -->
  <div class="mb-2">
    <button
      type="button"
      id="startModem"
      class="btn btn-sm btn-outline-success"
      data-bs-toggle="tooltip"
      data-bs-trigger="hover"
      data-bs-html="false"
      title="Start the Modem. Please set your audio and radio settings first!"
      @click="startModem"
      :class="{ disabled: state.is_modem_running === true }"
    >
      <i class="bi bi-play-fill"></i>
      <span class="ms-2">Start Modem</span>
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
      :class="{ disabled: state.is_modem_running === false }"
    >
      <i class="bi bi-stop-fill"></i>
      <span class="ms-2">Stop Modem</span>
    </button>
  </div>

  <!-- Modem Port -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Modem port
      <span id="modemPortHelp" class="ms-2 badge bg-secondary text-wrap">
        Server restart required
      </span>
    </label>
    <input
      type="number"
      class="form-control"
      placeholder="Enter modem port"
      id="modem_port"
      maxlength="5"
      max="65534"
      min="1025"
      aria-describedby="modemPortHelp"
      @change="onChange"
      v-model.number="settings.remote.NETWORK.modemport"
    />
  </div>

  <!-- Modem Host -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Modem host
      <span id="modemHostHelp" class="ms-2 badge bg-secondary text-wrap">
        Server restart required
      </span>
    </label>
    <select
      class="form-select form-select-sm w-50"
      id="modem_host"
      aria-describedby="modemHostHelp"
      @change="onChange"
      v-model="settings.remote.NETWORK.modemaddress"
    >
      <option value="127.0.0.1">127.0.0.1 (Local operation)</option>
      <option value="localhost">localhost (Local operation)</option>
      <option value="0.0.0.0">0.0.0.0 (Remote operation)</option>
    </select>
  </div>

  <!-- Audio Input Device -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Audio Input device
      <span id="audioInputHelp" class="ms-2 badge bg-secondary text-wrap">
        Select your microphone or line-in device
      </span>
    </label>
    <select
      class="form-select form-select-sm w-50"
      aria-describedby="audioInputHelp"
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
    <label class="input-group-text w-50 text-wrap">
      Audio Output device
      <span id="audioOutputHelp" class="ms-2 badge bg-secondary text-wrap">
        Select your speakers or output device
      </span>
    </label>
    <select
      class="form-select form-select-sm w-50"
      aria-describedby="audioOutputHelp"
      @change="onChange"
      v-model="settings.remote.AUDIO.output_device"
    >
      <option v-for="device in audioStore.audioOutputs" :key="device.id" :value="device.id">
        {{ device.name }} [{{ device.api }}]
      </option>
    </select>
  </div>

  <!-- RX Audio Level -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      RX Audio Level
      <span id="rxAudioLevelHelp" class="ms-2 badge bg-secondary text-wrap">
        Adjust to set the receive audio gain
      </span>
    </label>
    <div class="input-group-text w-25">
      {{ settings.remote.AUDIO.rx_audio_level }}
    </div>
    <div class="w-25">
      <input
        type="range"
        class="form-range"
        min="-30"
        max="20"
        step="1"
        id="audioLevelRX"
        aria-describedby="rxAudioLevelHelp"
        @change="onChange"
        v-model.number="settings.remote.AUDIO.rx_audio_level"
      />
    </div>
  </div>

  <!-- TX Audio Level -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      TX Audio Level
      <span id="txAudioLevelHelp" class="ms-2 badge bg-secondary text-wrap">
        Adjust to set the transmit audio gain
      </span>
    </label>
    <div class="input-group-text w-25">
      {{ settings.remote.AUDIO.tx_audio_level }}
    </div>
    <div class="w-25">
      <input
        type="range"
        class="form-range"
        min="-30"
        max="20"
        step="1"
        id="audioLevelTX"
        aria-describedby="txAudioLevelHelp"
        @change="onChange"
        v-model.number="settings.remote.AUDIO.tx_audio_level"
      />
    </div>
  </div>

  <!-- TX Delay -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      TX delay in ms
      <span id="txDelayHelp" class="ms-2 badge bg-secondary text-wrap">
        Delay before transmitting, in milliseconds
      </span>
    </label>
    <select
      class="form-select form-select-sm w-50"
      id="tx_delay"
      aria-describedby="txDelayHelp"
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

  <!-- Maximum Used Bandwidth -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Maximum used bandwidth
      <span id="maxBandwidthHelp" class="ms-2 badge bg-secondary text-wrap">
        Select the maximum bandwidth the modem will use
      </span>
    </label>
    <select
      class="form-select form-select-sm w-50"
      id="maximum_bandwidth"
      aria-describedby="maxBandwidthHelp"
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

