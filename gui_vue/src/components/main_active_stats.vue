<script setup lang="ts">
import { saveSettingsToFile } from "../js/settingsHandler";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line, Scatter } from "vue-chartjs";
import { ref, computed } from "vue";

function selectStatsControl(obj) {
  switch (obj.delegateTarget.id) {
    case "list-waterfall-list":
      settings.spectrum = "waterfall";
      break;
    case "list-scatter-list":
      settings.spectrum = "scatter";
      break;
    case "list-chart-list":
      settings.spectrum = "chart";
      break;
    default:
      settings.spectrum = "waterfall";
  }
  saveSettingsToFile();
}

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

// https://www.chartjs.org/docs/latest/samples/line/segments.html
const skipped = (speedCtx, value) =>
  speedCtx.p0.skip || speedCtx.p1.skip ? value : undefined;
const down = (speedCtx, value) =>
  speedCtx.p0.parsed.y > speedCtx.p1.parsed.y ? value : undefined;

var transmissionSpeedChartOptions = {
  type: "line",
  responsive: true,
  animations: true,
  cubicInterpolationMode: "monotone",
  tension: 0.4,
  scales: {
    SNR: {
      type: "linear",
      ticks: { beginAtZero: false, color: "rgb(255, 99, 132)" },
      position: "right",
    },
    SPEED: {
      type: "linear",
      ticks: { beginAtZero: false, color: "rgb(120, 100, 120)" },
      position: "left",
      grid: {
        drawOnChartArea: false, // only want the grid lines for one axis to show up
      },
    },
    x: { ticks: { beginAtZero: true } },
  },
};

const transmissionSpeedChartData = computed(() => ({
  labels: state.arq_speed_list_timestamp,
  datasets: [
    {
      type: "line",
      label: "SNR[dB]",
      data: state.arq_speed_list_snr,
      borderColor: "rgb(75, 192, 192, 1.0)",
      pointRadius: 1,
      segment: {
        borderColor: (speedCtx) =>
          skipped(speedCtx, "rgb(0,0,0,0.4)") ||
          down(speedCtx, "rgb(192,75,75)"),
        borderDash: (speedCtx) => skipped(speedCtx, [3, 3]),
      },
      spanGaps: true,
      backgroundColor: "rgba(75, 192, 192, 0.2)",
      order: 1,
      yAxisID: "SNR",
    },
    {
      type: "bar",
      label: "Speed[bpm]",
      data: state.arq_speed_list_bpm,
      borderColor: "rgb(120, 100, 120, 1.0)",
      backgroundColor: "rgba(120, 100, 120, 0.2)",
      order: 0,
      yAxisID: "SPEED",
    },
  ],
}));

const scatterChartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  scales: {
    x: {
      type: "linear",
      position: "bottom",
      grid: {
        display: true,
        lineWidth: 1, // Set the line width for x-axis grid lines
      },
      ticks: {
        display: false,
      },
    },
    y: {
      type: "linear",
      position: "left",
      grid: {
        display: true,
        lineWidth: 1, // Set the line width for y-axis grid lines
      },
      ticks: {
        display: false,
      },
    },
  },
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      enabled: false,
    },
  },
};

// dummy data
//state.scatter = [{"x":"166","y":"46"},{"x":"-193","y":"-139"},{"x":"-165","y":"-291"},{"x":"311","y":"-367"},{"x":"389","y":"199"},{"x":"78","y":"372"},{"x":"242","y":"-431"},{"x":"-271","y":"-248"},{"x":"28","y":"-130"},{"x":"-20","y":"187"},{"x":"74","y":"362"},{"x":"-316","y":"-229"},{"x":"-180","y":"261"},{"x":"321","y":"360"},{"x":"438","y":"-288"},{"x":"378","y":"-94"},{"x":"462","y":"-163"},{"x":"-265","y":"248"},{"x":"210","y":"314"},{"x":"230","y":"-320"},{"x":"261","y":"-244"},{"x":"-283","y":"-373"}]

const scatterChartData = computed(() => ({
  datasets: [
    {
      type: "scatter",
      fill: true,
      data: state.scatter,
      label: "Scatter",
      tension: 0.1,
      borderColor: "rgb(0, 255, 0)",
    },
  ],
}));
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
                  v-bind:class="{ active: settings.spectrum === 'waterfall' }"
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
                  v-bind:class="{ active: settings.spectrum === 'scatter' }"
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
                  v-bind:class="{ active: settings.spectrum === 'chart' }"
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
                v-bind:class="{
                  'btn-warning': state.channel_busy === 'True',
                  'btn-outline-secondary': state.channel_busy === 'False',
                }"
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
                v-bind:class="{
                  'btn-success': state.is_codec2_traffic === 'True',
                  'btn-outline-secondary': state.is_codec2_traffic === 'False',
                }"
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
          v-bind:class="{ 'show active': settings.spectrum === 'waterfall' }"
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
          v-bind:class="{ 'show active': settings.spectrum === 'scatter' }"
          id="list-scatter"
          role="tabpanel"
          aria-labelledby="list-scatter-list"
        >
          <Scatter :data="scatterChartData" :options="scatterChartOptions" />
        </div>
        <div
          class="tab-pane fade"
          v-bind:class="{ 'show active': settings.spectrum === 'chart' }"
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
