<script setup lang="ts">
// @ts-nocheck

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { useChatStore } from "../store/chatStore.js";
const chat = useChatStore(pinia);

import { startChatWithNewStation } from "../js/chatHandler";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
} from "chart.js";

import { Bar } from "vue-chartjs";
import { ref, computed } from "vue";
import annotationPlugin from "chartjs-plugin-annotation";

const newChatCall = ref(null);

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
  annotationPlugin,
);

var beaconHistogramOptions = {
  type: "bar",
  bezierCurve: false, //remove curves from your plot
  scaleShowLabels: false, //remove labels
  tooltipEvents: [], //remove trigger from tooltips so they will'nt be show
  pointDot: false, //remove the points markers
  scaleShowGridLines: true, //set to false to remove the grids background
  maintainAspectRatio: true,
  plugins: {
    legend: {
      display: false,
    },
    annotation: {
      annotations: [
        {
          type: "line",
          mode: "horizontal",
          scaleID: "y",
          value: 0,
          borderColor: "darkgrey", // Set the color to dark grey for the zero line
          borderWidth: 0.5, // Set the line width
        },
      ],
    },
  },

  scales: {
    x: {
      position: "bottom",
      display: false,
      min: -10,
      max: 15,
      ticks: {
        display: false,
      },
    },
    y: {
      display: false,
      min: -5,
      max: 10,
      ticks: {
        display: false,
      },
    },
  },
};

const beaconHistogramData = computed(() => ({
  labels: chat.beaconLabelArray,
  datasets: [
    {
      data: chat.beaconDataArray,
      tension: 0.1,
      borderColor: "rgb(0, 255, 0)",

      backgroundColor: function (context) {
        var value = context.dataset.data[context.dataIndex];
        return value >= 0 ? "green" : "red";
      },
    },
  ],
}));

function newChat() {
  let callsign = this.newChatCall.value;
  callsign = callsign.toUpperCase().trim();
  if (callsign === "") return;
  //startChatWithNewStation(callsign);
  //updateAllChat(false);
  this.newChatCall.value = "";
}

</script>

<template>
  <nav class="navbar bg-body-tertiary p-2 border-bottom">
    <div class="container">
      <div class="row w-100">
        <div class="col-3 p-0">
          <button
              class="btn btn-outline-primary w-100"
              data-bs-target="#newChatModal"
              data-bs-toggle="modal"
            >
              <i class="bi bi-pencil-square"> Start a new chat</i>
            </button>


        </div>
        <div class="col-5 ms-2 p-0">
          <!-- right side of chat nav bar-->

          <div class="input-group mb-0 p-0 w-50">
            <button type="button" class="btn btn-outline-secondary" disabled>
              Beacons
            </button>

            <div
              class="form-floating border border-secondary-subtle border-1 rounded-end"
            >
              <Bar
                :data="beaconHistogramData"
                :options="beaconHistogramOptions"
                width="300"
                height="50"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>
