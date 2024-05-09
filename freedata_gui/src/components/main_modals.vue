<script setup lang="ts">
// @ts-nocheck
// reason for no check is, that we have some mixing of typescript and chart js which seems to be not to be fixed that easy
import { ref, onMounted } from "vue";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useChatStore } from "../store/chatStore.js";
const chat = useChatStore(pinia);

import { useStationStore } from "../store/stationStore.js";
const station = useStationStore(pinia);
import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import {
  getStationInfoByCallsign,
  setStationInfoByCallsign,
} from "../js/stationHandler.js";

import { settingsStore } from "../store/settingsStore.js";

import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { sendModemTestFrame } from "../js/api";
import main_startup_check from "./main_startup_check.vue";
import { newMessage, deleteCallsignFromDB } from "../js/messagesHandler.ts";

function newChat() {
  let newCallsign = chat.newChatCallsign.toUpperCase();
  newMessage(newCallsign, chat.newChatMessage);

  chat.newChatCallsign = "";
  chat.newChatMessage = "";
}

function deleteChat() {
  deleteCallsignFromDB(chat.selectedCallsign);
}

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
import { computed } from "vue";

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

var transmissionSpeedChartOptionsMessageInfo = {
  //type: "line",
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
        drawOnChartArea: false, // only want the grid lines for one axis to show up
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

/*
const stationInfoData = ref({
  name: "",
  city: "",
  age: "",
  radio: "",
  antenna: "",
  email: "",
  website: "",
  socialMedia: {
    facebook: "",
    "twitter-x": "", // Use twitter-x to correspond to the Twitter X icon
    mastodon: "",
    instagram: "",
    linkedin: "",
    youtube: "",
    tiktok: "",
  },
  comments: "",
});
*/

// Function to handle updates and save changes
function updateStationInfo() {
  let mycall = settingsStore.remote.STATION.mycall;
  let myssid = settingsStore.remote.STATION.myssid;
  let fullCall = `${mycall}-${myssid}`;
  console.log("Updating station info:", fullCall);

  setStationInfoByCallsign(fullCall, station.stationInfo.value);
}

// Fixme: this is a dirty hack. Can we make this more VueJS like?
onMounted(() => {
  const modalElement = document.getElementById("stationInfoModal");
  modalElement.addEventListener("show.bs.modal", fetchMyStationInfo);
});

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
            {{ chat.selectedMessageObject["uuid"] }}
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
                <span class="input-group-text" id="basic-addon1">Status</span>
                <span class="input-group-text" id="basic-addon1">{{
                  chat.selectedMessageObject["status"]
                }}</span>
              </div>

              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1">Attempts</span>
                <span class="input-group-text" id="basic-addon1">{{
                  chat.selectedMessageObject["attempt"]
                }}</span>
              </div>
            </div>
          </div>

          <div class="container">
            <div class="d-flex flex-row justify-content-between">
              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1">nacks</span>
                <span class="input-group-text">{{
                  chat.selectedMessageObject["nacks"]
                }}</span>
              </div>
              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1">hmack</span>
                <span class="input-group-text">{{
                  chat.selectedMessageObject["hmac_signed"]
                }}</span>
              </div>
            </div>
          </div>

          <div class="container">
            <div class="d-flex flex-row justify-content-between">
              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1"
                  >Bytes per Minute</span
                >
                <span class="input-group-text" id="basic-addon1">{{
                  chat.selectedMessageObject["bytesperminute"]
                }}</span>
              </div>
              <div class="input-group mb-3">
                <span class="input-group-text" id="basic-addon1"
                  >Duration [s]</span
                >
                <span class="input-group-text">{{
                  parseInt(chat.selectedMessageObject["duration"])
                }}</span>
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

  <!-- HELP MODALS AUDIO -->
  <div
    class="modal fade"
    data-bs-backdrop="static"
    tabindex="-1"
    id="audioHelpModal"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Help</h5>
          <button
            type="button"
            class="btn btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="card mb-3">
            <div class="card-body">
              <div class="input-group input-group-sm mb-1">
                <span class="input-group-text">
                  <i class="bi bi-mic-fill" style="font-size: 1rem"></i>
                </span>
                <select
                  class="form-select form-select-sm"
                  aria-label=".form-select-sm"
                  disabled
                >
                  <!-- 					 					<option selected value="3011">USB Interface</option>-->
                </select>
              </div>
              <p class="card-text">
                Select your audio device for transmitting. It
                <strong>must</strong> be using a sample rate of
                <strong>48000Hz</strong>
              </p>
            </div>
          </div>

          <div class="card">
            <div class="card-body">
              <div class="input-group input-group-sm">
                <span class="input-group-text">
                  <i class="bi bi-volume-up" style="font-size: 1rem"></i>
                </span>
                <select
                  class="form-select form-select-sm"
                  aria-label=".form-select-sm"
                  disabled
                ></select>
              </div>
              <p class="card-text">
                Select your audio device for receiving. It
                <strong>must</strong> be using a sample rate of
                <strong>48000Hz</strong>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <!-- HELP MODALS RIGCONTROL -->
  <div
    class="modal fade"
    data-bs-backdrop="static"
    tabindex="-1"
    id="rigcontrolHelpModal"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Help</h5>
          <button
            type="button"
            class="btn btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">Rig Control</h5>
              <p class="card-text">
                This section is where you configure rig control method (none
                (VOX) or hamlib) for both GUI and TNC. For the best experience
                hamlib control is recommended.
              </p>
            </div>
          </div>

          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">None/Vox</h5>
              <p class="card-text">
                Select "None/Vox" if you want to use Vox for triggering PTT. No
                connection to rigctld will be established. No frequency
                information is availble.
              </p>
            </div>
          </div>

          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">Hamlib</h5>
              <p class="card-text">
                Select "Hamlib" if you want to have more control over your
                radio. Define your hamlib settings in settings, and click the
                start button to start rigctld. You may use the 'PTT test' button
                to ensure rig control is working.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <!-- HELP MODALS STATION -->
  <div
    class="modal fade"
    data-bs-backdrop="static"
    tabindex="-1"
    id="stationHelpModal"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Help</h5>
          <button
            type="button"
            class="btn btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="alert alert-info" role="alert">
            These settings will be saved automatically when changing.
          </div>

          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                <div
                  class="input-group input-group-sm mb-0"
                  data-bs-placement="bottom"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="false"
                  title="Enter your callsign and save it"
                >
                  <span class="input-group-text">
                    <i
                      class="bi bi-person-bounding-box"
                      style="font-size: 1rem"
                    ></i>
                  </span>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="callsign"
                    pattern="[A-Z]*"
                    maxlength="8"
                    style="max-width: 8rem"
                    aria-label="Input group"
                    aria-describedby="btnGroupAddon"
                    disabled
                  />
                  <select
                    class="form-select form-select-sm"
                    aria-label=".form-select-sm"
                    style="max-width: 6rem"
                    disabled
                  >
                    <option selected value="SSID">SSID</option>
                  </select>
                </div>
              </h5>
              <p class="card-text">
                Enter your callsign and SSID. Your callsign can have a maximum
                length of 7 characters
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                <div
                  class="input-group input-group-sm mb-0"
                  data-bs-placement="bottom"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="false"
                  title="Enter your gridsquare and save it"
                >
                  <span class="input-group-text">
                    <i class="bi bi-house-fill" style="font-size: 1rem"></i>
                  </span>
                  <input
                    type="text"
                    class="form-control mr-1"
                    style="max-width: 6rem"
                    placeholder="locator"
                    maxlength="6"
                    aria-label="Input group"
                    aria-describedby="btnGroupAddon"
                    disabled
                  />
                </div>
              </h5>
              <p class="card-text">
                Enter your position as a 4 or 6 digit grid square, also known as
                a maidenhead locator. Six digits are recommended.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <!-- HELP MODALS UPDATER -->
  <div
    class="modal fade"
    data-bs-backdrop="static"
    tabindex="-1"
    id="updaterHelpModal"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Help</h5>
          <button
            type="button"
            class="btn btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">Auto-Updater</h5>
              <p class="card-text">
                The auto updater loads the latest version from Github and
                installs it automatically. You can select the update channel in
                settings. Once an update has been downlaoded, you need to
                confirm the auto-installation and restart.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">Alpha</h5>
              <p class="card-text">
                Alpha releases are more frequent and contain the latest
                features, but are likely to be unstable and introduce bugs.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">Beta</h5>
              <p class="card-text">
                Beta releases are more stable than Alpha releases. They are a
                good tradeoff between latest features and stability. They will
                be updated less often. A beta release has not been released yet.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">Stable</h5>
              <p class="card-text">
                Stable releases are the most stable versions with no known major
                issues. A stable release has not been released yet.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <!-- HELP MODALS LOCAL REMOTE -->
  <div
    class="modal fade"
    data-bs-backdrop="static"
    tabindex="-1"
    id="localRemoteHelpModal"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Help</h5>
          <button
            type="button"
            class="btn btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                <div
                  class="btn-group btn-group-sm me-2"
                  role="group"
                  aria-label="local-remote-switch toggle button group"
                  data-bs-placement="bottom"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="true"
                  title="Select a local or a remote location of your TNC daemon. Normally local is the preferred option."
                >
                  <input
                    type="radio"
                    class="btn-check"
                    name="local-remote-switch"
                    autocomplete="off"
                    checked
                    disabled
                  />
                  <label
                    class="btn btn-sm btn-outline-secondary"
                    for="local-remote-switch1"
                  >
                    <i class="bi bi-pc-display-horizontal"></i>
                    <span class="ms-2 me-2">Local modem</span>
                  </label>
                  <input
                    type="radio"
                    class="btn-check"
                    name="local-remote-switch"
                    autocomplete="off"
                    disabled
                  />
                  <label
                    class="btn btn-sm btn-outline-secondary"
                    for="local-remote-switch2"
                  >
                    <i class="bi bi-ethernet"></i>
                    <span class="ms-2 me-2">Remote modem</span>
                  </label>
                </div>
              </h5>
              <p class="card-text">
                Local / Remote switch. If the TNC is running on the same
                computer as the GUI, select local. Otherwise choose remote and
                enter the IP/Port of where the TNC is running.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                <div class="input-group input-group-sm me-2">
                  <span class="input-group-text">modem ip</span>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="ip address"
                    value="192.168.178.163"
                    maxlength="17"
                    style="width: 8rem"
                    aria-label="Username"
                    aria-describedby="basic-addon1"
                    disabled
                  />
                  <span class="input-group-text">:</span>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="port"
                    value="3000"
                    maxlength="5"
                    max="65534"
                    min="1025"
                    style="width: 4rem"
                    aria-label="Username"
                    aria-describedby="basic-addon1"
                    disabled
                  />
                  <button class="btn btn-sm btn-danger" type="button" disabled>
                    <i class="bi bi-diagram-3" style="font-size: 1rem"></i>
                  </button>
                </div>
              </h5>
              <p class="card-text">
                Remote IP of TNC. Port is port of daemon. The modem port will
                automatically adjusted. ( daemon port - 1 )
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- HELP MODALS START STOP TNC -->
  <div
    class="modal fade"
    data-bs-backdrop="static"
    tabindex="-1"
    id="startStopTNCHelpModal"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Help</h5>
          <button
            type="button"
            class="btn btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                <div class="btn-group" role="group">
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-success"
                    data-bs-toggle="tooltip"
                    data-bs-trigger="hover"
                    data-bs-html="false"
                    title="Start the TNC. Please set your audio and radio settings first!"
                    disabled
                  >
                    <i class="bi bi-play-fill"></i>
                    <span class="ms-2">Start modem</span>
                  </button>
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-danger"
                    data-bs-toggle="tooltip"
                    data-bs-trigger="hover"
                    data-bs-html="false"
                    title="Stop the TNC."
                    disabled
                  >
                    <i class="bi bi-stop-fill"></i>
                    <span class="ms-2">Stop modem</span>
                  </button>
                </div>
              </h5>
              <p class="card-text">
                Start or stop the TNC service. The TNC daemon must be running
                and will work whether the TNC is local or remote.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <!-- HELP MODALS AUDIO LEVEL -->
  <div
    class="modal fade"
    data-bs-backdrop="static"
    tabindex="-1"
    id="audioLevelHelpModal"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Help</h5>
          <button
            type="button"
            class="btn btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                <div class="progress mb-0" style="height: 22px">
                  <div
                    class="progress-bar progress-bar-striped bg-primary force-gpu"
                    role="progressbar"
                    style="width: 5%"
                    aria-valuenow="5"
                    aria-valuemin="0"
                    aria-valuemax="100"
                  ></div>
                  <p
                    class="justify-content-center d-flex position-absolute w-100"
                  >
                    -38 dBFS (Audio Level)
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
              </h5>
              <p class="card-text">
                Represents the level of audio from transceiver. Excessively high
                levels will affect decoding performance negatively.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                <div class="progress mb-0" style="height: 22px">
                  <div
                    class="progress-bar progress-bar-striped bg-primary force-gpu"
                    role="progressbar"
                    style="width: 30%"
                    aria-valuenow="0"
                    aria-valuemin="0"
                    aria-valuemax="100"
                  ></div>
                  <p
                    class="justify-content-center d-flex position-absolute w-100"
                    id="noise_level_value"
                  >
                    -24 S-Meter (dBm)
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
              </h5>
              <p class="card-text">
                Represents noise level of the channel from the transceiver.
                Requires hamlib rig control.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-secondary"
                  @click="sendModemTestFrame()"
                >
                  Tune
                </button>
              </h5>
              <p class="card-text">
                Adjust volume level of outgoing audio to transceiver. For best
                results lower the level so that a minimum amount of ALC is used.
                Can be used in combination with rig's mic/input gain for
                furthrer refinement.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                <button type="button" class="btn btn-sm btn-outline-danger">
                  Record audio
                </button>
              </h5>
              <p class="card-text">Create a recording of current channel</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <!-- HELP MODALS BROADCASTS -->
  <div
    class="modal fade"
    data-bs-backdrop="static"
    tabindex="-1"
    id="broadcastsHelpModal"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Help</h5>
          <button
            type="button"
            class="btn btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="card mb-3">
            <div class="card-body">
              <button
                class="btn btn-sm btn-outline-secondary ms-1"
                type="button"
                disabled
              >
                Ping
              </button>
              <p class="card-text">
                Send a ping to a remote station by entering a callsign and
                optional SSID (-0 will be used if not specified.) Alternatively
                click on a station in the heard station list to populate the
                call sign field. If the remote station decodes the ping it will
                transmit a reply. If able to decode the reply, a signal report
                will be listed in the heard station list.
              </p>
            </div>
          </div>

          <div class="card mb-3">
            <div class="card-body">
              <button
                class="btn btn-sm btn-outline-secondary"
                type="button"
                disabled
              >
                Call CQ
              </button>
              <p class="card-text">Sending out a CQ CQ CQ to the world.</p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <button
                type="button"
                class="btn btn-sm btn-outline-secondary"
                disabled
              >
                <i class="bi bi-soundwave"></i>Toggle beacon
              </button>
              <p class="card-text">
                Sends a periodic broadcast (duration is definable in settings)
                that announces you are available. Check explorer to see other
                active stations that may have decoded your beacon.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <!-- HELP MODALS WATERFALL -->
  <div
    class="modal fade"
    data-bs-backdrop="static"
    tabindex="-1"
    id="waterfallHelpModal"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Help</h5>
          <button
            type="button"
            class="btn btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                Waterfall
                <input
                  type="radio"
                  class="btn-check"
                  name="waterfall-scatter-switch"
                  autocomplete="off"
                  checked
                />
                <label
                  class="btn btn-sm btn-outline-secondary"
                  for="waterfall-scatter-switch1"
                  ><strong><i class="bi bi-water"></i></strong>
                </label>
              </h5>
              <p class="card-text">
                Displays a waterfall for activity of current channel.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                Busy Indicator

                <button class="btn btn-sm btn-success" type="button">
                  busy
                </button>
              </h5>
              <p class="card-text">
                Green when channel is open and changes to red to indicate there
                is activity on the channel.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                Signal Indicator
                <button class="btn btn-sm btn-success" type="button">
                  signal
                </button>
              </h5>
              <p class="card-text">
                Changes to green when Codec2 data is detected on channel.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                Constellation Plot
                <input type="radio" class="btn-check" autocomplete="off" />
                <label class="btn btn-sm btn-outline-secondary"
                  ><strong><i class="bi bi-border-outer"></i></strong>
                </label>
              </h5>
              <p class="card-text">
                Displays a plot of last decoded message. A constellation plot is
                a simple way to represent signal quality.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <h5 class="card-title">
                Speed Chart

                <input type="radio" class="btn-check" autocomplete="off" />
                <label class="btn btn-sm btn-outline-secondary"
                  ><strong><i class="bi bi-graph-up-arrow"></i></strong>
                </label>
              </h5>
              <p class="card-text">
                Shows history of SNR and bit rate of messages.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- HELP MODALS HEARD STATIONS -->
  <div
    class="modal fade"
    data-bs-backdrop="static"
    tabindex="-1"
    id="heardStationsHelpModal"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Station List Help</h5>
          <button
            type="button"
            class="btn btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="card mb-3">
            <div class="card-body">
              <p class="card-text">
                Stations that you've been able to decode will be listed here.
                Details such as time, frequency, message type, call sign,
                location and SNR will be listed. Existing entries are updated if
                they already exist and more detailed history can be viewed in
                chat window for each station.
              </p>
            </div>
          </div>
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
            >
              <div class="input-group mb-1" :key="platform">
                <span class="input-group-text"
                  ><i :class="`bi bi-${platform}`"></i
                ></span>
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
