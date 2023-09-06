<script setup lang="ts">

import {saveSettingsToFile} from '../js/settingsHandler'

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);

function saveSettings(){
    saveSettingsToFile()
}

</script>

<template>

    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50">TNC IP</label>

      <div
        class="btn-group btn-group-sm me-2"
        role="group"
        aria-label="local-remote-switch toggle button group"
        data-bs-placement="bottom"
        data-bs-toggle="tooltip"
        data-bs-trigger="hover"
        data-bs-html="true"
        title="Select a local or a remote location of your TNC daemon. Normally local is the preferred option."
      >
        <input
          type="radio"
          class="btn-check"
          name="local-remote-switch"
          id="local-remote-switch1"
          autocomplete="off"
                  @change="saveSettings"
        />
        <label
          class="btn btn-sm btn-outline-secondary"
          for="local-remote-switch1"
        >
          <i class="bi bi-pc-display-horizontal"></i>
          <span class="ms-2 me-2">Local tnc</span>
        </label>
        <input
          type="radio"
          class="btn-check"
          name="local-remote-switch"
          id="local-remote-switch2"
          autocomplete="off"
                  @change="saveSettings"
        />
        <label
          class="btn btn-sm btn-outline-secondary"
          for="local-remote-switch2"
        >
          <i class="bi bi-ethernet"></i>
          <span class="ms-2 me-2">Remote tnc</span>
        </label>
      </div>

      <div class="input-group input-group-sm me-2" id="remote-tnc-field">
        <span class="input-group-text">tnc ip</span>
        <input
          type="text"
          class="form-control"
          placeholder="ip address"
          id="tnc_adress"
          maxlength="17"
          style="width: 8rem"
          aria-label="Username"
          aria-describedby="basic-addon1"
                  @change="saveSettings"
        v-model="settings.tnc_host"
        />
        <span class="input-group-text">:</span>
        <input
          type="text"
          class="form-control"
          placeholder="port"
          id="tnc_port"
          maxlength="5"
          max="65534"
          min="1025"
          style="width: 4rem"
          aria-label="Username"
          aria-describedby="basic-addon1"
                  @change="saveSettings"
        v-model="settings.tnc_port"
        />
        <button
          class="btn btn-sm btn-danger"
          id="daemon_connection_state"
          type="button"
          disabled
        >
          <i class="bi bi-diagram-3" style="font-size: 1rem"></i>
        </button>
      </div>

      <button
        type="button"
        id="openHelpModalLocalRemote"
        data-bs-toggle="modal"
        data-bs-target="#localRemoteHelpModal"
        class="btn m-0 p-0 border-0"
      >
        <i class="bi bi-question-circle" style="font-size: 1rem"></i>
      </button>
    </div>

    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50">TX delay in ms</label>
      <select class="form-select form-select-sm" id="tx_delay"         @change="saveSettings"
        v-model="settings.tx_delay">
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
      <select class="form-select form-select-sm" id="tuning_range_fmin"         @change="saveSettings"
        v-model="settings.tuning_range_fmin">
        <option value="-50.0">-50.0</option>
        <option value="-100.0">-100.0</option>
        <option value="-150.0">-150.0</option>
        <option value="-200.0">-200.0</option>
        <option value="-250.0">-250.0</option>
      </select>
      <label class="input-group-text">fmax</label>
      <select class="form-select form-select-sm" id="tuning_range_fmax"         @change="saveSettings"
        v-model="settings.tuning_range_fmax">
        <option value="50.0">50.0</option>
        <option value="100.0">100.0</option>
        <option value="150.0">150.0</option>
        <option value="200.0">200.0</option>
        <option value="250.0">250.0</option>
      </select>
    </div>
    <div class="input-group input-group-sm mb-1">
      <span class="input-group-text w-50">Beacon interval</span>
      <select
        class="form-select form-select-sm"
        aria-label=".form-select-sm"
        id="beaconInterval"
        style="width: 6rem"
                @change="saveSettings"
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
          <input class="form-check-input" type="checkbox" id="fftSwitch"         @change="saveSettings" v-model="settings.enable_fft" true-value="True" false-value="False"/>
          <label class="form-check-label" for="fftSwitch">Waterfall</label>
        </div>
      </label>
    </div>
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50">Enable scatter diagram data</label>
      <label class="input-group-text w-50">
        <div class="form-check form-switch form-check-inline">
          <input class="form-check-input" type="checkbox" id="scatterSwitch" @change="saveSettings" v-model="settings.enable_scatter" true-value="True" false-value="False"/>
          <label class="form-check-label" for="scatterSwitch">Scatter</label>
        </div>
      </label>
    </div>
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50">Enable 250Hz only mode</label>
      <label class="input-group-text w-50">
        <div class="form-check form-switch form-check-inline">
          <input
            class="form-check-input"
            type="checkbox"
            id="250HzModeSwitch"
            v-model="settings.low_bandwidth_mode" true-value="True" false-value="False" @change="saveSettings"
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
            v-model="settings.respond_to_cq" true-value="True" false-value="False" @change="saveSettings"
          />
          <label class="form-check-label" for="respondCQSwitch">QRV</label>
        </div>
      </label>
    </div>
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50">RX buffer size</label>
      <label class="input-group-text w-50">
        <select class="form-select form-select-sm" id="rx_buffer_size"         @change="saveSettings"
        v-model="settings.rx_buffer_size">
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
