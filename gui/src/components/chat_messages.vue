<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useChatStore } from "../store/chatStore.js";
const chat = useChatStore(pinia);

import SentMessage from "./chat_messages_sent.vue"; // Import the chat_messages_sent component
import ReceivedMessage from "./chat_messages_received.vue"; // Import the chat_messages_sent component
import ReceivedBroadcastMessage from "./chat_messages_broadcast_received.vue"; // Import the chat_messages_sent component for broadcasts
import SentBroadcastMessage from "./chat_messages_broadcast_sent.vue"; // Import the chat_messages_sent component for broadcasts

//helper function for saving the last messages day for disaplying the day based divider
var prevChatMessageDay = "";

function getDateTime(timestampRaw) {
  let date = new Date(timestampRaw);
  let year = date.getFullYear();
  let month = (date.getMonth() + 1).toString().padStart(2, "0"); // Months are zero-indexed
  let day = date.getDate().toString().padStart(2, "0");
  return `${year}-${month}-${day}`;
}

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
</script>

<template>
  <nav class="navbar sticky-top bg-body-tertiary shadow">
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
  </nav>

  <div class="tab-content p-3" id="nav-tabContent-chat-messages">
    <template
      v-for="(details, callsign, key) in chat.callsign_list"
      :key="callsign"
    >
      <div
        class="tab-pane fade show"
        :class="{ active: key == 0 }"
        :id="`list-${callsign}-messages`"
        role="tabpanel"
        :aria-labelledby="`list-chat-list-${callsign}`"
      >
        <template v-for="item in chat.sorted_chat_list[callsign]">
          <div v-if="prevChatMessageDay !== getDateTime(item.timestamp)">
            <div class="separator my-2">
              {{ (prevChatMessageDay = getDateTime(item.timestamp)) }}
            </div>
          </div>

          <div v-if="item.direction === 'transmit'">
            <sent-message :message="item" />
          </div>

          <div v-else-if="item.direction === 'receive'">
            <received-message :message="item" />
          </div>
          <!--
          <div v-if="item.type === 'broadcast_transmit'">
            <sent-broadcast-message :message="item" />
          </div>
          <div v-else-if="item.type === 'broadcast_received'">
            <received-broadcast-message :message="item" />
          </div>
          -->
        </template>
      </div>
    </template>
  </div>
</template>

<style>
/* https://stackoverflow.com/a/26634224 */
.separator {
  display: flex;
  align-items: center;
  text-align: center;
  color: #6c757d;
}

.separator::before,
.separator::after {
  content: "";
  flex: 1;
  border-bottom: 1px solid #adb5bd;
}

.separator:not(:empty)::before {
  margin-right: 0.25em;
}

.separator:not(:empty)::after {
  margin-left: 0.25em;
}
</style>
