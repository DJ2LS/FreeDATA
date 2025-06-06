<script setup>

import { settingsStore as settings, onChange } from "../store/settingsStore.js";


// Pinia setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);


import { startModem, stopModem } from "../js/api.js";

import { useAudioStore } from "../store/audioStore";
const audioStore = useAudioStore(pinia);


function reloadModem(){
  stopModem();
  setTimeout(startModem, 5000); // Executes startModem after 5000 milliseconds as server needs to shutdown first
}

</script>

<template>
  <!-- Top Info Area for Modem and Audio Settings -->
  <div
    class="alert alert-info"
    role="alert"
  >
    <strong><i class="bi bi-gear-wide-connected me-1" /></strong>{{ $t('settings.modem.introduction') }}
  </div>

  <div
    class="alert alert-light"
    role="alert"
  >
    <span class="text-danger">{{ $t('settings.modem.serverrestart_notification') }}</span>
  </div>

  <!-- Start and Stop Modem Buttons -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">

      {{ $t('settings.modem.restartserver') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.modem.restartserver_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <div class="w-50 d-flex justify-content-between">
      <button
        type="button"
        class="btn btn-outline-secondary btn-sm w-100 me-1"
        data-bs-toggle="tooltip"
        title="Start the Modem"
        @click="reloadModem"
      >
        <i class="bi bi-arrow-clockwise" />
        {{ $t('settings.reload') }}
      </button>
    </div>
  </div>
  <!-- Modem Port -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap text-danger">
      {{ $t('settings.modem.modemport') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.modem.modemport_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <input
      id="modem_port"
      v-model.number="settings.remote.NETWORK.modemport"
      type="number"
      class="form-control"
      placeholder="Enter modem port"
      maxlength="5"
      max="65534"
      min="1025"
      @change="onChange"
    >
  </div>

  <!-- Modem Host -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap text-danger">
      {{ $t('settings.modem.modemhost') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.modem.modemhost_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <select
      id="modem_host"
      v-model="settings.remote.NETWORK.modemaddress"
      class="form-select form-select-sm w-50"
      @change="onChange"
    >
      <option value="127.0.0.1">
        127.0.0.1 (Local operation)
      </option>
      <option value="localhost">
        localhost (Local operation)
      </option>
      <option value="0.0.0.0">
        0.0.0.0 (Remote operation)
      </option>
    </select>
  </div>

  <!-- Audio Input Device -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.modem.audioinputdevice') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.modem.audioinputdevice_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <select
      v-model="settings.remote.AUDIO.input_device"
      class="form-select form-select-sm w-50"
      @change="onChange"
    >
      <option
        v-for="device in audioStore.audioInputs"
        :key="device.id"
        :value="device.id"
      >
        {{ device.name }} [{{ device.api }}]
      </option>
    </select>
  </div>

  <!-- Audio Output Device -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.modem.audiooutputdevice') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.modem.audiooutputdevice_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <select
      v-model="settings.remote.AUDIO.output_device"
      class="form-select form-select-sm w-50"
      @change="onChange"
    >
      <option
        v-for="device in audioStore.audioOutputs"
        :key="device.id"
        :value="device.id"
      >
        {{ device.name }} [{{ device.api }}]
      </option>
    </select>
  </div>

  <!-- RX Audio Level -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.modem.rxaudiolevel') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.modem.rxaudiolevel_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <div class="input-group-text w-25">
      {{ settings.remote.AUDIO.rx_audio_level }}
    </div>
    <div class="w-25">
      <input
        id="audioLevelRX"
        v-model.number="settings.remote.AUDIO.rx_audio_level"
        type="range"
        class="form-range"
        min="-30"
        max="20"
        step="1"
        @change="onChange"
      >
    </div>
  </div>

  <!-- TX Audio Level -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.modem.txaudiolevel') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.modem.txaudiolevel_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <div class="input-group-text w-25">
      {{ settings.remote.AUDIO.tx_audio_level }}
    </div>
    <div class="w-25">
      <input
        id="audioLevelTX"
        v-model.number="settings.remote.AUDIO.tx_audio_level"
        type="range"
        class="form-range"
        min="-30"
        max="20"
        step="1"
        @change="onChange"
      >
    </div>
  </div>

<!-- RX Audio Auto Adjust -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.modem.enablerxautoadjust') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.modem.enablerxautoadjust_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          id="enableRXAutoAudioSwitch"
          v-model="settings.remote.AUDIO.rx_auto_audio_level"
          class="form-check-input"
          type="checkbox"
          @change="onChange"
        >
        <label
          class="form-check-label"
          for="enableRXAutoAudioSwitch"
        >{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>

<!-- TX Audio Auto Adjust -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.modem.enabletxautoadjust') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.modem.enabletxautoadjust_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          id="enableTXAutoAudioSwitch"
          v-model="settings.remote.AUDIO.tx_auto_audio_level"
          class="form-check-input"
          type="checkbox"
          @change="onChange"
        >
        <label
          class="form-check-label"
          for="enableTXAutoAudioSwitch"
        >{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>

  <!-- TX Delay -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.modem.txdelay') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.modem.txdelay_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <select
      id="tx_delay"
      v-model.number="settings.remote.MODEM.tx_delay"
      class="form-select form-select-sm w-50"
      @change="onChange"
    >
      <option value="0">
        0
      </option>
      <option value="50">
        50
      </option>
      <option value="100">
        100
      </option>
      <option value="150">
        150
      </option>
      <option value="200">
        200
      </option>
      <option value="250">
        250
      </option>
      <option value="300">
        300
      </option>
      <option value="350">
        350
      </option>
      <option value="400">
        400
      </option>
      <option value="450">
        450
      </option>
      <option value="500">
        500
      </option>
      <option value="550">
        550
      </option>
      <option value="600">
        600
      </option>
      <option value="650">
        650
      </option>
      <option value="700">
        700
      </option>
      <option value="750">
        750
      </option>
      <option value="800">
        800
      </option>
      <option value="850">
        850
      </option>
      <option value="900">
        900
      </option>
      <option value="950">
        950
      </option>
      <option value="1000">
        1000
      </option>
    </select>
  </div>

  <!-- Maximum Used Bandwidth -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.modem.maximumbandwidth') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.modem.maximumbandwidth_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <select
      id="maximum_bandwidth"
      v-model.number="settings.remote.MODEM.maximum_bandwidth"
      class="form-select form-select-sm w-50"
      @change="onChange"
    >
      <option value="250">
        250 Hz
      </option>
      <option value="500">
        500 Hz
      </option>
      <option value="1700">
        1700 Hz
      </option>
      <option value="2438">
        2438 Hz
      </option>
    </select>
  </div>
</template>


