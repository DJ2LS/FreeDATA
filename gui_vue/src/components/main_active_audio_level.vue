<script setup lang="ts">

import {saveSettingsToFile} from '../js/settingsHandler'

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);

import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);

</script>
<template>
<div class="card mb-1">
              <div class="card-header p-1">
                <div class="container">

                  <div class="row">
                    <div class="col-1">
                      <i class="bi bi-volume-up" style="font-size: 1.2rem"></i>
                    </div>
                    <div class="col-5">
                      <strong class="fs-5">Audio level</strong>
                    </div>
                    <div class="col-5">
                      <button
                        type="button"
                        id="audioModalButton"
                        data-bs-toggle="modal"
                        data-bs-target="#audioModal"
                        class="btn btn-sm btn-outline-secondary"
                      >
                        Tune
                      </button>
                      <button
                        type="button"
                        id="startStopRecording"
                        class="btn btn-sm btn-outline-danger"
                      >
                        Record audio
                      </button>
                    </div>
                    <div class="col-1 text-end">
                      <button
                        type="button"
                        id="openHelpModalAudioLevel"
                        data-bs-toggle="modal"
                        data-bs-target="#audioLevelHelpModal"
                        class="btn m-0 p-0 border-0"
                      >
                        <i
                          class="bi bi-question-circle"
                          style="font-size: 1rem"
                        ></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card-body p-2">
                <div class="container">
                  <div class="row">
                    <div class="col-sm">
                      <div class="progress mb-0" style="height: 22px">
                        <div
                          class="progress-bar progress-bar-striped bg-primary force-gpu"
                          id="noise_level"
                          role="progressbar"
                          style="width: {{state.s_meter_strength_percent}}%;"
                          aria-valuenow="{{state.s_meter_strength_percent}}"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <p
                          class="justify-content-center d-flex position-absolute w-100"
                          id="noise_level_value"
                        >
                          S-Meter: {{state.s_meter_strength_raw}} dB
                        </p>
                      </div>
                      <div class="progress mb-0" style="height: 8px">
                        <div
                          class="progress-bar progress-bar-striped bg-warning"
                          role="progressbar"
                          style="width: 1%"
                          aria-valuenow="1"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <div
                          class="progress-bar bg-success"
                          role="progressbar"
                          style="width: 89%"
                          aria-valuenow="50"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <div
                          class="progress-bar progress-bar-striped bg-warning"
                          role="progressbar"
                          style="width: 20%"
                          aria-valuenow="20"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <div
                          class="progress-bar progress-bar-striped bg-danger"
                          role="progressbar"
                          style="width: 29%"
                          aria-valuenow="29"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                      </div>
                    </div>
                    <div class="col-sm">
                      <div class="progress mb-0" style="height: 22px">
                        <div
                          class="progress-bar progress-bar-striped bg-primary force-gpu"
                          id="dbfs_level"
                          role="progressbar"
                          style="width: 0%"
                          aria-valuenow="0"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <p
                          class="justify-content-center d-flex position-absolute w-100"
                          id="dbfs_level_value"
                        >
                          dBFS (Audio Level)
                        </p>
                      </div>
                      <div class="progress mb-0" style="height: 8px">
                        <div
                          class="progress-bar progress-bar-striped bg-warning"
                          role="progressbar"
                          style="width: 1%"
                          aria-valuenow="1"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <div
                          class="progress-bar bg-success"
                          role="progressbar"
                          style="width: 89%"
                          aria-valuenow="50"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <div
                          class="progress-bar progress-bar-striped bg-warning"
                          role="progressbar"
                          style="width: 20%"
                          aria-valuenow="20"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <div
                          class="progress-bar progress-bar-striped bg-danger"
                          role="progressbar"
                          style="width: 29%"
                          aria-valuenow="29"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
</template>