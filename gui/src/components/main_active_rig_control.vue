<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { setRadioParametersFrequency, setRadioParametersMode, setRadioParametersRFLevel } from "../js/api";

function updateFrequencyAndApply(frequency) {
  state.new_frequency = frequency;
  set_radio_parameter_frequency();
}

function set_radio_parameter_frequency(){
    setRadioParametersFrequency(state.new_frequency)
}

function set_radio_parameter_mode(){
    setRadioParametersMode(state.mode)
}

function set_radio_parameter_rflevel(){
    setRadioParametersRFLevel(state.rf_level)
}

</script>

<template>
  <div class="mb-3">
    <div class="card mb-1">
      <div class="card-header p-1">
        <div class="container">
          <div class="row">
            <div class="col-1">
              <i class="bi bi-house-door" style="font-size: 1.2rem"></i>
            </div>
            <div class="col-10">
              <strong class="fs-5 me-2">Radio control</strong>
              <span
                class="badge"
                v-bind:class="{
                  'text-bg-success': state.hamlib_status === 'connected',
                  'text-bg-danger disabled':
                    state.hamlib_status === 'disconnected',
                }"
                >{{ state.hamlib_status }}</span
              >
            </div>
            <div class="col-1 text-end">
              <button
                type="button"
                id="openHelpModalStation"
                data-bs-toggle="modal"
                data-bs-target="#stationHelpModal"
                class="btn m-0 p-0 border-0"
                disabled
              >
                <i class="bi bi-question-circle" style="font-size: 1rem"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="card-body p-2">
        <div class="input-group input-group-sm bottom-0 m-0">
          <div class="me-2">
            <div class="input-group input-group-sm">
              <span class="input-group-text">QRG</span>
              <span class="input-group-text">{{ state.frequency }} Hz</span>

              <!-- Dropdown Button -->
              <button
                v-bind:class="{
                  disabled: state.hamlib_status === 'disconnected',
                }"
                class="btn btn-secondary dropdown-toggle"
                type="button"
                id="dropdownMenuButton"
                data-bs-toggle="dropdown"
                aria-expanded="false"
              ></button>

              <!-- Dropdown Menu -->
              <ul class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                <li>
                  <div class="input-group p-1">
                    <span class="input-group-text">frequency</span>

                    <input
                      v-model="state.new_frequency"
                      style="max-width: 8rem"
                      pattern="[0-9]*"
                      type="text"
                      class="form-control form-control-sm"
                      v-bind:class="{
                        disabled: state.hamlib_status === 'disconnected',
                      }"
                      placeholder="Type frequency..."
                      aria-label="Frequency"
                    />
                    <button
                      class="btn btn-sm btn-outline-success"
                      type="button"
                      @click="updateFrequencyAndApply(state.new_frequency)"
                      v-bind:class="{
                        disabled: state.hamlib_status === 'disconnected',
                      }"
                    >
                      <i class="bi bi-check-square"></i>
                    </button>
                  </div>
                </li>

                <!-- Dropdown Divider -->
                <li><hr class="dropdown-divider" /></li>
                <!-- Dropdown Items -->
                <li>
                  <a
                    class="dropdown-item"
                    href="#"
                    @click="updateFrequencyAndApply(50616000)"
                    ><strong>50616 kHz</strong>&nbsp;
                    <span class="badge bg-secondary">6m | USB</span>&nbsp;
                    <span class="badge bg-info">EU | US</span>
                  </a>
                </li>
                <li>
                  <a
                    class="dropdown-item"
                    href="#"
                    @click="updateFrequencyAndApply(50308000)"
                    ><strong>50308 kHz</strong>&nbsp;
                    <span class="badge bg-secondary">6m | USB</span>&nbsp;
                    <span class="badge bg-info">US</span></a
                  >
                </li>
                <li>
                  <a
                    class="dropdown-item"
                    href="#"
                    @click="updateFrequencyAndApply(28093000)"
                    ><strong>28093 kHz</strong>&nbsp;
                    <span class="badge bg-secondary">10m | USB</span>&nbsp;
                    <span class="badge bg-info">EU | US</span>
                  </a>
                </li>
                <li>
                  <a
                    class="dropdown-item"
                    href="#"
                    @click="updateFrequencyAndApply(27265000)"
                    ><strong>27265 kHz</strong>&nbsp;
                    <span class="badge bg-secondary">11m | USB</span>&nbsp;
                    <span class="badge bg-dark">Ch 26</span></a
                  >
                </li>
                <li>
                  <a
                    class="dropdown-item"
                    href="#"
                    @click="updateFrequencyAndApply(27245000)"
                    ><strong>27245 kHz</strong>&nbsp;
                    <span class="badge bg-secondary">11m | USB</span>&nbsp;
                    <span class="badge bg-dark">Ch 25</span></a
                  >
                </li>
                <li>
                  <a
                    class="dropdown-item"
                    href="#"
                    @click="updateFrequencyAndApply(24908000)"
                    ><strong>24908 kHz</strong>&nbsp;
                    <span class="badge bg-secondary">12m | USB</span>&nbsp;
                    <span class="badge bg-info">EU | US</span>
                  </a>
                </li>
                <li>
                  <a
                    class="dropdown-item"
                    href="#"
                    @click="updateFrequencyAndApply(21093000)"
                    ><strong>21093 kHz</strong>&nbsp;
                    <span class="badge bg-secondary">15m | USB</span>&nbsp;
                    <span class="badge bg-info">EU | US</span>
                  </a>
                </li>
                <li>
                  <a
                    class="dropdown-item"
                    href="#"
                    @click="updateFrequencyAndApply(14093000)"
                    ><strong>14093 kHz</strong>&nbsp;
                    <span class="badge bg-secondary">20m | USB</span>&nbsp;
                    <span class="badge bg-info">EU | US</span>
                  </a>
                </li>
                <li>
                  <a
                    class="dropdown-item"
                    href="#"
                    @click="updateFrequencyAndApply(7053000)"
                    ><strong>7053 kHz</strong>&nbsp;
                    <span class="badge bg-secondary">40m | USB</span>&nbsp;
                    <span class="badge bg-info">EU | US</span>
                  </a>
                </li>
              </ul>
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
              <option value="USB">USB</option>
              <option value="USB-D">USB-D</option>
              <option value="PKTUSB">PKT-U</option>
              </select>
            </div>
          </div>

          <div class="me-2">
            <div class="input-group input-group-sm">
              <span class="input-group-text">Power</span>
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
              <span class="input-group-text">%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
