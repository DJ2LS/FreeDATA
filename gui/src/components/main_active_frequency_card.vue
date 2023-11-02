<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { set_frequency, set_mode, set_rf_level } from "../js/sock.js";

function updateFrequencyAndApply(frequency) {
  state.new_frequency = frequency;
  set_frequency(state.new_frequency);
}

function set_hamlib_frequency_manually() {
  set_frequency(state.new_frequency);
}

function set_hamlib_mode() {
  set_mode(state.mode);
}

function set_hamlib_rf_level() {
  set_rf_level(state.rf_level);
}
</script>


<template>

<div class="card border-dark mb-3 h-100">
  <div class="card-body">


<div class="row h-25">
        <div class="col">
<div class="input-group input-group-sm mb-1 w-100 h-100">


                      <button
              class="btn btn-sm w-100 h-100"
            v-bind:class="{
              'btn-danger': state.ptt_state === 'True',
              'btn-outline-danger': state.ptt_state === 'False',
            }"
            type="button"
            style="pointer-events: auto"
            disabled
            data-bs-toggle="tooltip"
            data-bs-placement="bottom"
            data-bs-title="PTT trigger state"
          >
            ON AIR
          </button>

</div>
</div>
</div>

<div class="row mt-1 h-25 w-100">
        <div class="col">
          <div class="input-group w-100 p-0">

              <!-- Dropdown Button -->
              <button
                v-bind:class="{
                  disabled: state.hamlib_status === 'disconnected',
                }"
                class="btn btn-secondary dropdown-toggle"
                type="button"
                id="dropdownMenuButtonFrequency"
                data-bs-toggle="dropdown"
                aria-expanded="false"
              >
                {{ state.frequency }} Hz
              </button>

              <!-- Dropdown Menu -->
              <ul class="dropdown-menu" aria-labelledby="dropdownMenuButtonFrequency">
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
                      @click="set_hamlib_frequency_manually"
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

              <select
                class="form-control w-25"
                v-model="state.mode"
                @click="set_hamlib_mode()"
                v-bind:class="{
                  disabled: state.hamlib_status === 'disconnected',
                }"
              >
                <option value="USB">USB</option>
                <option value="LSB">LSB</option>
                <option value="PKTUSB">PKT-U</option>
                <option value="PKTLSB">PKT-L</option>
                <option value="AM">AM</option>
                <option value="FM">FM</option>
                <option value="PKTFM">PKTFM</option>
              </select>
            </div>
            </div>

      </div>



 <h3>RADIO MODEL</h3>
  </div>
 <div class="card-footer text-center p-0"
 v-bind:class="{
                  'bg-success text-bg-success': state.hamlib_status === 'connected',
                  'bg-danger text-bg-danger': state.hamlib_status === 'disconnected',
                }"

 >



{{ state.hamlib_status }}
              </div>











</div>

</template>
