<script setup lang="ts">

import {saveSettingsToFile} from '../js/settingsHandler'

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);

import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);

function selectStatsControl(obj){
console.log(event.target.id)
switch (event.target.id) {
  case 'list-waterfall-list':
    settings.spectrum = "waterfall"
    break;
  case 'list-scatter-list':
    settings.spectrum = "scatter"
    break;
  case 'list-chart-list':
    settings.spectrum = "chart"
    break;
  default:
    settings.spectrum = "waterfall"

}
    saveSettingsToFile()


}


</script>
<template>
<div class="card mb-1">
              <div class="card-header p-1">




                <div class="container">
                  <div class="row">
                    <div class="col-11">
                    <div
                        class="btn-group"
                        role="group"
                        aria-label="Busy indicators"
                      >

                       <div class="list-group list-group-horizontal" id="list-tab" role="tablist">
      <a class="py-1 list-group-item list-group-item-action" id="list-waterfall-list" data-bs-toggle="list" href="#list-waterfall" role="tab" aria-controls="list-home" v-bind:class="{ 'active' : settings.spectrum === 'waterfall'}" @click="selectStatsControl()"><strong><i class="bi bi-water" ></i></strong></a>
      <a class="py-1 list-group-item list-group-item-action" id="list-scatter-list" data-bs-toggle="list" href="#list-scatter" role="tab" aria-controls="list-profile" v-bind:class="{ 'active' : settings.spectrum === 'scatter'}" @click="selectStatsControl()"><strong><i class="bi bi-border-outer" ></i></strong></a>
      <a class="py-1 list-group-item list-group-item-action" id="list-chart-list" data-bs-toggle="list" href="#list-chart" role="tab" aria-controls="list-messages" v-bind:class="{ 'active' : settings.spectrum === 'chart'}" @click="selectStatsControl()"><strong><i class="bi bi-graph-up-arrow" ></i></strong></a>
    </div>

                        <button
                          class="btn btn-sm btn-secondary ms-2 "
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


               <div class="tab-content" id="nav-stats-tabContent">
                  <div class="tab-pane fade" v-bind:class="{ 'show active' : settings.spectrum === 'waterfall'}" id="list-waterfall" role="stats_tabpanel" aria-labelledby="list-waterfall-list"><canvas
                  id="waterfall"
                  style="position: relative; z-index: 2"
                  class="force-gpu"
                ></canvas></div>
                  <div class="tab-pane fade" v-bind:class="{ 'show active' : settings.spectrum === 'scatter'}" id="list-scatter" role="tabpanel" aria-labelledby="list-scatter-list"> <canvas
                  id="scatter"
                  style="position: relative; z-index: 1"
                  class="force-gpu"
                ></canvas></div>
                  <div class="tab-pane fade" v-bind:class="{ 'show active' : settings.spectrum === 'chart'}" id="list-chart" role="tabpanel" aria-labelledby="list-chart-list">   <canvas
                  id="chart"
                  style="position: relative; z-index: 1"
                  class="force-gpu"
                ></canvas></div>
                </div>





                <!--278px-->



              </div>
            </div>
</template>