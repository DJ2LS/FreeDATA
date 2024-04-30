<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
import {
  setRadioParametersFrequency,
  setRadioParametersMode,
  setRadioParametersRFLevel,
  setRadioParametersTuner,
} from "../../js/api";
setActivePinia(pinia);

import { useStateStore } from "../../store/stateStore.js";
const state = useStateStore(pinia);

function set_radio_parameter_frequency() {
  setRadioParametersFrequency(state.new_frequency);
}

function set_radio_parameter_mode() {
  setRadioParametersMode(state.mode);
}

function set_radio_parameter_rflevel() {
  setRadioParametersRFLevel(state.rf_level);
}

function set_radio_parameter_auto_tuner() {
  console.log(state.tuner);
  setRadioParametersTuner(state.tuner);
}
</script>

<template>
  <div class="card h-100">
    <div class="card-header p-0">
      <i class="bi bi-house-door" style="font-size: 1.2rem"></i>&nbsp;
      <strong>Radio control</strong>
    </div>

    <div class="card-body overflow-auto p-0">
      <div class="input-group input-group-sm bottom-0 m-0">
        <div class="me-2">
          <div class="input-group input-group-sm">
            <span class="input-group-text">QRG</span>
            <span class="input-group-text"
              >{{ state.frequency / 1000 }} kHz</span
            >

            <button
              class="btn btn-secondary dropdown-toggle"
              v-bind:class="{
                disabled: state.hamlib_status === 'disconnected',
              }"
              type="button"
              data-bs-toggle="offcanvas"
              data-bs-target="#offcanvasFrequency"
              aria-controls="offcanvasExample"
            ></button>
          </div>
        </div>

        <div class="me-2">
          <div class="input-group input-group-sm">
            <span class="input-group-text">Mode</span>
            <select
              class="form-control"
              v-model="state.mode"
              @click="set_radio_parameter_mode()"
              v-bind:class="{
                disabled: state.hamlib_status === 'disconnected',
              }"
            >
              <option selected value="">---</option>
              <option value="USB">USB</option>
              <option value="USB-D">USB-D</option>
              <option value="PKTUSB">PKT-U</option>
            </select>
          </div>
        </div>

        <div class="me-2">
          <div class="input-group input-group-sm">
            <span class="input-group-text">% Power</span>
            <select
              class="form-control"
              v-model="state.rf_level"
              @click="set_radio_parameter_rflevel()"
              v-bind:class="{
                disabled: state.hamlib_status === 'disconnected',
              }"
            >
              <option value="0">-</option>
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="30">30</option>
              <option value="40">40</option>
              <option value="50">50</option>
              <option value="60">60</option>
              <option value="70">70</option>
              <option value="80">80</option>
              <option value="90">90</option>
              <option value="100">100</option>
            </select>
          </div>
        </div>

        <div class="form-check form-switch">
          <input
            class="form-check-input"
            type="checkbox"
            role="switch"
            id="flexSwitchTuner"
            v-model="state.tuner"
            @change="set_radio_parameter_auto_tuner()"
          />
          <label class="form-check-label" for="flexSwitchTuner">Tuner</label>
        </div>
      </div>
    </div>
  </div>
</template>
