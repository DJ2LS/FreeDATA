<script setup>
   import { onMounted, computed } from "vue";
   import { setActivePinia } from "pinia";
   import pinia from "../store/index";
   import { useChatStore } from "../store/chatStore.js";
   import { useBroadcastStore } from "../store/broadcastStore.js";
   import { useStationStore } from "../store/stationStore.js";
   import { getStationInfoByCallsign, setStationInfoByCallsign } from "../js/stationHandler.js";
   import { settingsStore } from "../store/settingsStore.js";
   import { settingsStore as settings, onChange } from "../store/settingsStore.js";
   import {getFreedataBroadcastsPerDomain, getFreedataDomains, sendModemTestFrame, sendSineTone} from "../js/api";
   import { newMessage, deleteCallsignFromDB } from "../js/messagesHandler.js";
   import main_startup_check from "./main_startup_check.vue";
   import {deleteBroadcastDomainFromDB, newBroadcastMessage} from "../js/broadcastsHandler";

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
     BarElement,
   } from "chart.js";
   import { Line, Bar } from "vue-chartjs";
   import DOMPurify from "dompurify";
   import {marked} from "marked";

   // Register Chart.js components
   ChartJS.register(
     CategoryScale,
     LinearScale,
     PointElement,
     LineElement,
     Title,
     Tooltip,
     Legend,
     BarElement,
   );
   
   // Initialize Pinia
   setActivePinia(pinia);
   
   // Setup stores
   const chat = useChatStore(pinia);
   const station = useStationStore(pinia);
   const broadcast = useBroadcastStore(pinia);
   
   // Function to handle new chat messages
   function newChat() {
     let newCallsign = chat.newChatCallsign.toUpperCase();
     newMessage(newCallsign, chat.newChatMessage);
   
     chat.newChatCallsign = "";
     chat.newChatMessage = "";
   }

      // Function to handle new broadcast messages
   function newBroadcast() {
     broadcast.inputText = broadcast.inputText.trim();
      if (broadcast.inputText.length === 0) return;
      const sanitizedInput = DOMPurify.sanitize(marked.parse(broadcast.inputText));
      const base64data = btoa(sanitizedInput);
      const params = {
    origin: settings.remote.STATION.mycall + '-' + settings.remote.STATION.myssid,
    domain: broadcast.newDomain && broadcast.newDomain.trim() ? broadcast.newDomain : "GLOBAL-1",
    gridsquare: settings.remote.STATION.mygrid,
    type: broadcast.newMessageType && broadcast.newMessageType.trim() ? broadcast.newMessageType : "MESSAGE",
    priority: 1,
    data: base64data
  };

     newBroadcastMessage(params);
     setTimeout(() => {
        getFreedataDomains()
        getFreedataBroadcastsPerDomain(broadcast.newDomain)

        broadcast.selectedDomain = broadcast.newDomain;
        broadcast.newDomain = "";
     }, 1000);

   }
   
   // Function to delete selected chat
   function deleteChat() {
     deleteCallsignFromDB(chat.selectedCallsign);
   }

      function deleteDomain() {
     deleteBroadcastDomainFromDB(broadcast.selectedDomain);
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
         ticks: { beginAtZero: false, color: "rgb(255, 99, 132, 1.0)" },
         position: "right",
       },
       SPEED: {
         type: "linear",
         ticks: { beginAtZero: false, color: "rgb(120, 100, 120, 1.0)" },
         position: "left",
         grid: {
           drawOnChartArea: false,
         },
       },
       x: { ticks: { beginAtZero: true } },
     },
   };

// Utility function to format timestamps
function formatTimestamp(isoTimestamp) {
  const date = new Date(isoTimestamp);
  return date.toLocaleTimeString('en-US', { hour12: false });
}

function formatTimestampFull(isoTimestamp) {
  const date = new Date(isoTimestamp * 1000);
  return date.toLocaleString('en-US', {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
  });
}


