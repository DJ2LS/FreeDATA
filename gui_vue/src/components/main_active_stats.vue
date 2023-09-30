<script setup lang="ts">


import {saveSettingsToFile} from '../js/settingsHandler';

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);

import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);


import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line, Scatter } from 'vue-chartjs'
import { ref, computed } from 'vue';



function selectStatsControl(obj){
switch (obj.delegateTarget.id) {
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



  var transmissionSpeedChartOptions = {
    type: "line",
  };


const scatterChartOptions = {
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          enabled: false,
        },
        annotation: {
          annotations: {
            line1: {
              type: "line",
              yMin: 0,
              yMax: 0,
              borderColor: "rgb(255, 99, 132)",
              borderWidth: 2,
            },
            line2: {
              type: "line",
              xMin: 0,
              xMax: 0,
              borderColor: "rgb(255, 99, 132)",
              borderWidth: 2,
            },
          },
        },
      },
      animations: false,
      scales: {
        x: {
          type: "linear",
          position: "bottom",
          display: true,
          min: -80,
          max: 80,
          ticks: {
            display: false,
          },
        },
        y: {
          display: true,
          min: -80,
          max: 80,
          ticks: {
            display: false,
          },
        },
      },
    };




ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)


const transmissionSpeedChartData = computed(() => ({
 labels: ['-10', '-5', '0', '5', '10'],
  datasets: [
    { data: state.arq_speed_list, label: 'BPM 0%' ,tension: 0.1, borderColor: 'rgb(0, 255, 0)' },
  ]
}
));




const scatterChartData = computed(() => ({
 labels: ['-10', '-5', '0', '5', '10'],
  datasets: [
    { type: 'scatter', data: state.scatter, label: 'PER 0%' ,tension: 0.1, borderColor: 'rgb(0, 255, 0)' },
  ]
  }
));
</script>

<template>
  <div class="card mb-1">
    <div class="card-header p-1">
      <div class="container">
        <div class="row">
          <div class="col-11">
            <div class="btn-group" role="group">
              <div
                class="list-group list-group-horizontal"
                id="list-tab"
                role="tablist"
              >
                <a
                  class="py-1 list-group-item list-group-item-action"
                  id="list-waterfall-list"
                  data-bs-toggle="list"
                  href="#list-waterfall"
                  role="tab"
                  aria-controls="list-waterfall"
                  v-bind:class="{ 'active' : settings.spectrum === 'waterfall'}"
                  @click="selectStatsControl($event)"
                  ><strong><i class="bi bi-water"></i></strong
                ></a>
                <a
                  class="py-1 list-group-item list-group-item-action"
                  id="list-scatter-list"
                  data-bs-toggle="list"
                  href="#list-scatter"
                  role="tab"
                  aria-controls="list-scatter"
                  v-bind:class="{ 'active' : settings.spectrum === 'scatter'}"
                  @click="selectStatsControl($event)"
                  ><strong><i class="bi bi-border-outer"></i></strong
                ></a>
                <a
                  class="py-1 list-group-item list-group-item-action"
                  id="list-chart-list"
                  data-bs-toggle="list"
                  href="#list-chart"
                  role="tab"
                  aria-controls="list-chart"
                  v-bind:class="{ 'active' : settings.spectrum === 'chart'}"
                  @click="selectStatsControl($event)"
                  ><strong><i class="bi bi-graph-up-arrow"></i></strong
                ></a>
              </div>
            </div>
            <div class="btn-group" role="group" aria-label="Busy indicators">
              <button
                class="btn btn-sm ms-2 disabled"
                type="button"
                data-bs-placement="top"
                data-bs-toggle="tooltip"
                data-bs-trigger="hover"
                data-bs-html="true"
                v-bind:class="{ 'btn-warning' : state.channel_busy === 'True', 'btn-outline-secondary' : state.channel_busy === 'False'}"
                title="Channel busy state: <strong class='text-success'>not busy</strong> / <strong class='text-danger'>busy </strong>"
              >
                busy
              </button>
              <button
                class="btn btn-sm disabled"
                type="button"
                data-bs-placement="top"
                data-bs-toggle="tooltip"
                data-bs-trigger="hover"
                data-bs-html="true"
                title="Recieving data: illuminates <strong class='text-success'>green</strong> if receiving codec2 data"
                v-bind:class="{ 'btn-success' : state.is_codec2_traffic === 'True', 'btn-outline-secondary' : state.is_codec2_traffic === 'False'}"
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
              <i class="bi bi-question-circle" style="font-size: 1rem"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="card-body p-1" style="height: 200px">
      <div class="tab-content" id="nav-stats-tabContent">
        <div
          class="tab-pane fade"
          v-bind:class="{ 'show active' : settings.spectrum === 'waterfall'}"
          id="list-waterfall"
          role="stats_tabpanel"
          aria-labelledby="list-waterfall-list"
        >
          <canvas
            id="waterfall"
            style="position: relative; z-index: 2"
            class="force-gpu"
          ></canvas>
        </div>
        <div
          class="tab-pane fade"
          v-bind:class="{ 'show active' : settings.spectrum === 'scatter'}"
          id="list-scatter"
          role="tabpanel"
          aria-labelledby="list-scatter-list"
        >
          <Line :data="scatterChartData" :options="scatterChartOptions" />
        </div>
        <div
          class="tab-pane fade"
          v-bind:class="{ 'show active' : settings.spectrum === 'chart'}"
          id="list-chart"
          role="tabpanel"
          aria-labelledby="list-chart-list"
        >
          <Line
            :data="transmissionSpeedChartData"
            :options="transmissionSpeedChartOptions"
          />
        </div>
      </div>

      <!--278px-->
    </div>
  </div>
</template>
