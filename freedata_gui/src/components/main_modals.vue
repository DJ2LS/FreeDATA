<script setup>

import { onMounted, computed } from "vue";
import { setActivePinia } from "pinia";
import pinia from "../store/index";
import { useChatStore } from "../store/chatStore.js";
import { useStationStore } from "../store/stationStore.js";
import { getStationInfoByCallsign, setStationInfoByCallsign } from "../js/stationHandler.js";
import { settingsStore } from "../store/settingsStore.js";
import { settingsStore as settings } from "../store/settingsStore.js";
import { sendModemTestFrame } from "../js/api";
import { newMessage, deleteCallsignFromDB } from "../js/messagesHandler.js";
import main_startup_check from "./main_startup_check.vue";

// Chart.js imports
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
import { Line } from "vue-chartjs";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

// Initialize Pinia
setActivePinia(pinia);

// Setup stores
const chat = useChatStore(pinia);
const station = useStationStore(pinia);

// Function to handle new chat messages
function newChat() {
  let newCallsign = chat.newChatCallsign.toUpperCase();
  newMessage(newCallsign, chat.newChatMessage);

  chat.newChatCallsign = "";
  chat.newChatMessage = "";
}

// Function to delete selected chat
function deleteChat() {
  deleteCallsignFromDB(chat.selectedCallsign);
}

// Chart options and data
const skipped = (speedCtx, value) =>
  speedCtx.p0.skip || speedCtx.p1.skip ? value : undefined;
const down = (speedCtx, value) =>
  speedCtx.p0.parsed.y > speedCtx.p1.parsed.y ? value : undefined;

const transmissionSpeedChartOptionsMessageInfo = {
  responsive: true,
  animations: true,
  maintainAspectRatio: false,
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
        drawOnChartArea: false,
      },
    },
    x: { ticks: { beginAtZero: true } },
  },
};

const transmissionSpeedChartDataMessageInfo = computed(() => ({
  labels: chat.arq_speed_list_timestamp,
  datasets: [
    {
      type: "line",
      label: "SNR[dB]",
      data: chat.arq_speed_list_snr,
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
      data: chat.arq_speed_list_bpm,
      borderColor: "rgb(120, 100, 120, 1.0)",
      backgroundColor: "rgba(120, 100, 120, 0.2)",
      order: 0,
      yAxisID: "SPEED",
    },
  ],
}));

// Function to update station info
function updateStationInfo() {
  let mycall = settingsStore.remote.STATION.mycall;
  let myssid = settingsStore.remote.STATION.myssid;
  let fullCall = `${mycall}-${myssid}`;
  console.log("Updating station info:", fullCall);

  setStationInfoByCallsign(fullCall, station.stationInfo.value);
}

// Fix for modal interaction
onMounted(() => {
  const modalElement = document.getElementById("stationInfoModal");
  modalElement.addEventListener("show.bs.modal", fetchMyStationInfo);
  fetchMyStationInfo()
});

// Fetch station info
function fetchMyStationInfo() {

  let mycall = settingsStore.remote.STATION.mycall;
  let myssid = settingsStore.remote.STATION.myssid;
  let fullCall = `${mycall}-${myssid}`;
  getStationInfoByCallsign(fullCall);
}
</script>

