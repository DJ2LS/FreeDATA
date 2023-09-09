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
                    <div class="col-11">
                      <div
                        class="btn-group btn-group-sm"
                        role="group"
                        aria-label="waterfall-scatter-switch toggle button group"
                      >
                        <input
                          type="radio"
                          class="btn-check"
                          name="waterfall-scatter-switch"
                          id="waterfall-scatter-switch1"
                          autocomplete="off"
                          checked
                        />
                        <label
                          class="btn btn-sm btn-outline-secondary"
                          for="waterfall-scatter-switch1"
                          ><strong><i class="bi bi-water"></i></strong>
                        </label>
                        <input
                          type="radio"
                          class="btn-check"
                          name="waterfall-scatter-switch"
                          id="waterfall-scatter-switch2"
                          autocomplete="off"
                        />
                        <label
                          class="btn btn-sm btn-outline-secondary"
                          for="waterfall-scatter-switch2"
                          ><strong><i class="bi bi-border-outer"></i></strong>
                        </label>
                        <input
                          type="radio"
                          class="btn-check"
                          name="waterfall-scatter-switch"
                          id="waterfall-scatter-switch3"
                          autocomplete="off"
                        />
                        <label
                          class="btn btn-sm btn-outline-secondary"
                          for="waterfall-scatter-switch3"
                          ><strong><i class="bi bi-graph-up-arrow"></i></strong>
                        </label>
                      </div>
                      <div
                        class="btn-group"
                        role="group"
                        aria-label="Busy indicators"
                      >
                        <button
                          class="btn btn-sm btn-secondary"
                          id="channel_busy"
                          type="button"
                          data-bs-placement="top"
                          data-bs-toggle="tooltip"
                          data-bs-trigger="hover"
                          data-bs-html="true"
                          title="Channel busy state: <strong class='text-success'>not busy</strong> / <strong class='text-danger'>busy </strong>"
                        >
                          busy
                        </button>
                        <button
                          class="btn btn-sm btn-outline-secondary"
                          id="c2_busy"
                          type="button"
                          data-bs-placement="top"
                          data-bs-toggle="tooltip"
                          data-bs-trigger="hover"
                          data-bs-html="true"
                          title="Recieving data: illuminates <strong class='text-success'>green</strong> if receiving codec2 data"
                        >
                          signal
                        </button>
                      </div>
                    </div>

                    <div class="col-1 text-end">
                      <button
                        type="button"
                        id="openHelpModalWaterfall"
                        data-bs-toggle="modal"
                        data-bs-target="#waterfallHelpModal"
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
              <div class="card-body p-1" style="height: 200px">
                <!--278px-->
                <canvas
                  id="waterfall"
                  style="position: relative; z-index: 2"
                  class="force-gpu"
                ></canvas>
                <canvas
                  id="scatter"
                  style="position: relative; z-index: 1"
                  class="force-gpu"
                ></canvas>
                <canvas
                  id="chart"
                  style="position: relative; z-index: 1"
                  class="force-gpu"
                ></canvas>
              </div>
            </div>
</template>