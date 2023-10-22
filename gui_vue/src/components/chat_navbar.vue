<script setup lang="ts">
// @ts-nocheck

import { saveSettingsToFile } from "../js/settingsHandler";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { useChatStore } from "../store/chatStore.js";
const chat = useChatStore(pinia);

import { getRxBuffer } from "../js/sock.js";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
} from "chart.js";

import { Line, Scatter, Bar } from "vue-chartjs";
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

//let dataArray = new Array(25).fill(0)
//dataArray = dataArray.add([-3, 10, 8, 5, 3, 0, -5])
//let dataArray1 = dataArray.shift(2)
//console.log(dataArray1)
//[-3, 10, 8, 5, 3, 0, -5]

try {
  chat.beaconLabelArray = Object.values(
    chat.sorted_beacon_list["DJ2LS-0"].timestamp,
  );
  chat.beaconDataArray = Object.values(chat.sorted_beacon_list["DJ2LS-0"].snr);
} catch (e) {
  console.log(e);

  var beaconLabels = [];
  var beaconData = [];
}

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

function newChat(obj) {
  let callsign = this.newChatCall.value;
  callsign = callsign.toUpperCase();
  chat.callsign_list.add(callsign);
  this.newChatCall.value = "";
}

function syncWithModem() {
  getRxBuffer();
}
</script>

<template>
  <nav class="navbar bg-body-tertiary border-bottom">
    <div class="container">
      <div class="row w-100">
        <div class="col-3 p-0 me-2">
          <div class="input-group bottom-0 m-0 ms-1">
            <input
              class="form-control"
              maxlength="9"
              style="text-transform: uppercase"
              placeholder="callsign"
              @keypress.enter="newChat()"
              ref="newChatCall"
            />
            <button
              class="btn btn-sm btn-outline-success"
              id="createNewChatButton"
              type="button"
              title="Start a new chat (enter dx call sign first)"
              @click="newChat()"
            >
              new chat
              <i class="bi bi-pencil-square" style="font-size: 1.2rem"></i>
            </button>
          </div>
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

        <div class="col-2 ms-2 p-0">
          <div class="input-group mb-0 p-0">
            <button
              type="button"
              class="btn btn-outline-secondary"
              @click="syncWithModem()"
            >
              Modem Sync
            </button>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>