<template>
  <main_startup_check />

  <!-- Station Info Modal -->
  <div
    class="modal fade"
    ref="modalEle"
    id="dxStationInfoModal"
    tabindex="-1"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h4 class="p-0 m-0">{{ station.stationInfo.callsign }}</h4>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="alert alert-primary" role="alert">
            <strong> Please note:</strong> This is a preview to show you the
            direction, FreeDATA is going somewhen. For now you can save only
            your personal data, so we can optimize and improve the database. In
            future this data can be requested by a remote station.
          </div>

          <ul>
            <li v-for="(value, key) in station.stationInfo.info" :key="key">
              <strong>{{ key }}:</strong> {{ value }}
            </li>
          </ul>
        </div>

        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- updater release notes-->
  <div
    class="modal fade"
    ref="modalEle"
    id="updaterReleaseNotes"
    tabindex="-1"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <span class="input-group-text" id="updater_last_version"></span>
          <span class="input-group-text ms-1" id="updater_last_update"></span>

          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="modal-dialog modal-dialog-scrollable">
            <div class="" id="updater_release_notes"></div>
          </div>
        </div>

        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- delete chat modal -->
  <div
    class="modal fade"
    ref="modalEle"
    id="deleteChatModal"
    tabindex="-1"
    aria-labelledby="exampleModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="deleteChatModalLabel">
            Sub menu for: {{ chat.selectedCallsign }}
          </h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1"
              >Total Messages</span
            >
            <span class="input-group-text" id="basic-addon1">...</span>
          </div>

          <div class="input-group mb-3">
            <span class="input-group-text" id="basic-addon1">New Messages</span>
            <span class="input-group-text" id="basic-addon1">...</span>
          </div>
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            Close
          </button>
          <button
            type="button"
            class="btn btn-danger"
            @click="deleteChat"
            data-bs-dismiss="modal"
          >
            Delete Chat
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Message Info Modal -->
  <div
    class="modal fade"
    ref="modalEle"
    id="messageInfoModal"
    tabindex="-1"
    aria-labelledby="exampleModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="messageInfoModalLabel">
            {{ chat.selectedCallsign }}
          </h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="container">
            <div class="d-flex flex-row justify-content-between">
              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1">Attempts</span>
                <span class="input-group-text" id="basic-addon1">...</span>
              </div>
            </div>
          </div>

          <div class="container">
            <div class="d-flex flex-row justify-content-between">
              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1">hmack</span>
                <span class="input-group-text">...</span>
              </div>
            </div>
          </div>

          <div class="container">
            <div class="d-flex flex-row justify-content-between">
              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1"
                  >Bytes per Minute</span
                >
                <span class="input-group-text" id="basic-addon1">...</span>
              </div>
              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1"
                  >Duration [s]</span
                >
                <span class="input-group-text">...</span>
              </div>
            </div>
          </div>

          <div class="card mt-2">
            <div class="card-header">Statistics</div>
            <div class="card-body">
              <Line
                :data="transmissionSpeedChartDataMessageInfo"
                :options="transmissionSpeedChartOptionsMessageInfo"
              />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>

  <div
    class="modal fade"
    ref="modalEle"
    id="newChatModal"
    tabindex="-1"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="deleteChatModalLabel">
            Start a new chat
          </h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="alert alert-info" role="alert">
            1. Enter destination callsign
            <br />
            2. Enter a first message
            <br />
            3. Click "START NEW CHAT"
            <br />
            4. Check the chat tab on left side for messages
          </div>

          <div class="form-floating mb-3">
            <input
              type="text"
              class="form-control"
              id="floatingInputDestination"
              placeholder="dxcallsign / destination"
              maxlength="9"
              style="text-transform: uppercase"
              @keypress.enter="newChat()"
              v-model="chat.newChatCallsign"
            />
            <label for="floatingInputDestination"
              >dxcallsign / destination</label
            >
          </div>

          <div class="form-floating">
            <textarea
              class="form-control"
              placeholder="Your first message"
              id="floatingTextareaNewChatMessage"
              style="height: 100px"
              v-model="chat.newChatMessage"
            ></textarea>
            <label for="floatingTextareaNewChatMessage">First message</label>
          </div>
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            Close
          </button>
          <button
            class="btn btn-sm btn-outline-success"
            id="createNewChatButton"
            type="button"
            data-bs-dismiss="modal"
            title="Start a new chat (enter dx call sign first)"
            @click="newChat()"
          >
            START NEW CHAT
            <i class="bi bi-pencil-square" style="font-size: 1.2rem"></i>
          </button>
        </div>
      </div>
    </div>
  </div>





  <!-- AUDIO MODAL -->
  <div
    class="modal fade"
    data-bs-backdrop="static"
    tabindex="-1"
    id="audioModal"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Audio tuning</h5>
          <button
            type="button"
            class="btn btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="alert alert-info" role="alert">
            Adjust audio levels. Value in dB. Default is <strong>0</strong>
          </div>

          <div class="input-group input-group-sm mb-1">
            <span class="input-group-text">Test-Frame</span>
            <button
              type="button"
              id="sendTestFrame"
              @click="sendModemTestFrame()"
              class="btn btn-danger"
            >
              Transmit
            </button>
          </div>
          <div class="input-group input-group-sm mb-1">
            <span class="input-group-text">RX Level</span>
            <span class="input-group-text">{{
              settings.remote.AUDIO.rx_audio_level
            }}</span>
            <span class="input-group-text w-75">
              <input
                type="range"
                class="form-range"
                min="-30"
                max="20"
                step="1"
                id="audioLevelRX"
                @change="onChange"
                v-model.number="settings.remote.AUDIO.rx_audio_level"
            /></span>
          </div>
          <div class="input-group input-group-sm mb-1">
            <span class="input-group-text">TX Level</span>
            <span class="input-group-text">{{
              settings.remote.AUDIO.tx_audio_level
            }}</span>
            <span class="input-group-text w-75">
              <input
                type="range"
                class="form-range"
                min="-30"
                max="20"
                step="1"
                id="audioLevelTX"
                @change="onChange"
                v-model.number="settings.remote.AUDIO.tx_audio_level"
            /></span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- STATION INFO MODAL -->
  <div
    class="modal fade"
    id="stationInfoModal"
    tabindex="-1"
    aria-labelledby="stationInfoModal"
    aria-hidden="true"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">
            {{ settingsStore.remote.STATION.mycall }}
            -
            {{ settingsStore.remote.STATION.myssid }}
          </h1>

          <span class="badge text-bg-secondary ms-3">{{
            settingsStore.remote.STATION.mygrid
          }}</span>

          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="alert alert-primary" role="alert">
            <strong> Please note:</strong> This is a preview to show you the
            direction, FreeDATA is going somewhen. For now you can save only
            your personal data, so we can optimize and improve the database. In
            future this data can be requested by a remote station.
          </div>

          <!-- Name -->
          <div class="input-group mb-1">
            <span class="input-group-text"
              ><i class="bi bi-person-fill"></i
            ></span>
            <input
              type="text"
              class="form-control"
              placeholder="Name"
              v-model="station.stationInfo.info.name"
            />
          </div>

          <!-- City -->
          <div class="input-group mb-1">
            <span class="input-group-text"
              ><i class="bi bi-geo-alt-fill"></i
            ></span>
            <input
              type="text"
              class="form-control"
              placeholder="City"
              v-model="station.stationInfo.info.city"
            />
          </div>

          <!-- Age -->
          <div class="input-group mb-3">
            <span class="input-group-text"
              ><i class="bi bi-person-fill"></i
            ></span>
            <input
              type="text"
              class="form-control"
              placeholder="Age"
              v-model="station.stationInfo.info.age"
            />
          </div>

          <!-- Radio -->
          <div class="input-group mb-1">
            <span class="input-group-text"
              ><i class="bi bi-broadcast-pin"></i
            ></span>
            <input
              type="text"
              class="form-control"
              placeholder="Radio"
              v-model="station.stationInfo.info.radio"
            />
          </div>

          <!-- Antenna -->
          <div class="input-group mb-3">
            <span class="input-group-text"
              ><i class="bi bi-cone-striped"></i
            ></span>
            <input
              type="text"
              class="form-control"
              placeholder="Antenna"
              v-model="station.stationInfo.info.antenna"
            />
          </div>

          <!-- Website -->
          <div class="input-group mb-1">
            <span class="input-group-text"><i class="bi bi-globe"></i></span>
            <input
              type="url"
              class="form-control"
              placeholder="Website"
              v-model="station.stationInfo.info.website"
            />
          </div>

          <!-- Email -->
          <div class="input-group mb-3">
            <span class="input-group-text"
              ><i class="bi bi-envelope-fill"></i
            ></span>
            <input
              type="email"
              class="form-control"
              placeholder="Email"
              v-model="station.stationInfo.info.email"
            />
          </div>

          <!-- Social Media Inputs -->
<div class="mb-3">
  <div
    v-for="(url, platform) in station.stationInfo.info.socialMedia"
    :key="platform"
  >
    <div class="input-group mb-1">
      <span class="input-group-text">
        <i :class="`bi bi-${platform}`"></i>
      </span>
      <input
        type="url"
        class="form-control"
        :placeholder="`${platform.charAt(0).toUpperCase() + platform.slice(1)} URL`"
        v-model="station.stationInfo.info.socialMedia[platform]"
      />
    </div>
  </div>
</div>


          <!-- Comments -->
          <div class="mb-3">
            <label class="input-group-text" for="comments"
              ><i class="bi bi-textarea-resize"></i> Comments</label
            >
            <textarea
              class="form-control"
              rows="3"
              v-model="station.stationInfo.info.comments"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            Close
          </button>
          <button
            type="button"
            class="btn btn-primary"
            @click="updateStationInfo"
          >
            Save changes
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
