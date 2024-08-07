<script setup>
// @ts-nocheck
// disable typescript check because of error with beacon histogram options

import chat_conversations from "./chat_conversations.vue";
import chat_messages from "./chat_messages.vue";
import chat_new_message from "./chat_new_message.vue";

import { getStationInfoByCallsign } from "./../js/stationHandler";

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
} from 'chart.js';

import { Bar } from 'vue-chartjs';
import { watch, nextTick, ref, computed } from 'vue';
import annotationPlugin from 'chartjs-plugin-annotation';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
  annotationPlugin
);

const beaconHistogramOptions = {
  type: 'bar',
  bezierCurve: false, // remove curves from your plot
  scaleShowLabels: false, // remove labels
  tooltipEvents: [], // remove trigger from tooltips so they won't be shown
  pointDot: false, // remove the points markers
  scaleShowGridLines: true, // set to false to remove the grids background
  maintainAspectRatio: true,
  plugins: {
    legend: {
      display: false,
    },
    annotation: {
      annotations: [
        {
          type: 'line',
          mode: 'horizontal',
          scaleID: 'y',
          value: 0,
          borderColor: 'darkgrey', // Set the color to dark grey for the zero line
          borderWidth: 0.5, // Set the line width
        },
      ],
    },
  },

  scales: {
    x: {
      position: 'bottom',
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
      borderColor: 'rgb(0, 255, 0)',

      backgroundColor: function (context) {
        const value = context.dataset.data[context.dataIndex];
        return value >= 0 ? 'green' : 'red';
      },
    },
  ],
}));

const messagesContainer = ref(null);
watch(
  () => chat.scrollTrigger,
  (newVal, oldVal) => {
    nextTick(() => {
    console.log(newVal)
    console.log(oldVal)
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
      }
    });
  }
);
</script>

<template>
  <div class="container-fluid d-flex p-0">
    <!-- Chat Conversations -->
    <div class="bg-light p-0 col-xs-2 col-sm-3 col-md-3 col-lg-4 col-4">
      <div class="container-fluid overflow-auto p-0" style="height: calc(-60px + 100vh);">
        <chat_conversations />
      </div>
      <div class="list-group overflow-auto" id="list-tab-chat" role="tablist"></div>
    </div>

    <!-- Chat Messages -->
    <div class="flex-grow-1 border-start p-0">
      <div class="d-flex flex-column">
        <!-- Top Navbar -->
        <nav class="navbar sticky-top z-0 bg-body-tertiary border-bottom p-1">
          <button
            class="btn btn-sm btn-outline-secondary ms-2 border-0"
            data-bs-target="#dxStationInfoModal"
            data-bs-toggle="modal"
            @click="getStationInfoByCallsign(chat.selectedCallsign)"
            disabled
          >
            <h4 class="p-0 m-0">{{ chat.selectedCallsign }}</h4>
          </button>

          <div class="input-group mb-0 p-0 w-25">
            <button type="button" class="btn btn-outline-secondary" disabled>
              Beacons
            </button>
            <div class="form-floating border border-secondary-subtle border-1 rounded-end">
              <Bar
                :data="beaconHistogramData"
                :options="beaconHistogramOptions"
                width="300"
                height="50"
              />
            </div>
          </div>
        </nav>

        <!-- Chat Messages Area -->
        <div
          class="overflow-auto"
          style="height: calc(100vh - 156px)"
          ref="messagesContainer"
        >
          <chat_messages />
        </div>

        <!-- New Message Area -->
        <chat_new_message />
      </div>
    </div>
  </div>
</template>