const transmissionSpeedChartDataMessageInfo = computed(() => ({
  labels: Object.values(chat.messageInfoById?.statistics?.time_histogram || {}).map(formatTimestamp),
  datasets: [
    {
      type: 'line',
      label: 'SNR[dB]',
      data: Object.values(chat.messageInfoById?.statistics?.snr_histogram || {}),
      borderColor: 'rgb(255, 99, 132)',
      pointRadius: 1,
      segment: {
        borderColor: (speedCtx) =>
          skipped(speedCtx, 'rgb(0,0,0,0.4)') || down(speedCtx, 'rgb(192,75,75)'),
        borderDash: (speedCtx) => skipped(speedCtx, [3, 3]),
      },
      spanGaps: true,
      backgroundColor: 'rgb(255, 99, 132)',
      order: 1,
      yAxisID: 'SNR',
    },
    {
      type: 'bar',
      label: 'Speed[bpm]',
      data: Object.values(chat.messageInfoById?.statistics?.bpm_histogram || {}),
      borderColor: 'rgb(120, 100, 120, 1.0)',
      pointRadius: 1,
      backgroundColor: 'rgba(120, 100, 120, 0.2)',
      order: 0,
      yAxisID: 'SPEED',
    },
  ],
}));


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
      display: true,
      min: -10,
      max: 15,
      ticks: {
        display: false,
      },
      text: 'timestamp',
    },
    y: {
      display: true,
      min: -15,
      max: 15,
      ticks: {
        display: true,
      },
      text: 'SNR',
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



   
   // Function to update station info
   function updateStationInfo() {
     let mycall = settingsStore.remote.STATION.mycall;
     let myssid = settingsStore.remote.STATION.myssid;
     let fullCall = `${mycall}-${myssid}`;
     console.log("Updating station info:", fullCall, station.stationInfo);

     setStationInfoByCallsign(fullCall, station.stationInfo);
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
     console.log("fetching my station info:", fullCall)
     getStationInfoByCallsign(fullCall);
   }





</script>
<template>
  <main_startup_check />
  <!-- Station Info Modal -->
  <div
    id="dxStationInfoModal"
    ref="modalElement"
    class="modal fade"
    tabindex="-1"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h4 class="p-0 m-0">
            {{ station.stationInfo.callsign }}
          </h4>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          />
        </div>
        <div class="modal-body">
          <div
            class="alert alert-primary"
            role="alert"
          >
            <strong> Please note:</strong> This is a preview to show you the
            direction, FreeDATA is going somewhen. For now you can save only
            your personal data, so we can optimize and improve the database. In
            future this data can be requested by a remote station.
          </div>
          <ul>
            <li
              v-for="(value, key) in station.stationInfo.info"
              :key="key"
            >
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
    id="updaterReleaseNotes"
    ref="modalElement"
    class="modal fade"
    tabindex="-1"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <span
            id="updater_last_version"
            class="input-group-text"
          />
          <span
            id="updater_last_update"
            class="input-group-text ms-1"
          />
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          />
        </div>
        <div class="modal-body">
          <div class="modal-dialog modal-dialog-scrollable">
            <div
              id="updater_release_notes"
              class=""
            />
          </div>
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            {{ $t('modals.close') }}
          </button>
        </div>
      </div>
    </div>
  </div>
  <!-- delete chat modal -->
  <div
    id="deleteChatModal"
    ref="modalElement"
    class="modal fade"
    tabindex="-1"
    aria-labelledby="exampleModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1
            id="deleteChatModalLabel"
            class="modal-title fs-5"
          >
            {{ chat.selectedCallsign }} {{ $t('modals.options') }}
          </h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          />
        </div>
        <div class="modal-body">
          <div class="card">
            <div class="card-header">
              <strong>{{ $t('modals.beaconhistogram') }}</strong>
            </div>
            <div class="card-body">
              <Bar
                :data="beaconHistogramData"
                :options="beaconHistogramOptions"
                width="300"
                height="100"
              />
            </div>
          </div>


          <div class="card mt-3">
            <div class="card-header">
              <strong>{{ $t('modals.furtheroptions') }}</strong>
            </div>
            <div class="card-body">
              <button
                type="button"
                class="btn btn-danger"
                data-bs-dismiss="modal"
                @click="deleteChat"
              >
                {{ $t('modals.deletechat') }}
              </button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            {{ $t('modals.close') }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <div
    id="deleteBroadcastModal"
    ref="deleteBroadcastModalElement"
    class="modal fade"
    tabindex="-1"
    aria-labelledby="exampleModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1
            id="deleteBroadcastModalLabel"
            class="modal-title fs-5"
          >
            {{ chat.selectedCallsign }} {{ $t('modals.options') }}
          </h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          />
        </div>
        <div class="modal-body">


          <div class="card mt-3">
            <div class="card-header">
              <strong>{{ $t('modals.furtheroptions') }}</strong>
            </div>
            <div class="card-body">
              <button
                type="button"
                class="btn btn-danger"
                data-bs-dismiss="modal"
                @click="deleteDomain"
              >
                {{ $t('modals.deletebroadcastdomain') }}
              </button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            {{ $t('modals.close') }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Message Info Modal -->
  <div
    id="messageInfoModal"
    ref="modalElement"
    class="modal fade"
    tabindex="-1"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1
            id="messageInfoModalLabel"
            class="modal-title fs-5"
          >
            {{ chat.selectedCallsign }}
          </h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          />
        </div>
        <div class="modal-body">
          <div class="card mt-2">
            <div class="card-header">
              {{ $t('general.statistics') }}
            </div>
            <div class="card-body">
              <div class="container">
                <div class="row">
                  <!-- Bytes per Minute -->
                  <div class="auto mb-2">
                    <div class="input-group">
                      <span class="input-group-text">{{ $t('general.speed') }}</span>
                      <span class="input-group-text">{{ chat.messageInfoById?.statistics?.bytes_per_minute ?? 'NaN' }} bpm / {{ chat.messageInfoById?.statistics?.bits_per_second ?? 'NaN' }} bps</span>
                    </div>
                  </div>
                </div>

                <div class="row">
                  <!-- Duration [s] -->
                  <div class="col-auto mb-2">
                    <div class="input-group">
                      <span class="input-group-text">{{ $t('general.duration') }}</span>
                      <span class="input-group-text">{{ Math.round(chat.messageInfoById?.statistics?.duration) ?? 'NaN' }}</span>
                    </div>
                  </div>
                  <!-- Size -->
                  <div class="col-auto mb-2">
                    <div class="input-group">
                      <span class="input-group-text">{{ $t('general.size') }}</span>
                      <span class="input-group-text">{{ chat.messageInfoById?.statistics?.total_bytes ?? 'NaN' }} {{ $t('general.bytes') }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>


          <div class="card mt-2">
            <div class="card-header">
              {{ $t('general.chart') }}
            </div>
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
            {{ $t('modals.close') }}
          </button>
        </div>
      </div>
    </div>
  </div>

   <div
    id="broadcastMessageInfoModal"
    ref="broadcastMessageInfoModalElement"
    class="modal fade"
    tabindex="-1"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1
            id="broadcastMessageInfoModalLabel"
            class="modal-title fs-5"
          >
            {{ broadcast.selectedMessage?.origin?? 'NaN' }} - {{formatTimestampFull(broadcast.selectedMessage?.timestamp) ?? 'NaN' }}
          </h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          />
        </div>
        <div class="modal-body">

          <div class="card mt-2">
            <div class="card-header">
              {{ $t('broadcast.general') }}
            </div>
            <div class="card-body">
              <div class="container">
                <div class="row">
                  <div class="input-group">
                      <span class="input-group-text">{{ $t('broadcast.id') }}</span>
                      <span class="input-group-text">{{ broadcast.selectedMessage?.id ?? 'NaN' }}</span>
                  </div>

                                    <div class="input-group">
                      <span class="input-group-text">{{ $t('broadcast.msg_type') }}</span>
                      <span class="input-group-text">{{ broadcast.selectedMessage?.msg_type ?? 'NaN' }}</span>
                  </div>

                  <div class="input-group">
                      <span class="input-group-text">{{ $t('broadcast.timestamp') }}</span>
                      <span class="input-group-text">{{ formatTimestampFull(broadcast.selectedMessage?.timestamp) ?? 'NaN' }}</span>
                  </div>

                                    <div class="input-group">
                      <span class="input-group-text">{{ $t('broadcast.nexttransmission_at') }}</span>
                      <span class="input-group-text">{{ formatTimestampFull(broadcast.selectedMessage?.nexttransmission_at) ?? 'NaN' }}</span>
                  </div>

                                    <div class="input-group">
                      <span class="input-group-text">{{ $t('broadcast.expires_at') }}</span>
                      <span class="input-group-text">{{ formatTimestampFull(broadcast.selectedMessage?.expires_at) ?? 'NaN' }}</span>
                  </div>
                </div>
                </div>
              </div>
            </div>

          <div class="card mt-2">
            <div class="card-header">
              {{ $t('broadcast.sender') }}
            </div>
            <div class="card-body">
              <div class="container">
                <div class="row">
                  <div class="input-group">
                      <span class="input-group-text">{{ $t('broadcast.origin') }}</span>
                      <span class="input-group-text">{{ broadcast.selectedMessage?.origin ?? 'NaN' }}</span>
                  </div>

                  <div class="input-group">
                      <span class="input-group-text">{{ $t('broadcast.gridsquare') }}</span>
                      <span class="input-group-text">{{ broadcast.selectedMessage?.gridsquare ?? 'NaN' }}</span>
                  </div>
                </div>
                </div>
              </div>
            </div>


        </div>

        <div class="card mt-2">
            <div class="card-header">
              {{ $t('broadcast.data') }}
            </div>
            <div class="card-body">
              <div class="container">
                <div class="row">

                                    <div class="input-group">
                      <span class="input-group-text">{{ $t('broadcast.payload_size') }}</span>
                      <span class="input-group-text">{{ broadcast.selectedMessage?.payload_size ?? 'NaN' }}</span>
                  </div>

                  <div class="input-group">
                      <span class="input-group-text">{{ $t('broadcast.bursts') }}</span>
                      <span class="input-group-text">{{ broadcast.selectedMessage?.total_bursts ?? 'NaN' }}</span>
                  </div>

                </div>
                </div>
              </div>
            </div>


        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            {{ $t('modals.close') }}
          </button>
        </div>
      </div>
    </div>
  </div>


  <div
    id="newChatModal"
    ref="modalElement"
    class="modal fade"
    tabindex="-1"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1
            id="deleteChatModalLabel"
            class="modal-title fs-5"
          >
            {{ $t('modals.startnewchat') }}
          </h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          />
        </div>
        <div class="modal-body">
          <div
            class="alert alert-info"
            role="alert"
          >
            1. {{ $t('modals.newchatline1') }}
            <br>
            2. {{ $t('modals.newchatline2') }}
            <br>
            3. {{ $t('modals.newchatline3') }}
            <br>
            4. {{ $t('modals.newchatline4') }}
          </div>
          <div class="form-floating mb-3">
            <input
              id="floatingInputDestination"
              v-model="chat.newChatCallsign"
              type="text"
              class="form-control"
              placeholder="dxcallsign / destination"
              maxlength="9"
              style="text-transform: uppercase"
              @keypress.enter="newChat()"
            >
            <label for="floatingInputDestination">{{ $t('general.dxcallsign') }} / {{ $t('general.destination') }}</label>
          </div>
          <div class="form-floating">
            <textarea
              id="floatingTextareaNewChatMessage"
              v-model="chat.newChatMessage"
              class="form-control"
              placeholder="Your first message"
              style="height: 100px"
            />
            <label for="floatingTextareaNewChatMessage">{{ $t('modals.firstmessage') }}</label>
          </div>
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            {{ $t('modals.close') }}
          </button>
          <button
            id="createNewChatButton"
            class="btn btn-sm btn-outline-success"
            type="button"
            data-bs-dismiss="modal"
            data-bs-trigger="hover"
            :title="$t('modals.startnewchat2')"
            @click="newChat()"
          >
            {{ $t('modals.startnewchat').toUpperCase() }}
            <i
              class="bi bi-pencil-square"
              style="font-size: 1.2rem"
            />
          </button>
        </div>
      </div>
    </div>
  </div>


  <div
    id="newBroadcastModal"
    ref="newBroadcastModalElement"
    class="modal fade"
    tabindex="-1"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">
            {{ $t('modals.startnewbroadcast') }}
          </h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          />
        </div>

        <div class="modal-body">
          <!-- Domain selection -->
          <div class="mb-3">
            <label for="domainInput" class="form-label">Domain</label>
            <input
              id="domainInput"
              list="domainOptions"
              class="form-control"
              v-model="broadcast.newDomain"
              placeholder="Enter or select a domain"
            />
            <datalist id="domainOptions">
              <option value="EUROPE-1">EUROPE-1</option>
              <option value="ASIA-1">ASIA-1</option>
              <option value="NA-1">NA-1</option>
              <option value="SA-1">SA-1</option>
              <option value="AFRICA-1">AFRICA-1</option>
            </datalist>
          </div>

          <!-- Type selection -->
          <div class="mb-3">
            <label for="typeSelect" class="form-label">Type</label>
            <select
              id="typeSelect"
              class="form-select"
              v-model="broadcast.newMessageType"
            >
              <option value="MESSAGE">MESSAGE</option>
            </select>
          </div>

          <!-- Priority selection -->
          <!--
          <div class="mb-3">
            <label for="prioritySelect" class="form-label">Priority</label>
            <select
              id="prioritySelect"
              class="form-select"
              v-model="broadcast.newPriority"
            >
              <option value="1" select>Normal (1)</option>
              <option value="0">Low (0)</option>
              <option value="2">High (2)</option>
            </select>
          </div>
        -->
          <!-- Message content -->
          <div class="mb-3">
            <label for="messageTextarea" class="form-label">Message</label>
            <textarea
              id="messageTextarea"
              class="form-control"
              rows="5"
              v-model="broadcast.inputText"
              placeholder="Enter your message..."
            />
          </div>
        </div>

        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            {{ $t('modals.close') }}
          </button>
          <button
            type="button"
            class="btn btn-primary"
            data-bs-dismiss="modal"
            data-bs-trigger="hover"
            @click="newBroadcast"
          >
            Send Broadcast
          </button>
        </div>
      </div>
    </div>
  </div>



  <!-- AUDIO MODAL -->
  <div
    id="audioModal"
    class="modal fade"
    data-bs-backdrop="static"
    tabindex="-1"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            {{ $t('modals.audiotuning') }}
          </h5>
          <button
            type="button"
            class="btn btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          />
        </div>
        <div class="modal-body">
          <div
            class="alert alert-info"
            role="alert"
          >
            {{ $t('modals.audiotuninginfo') }}
          </div>
          <div class="input-group input-group-sm mb-1">
            <span class="input-group-text">{{ $t('modals.testframe') }}</span>
            <button
              id="sendTestFrame"
              type="button"
              class="btn btn-danger"
              @click="sendModemTestFrame()"
            >
              {{ $t('modals.testframetransmit') }}
            </button>
          </div>
          <div class="input-group input-group-sm mb-1">
            <span class="input-group-text">{{ $t('modals.audiotuningrxlevel') }}</span>
            <span class="input-group-text">{{
              settings.remote.AUDIO.rx_audio_level
            }}</span>
            <span class="input-group-text w-75">
              <input
                id="audioLevelRX"
                v-model.number="settings.remote.AUDIO.rx_audio_level"
                type="range"
                class="form-range"
                min="-30"
                max="20"
                step="1"
                @change="onChange"
              ></span>
          </div>
          <div class="input-group input-group-sm mb-1">
            <span class="input-group-text">{{ $t('modals.audiotuningtxlevel') }}</span>
            <span class="input-group-text">{{
              settings.remote.AUDIO.tx_audio_level
            }}</span>
            <span class="input-group-text w-75">
              <input
                id="audioLevelTX"
                v-model.number="settings.remote.AUDIO.tx_audio_level"
                type="range"
                class="form-range"
                min="-30"
                max="20"
                step="1"
                @change="onChange"
              ></span>
          </div>


          <div class="input-group input-group-sm mb-1">
            <span class="input-group-text">{{ $t('modals.audiotuningtransmitsine') }}</span>
            <button
              id="sendTestFrame"
              type="button"
              class="btn btn-success"
              @click="sendSineTone(true)"
            >
              {{ $t('modals.audiotuningtransmitsine30s') }}
            </button>

            <button
              id="sendTestFrame"
              type="button"
              class="btn btn-danger"
              @click="sendSineTone(false)"
            >
              {{ $t('general.stop') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <!-- STATION INFO MODAL -->
  <div
    id="stationInfoModal"
    class="modal fade"
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
          />
        </div>
        <div class="modal-body">
          <div
            class="alert alert-primary"
            role="alert"
          >
            <strong> Please note:</strong> This is a preview to show you the
            direction, FreeDATA is going somewhen. For now you can save only
            your personal data, so we can optimize and improve the database. In
            future this data can be requested by a remote station.
          </div>
          <!-- Name -->
          <div class="input-group mb-1">
            <span class="input-group-text"><i class="bi bi-person-fill" /></span>
            <input
              v-model="station.stationInfo.info.name"
              type="text"
              class="form-control"
              placeholder="Name"
            >
          </div>
          <!-- City -->
          <div class="input-group mb-1">
            <span class="input-group-text"><i class="bi bi-geo-alt-fill" /></span>
            <input
              v-model="station.stationInfo.info.city"
              type="text"
              class="form-control"
              placeholder="City"
            >
          </div>
          <!-- Age -->
          <div class="input-group mb-3">
            <span class="input-group-text"><i class="bi bi-person-fill" /></span>
            <input
              v-model="station.stationInfo.info.age"
              type="text"
              class="form-control"
              placeholder="Age"
            >
          </div>
          <!-- Radio -->
          <div class="input-group mb-1">
            <span class="input-group-text"><i class="bi bi-broadcast-pin" /></span>
            <input
              v-model="station.stationInfo.info.radio"
              type="text"
              class="form-control"
              placeholder="Radio"
            >
          </div>
          <!-- Antenna -->
          <div class="input-group mb-3">
            <span class="input-group-text"><i class="bi bi-cone-striped" /></span>
            <input
              v-model="station.stationInfo.info.antenna"
              type="text"
              class="form-control"
              placeholder="Antenna"
            >
          </div>
          <!-- Website -->
          <div class="input-group mb-1">
            <span class="input-group-text"><i class="bi bi-globe" /></span>
            <input
              v-model="station.stationInfo.info.website"
              type="url"
              class="form-control"
              placeholder="Website"
            >
          </div>
          <!-- Email -->
          <div class="input-group mb-3">
            <span class="input-group-text"><i class="bi bi-envelope-fill" /></span>
            <input
              v-model="station.stationInfo.info.email"
              type="email"
              class="form-control"
              placeholder="Email"
            >
          </div>
          <!-- Social Media Inputs -->
          <div class="mb-3">
            <div
              v-for="(url, platform) in station.stationInfo.info.socialMedia"
              :key="platform"
            >
              <div class="input-group mb-1">
                <span class="input-group-text">
                  <i :class="`bi bi-${platform}`" />
                </span>
                <input
                  v-model="station.stationInfo.info.socialMedia[platform]"
                  type="url"
                  class="form-control"
                  :placeholder="`${platform.charAt(0).toUpperCase() + platform.slice(1)} URL`"
                >
              </div>
            </div>
          </div>
          <!-- Comments -->
          <div class="mb-3">
            <label
              class="input-group-text"
              for="comments"
            ><i class="bi bi-textarea-resize" /> Comments</label>
            <textarea
              v-model="station.stationInfo.info.comments"
              class="form-control"
              rows="3"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            {{ $t('modals.close') }}
          </button>
          <button
            type="button"
            class="btn btn-primary"
            @click="updateStationInfo"
          >
            {{ $t('modals.savechanges') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
