<script setup>
   import { onMounted, computed } from "vue";
   import { setActivePinia } from "pinia";
   import pinia from "../store/index";
   import { useChatStore } from "../store/chatStore.js";
   import { useStationStore } from "../store/stationStore.js";
   import { getStationInfoByCallsign, setStationInfoByCallsign } from "../js/stationHandler.js";
   import { settingsStore } from "../store/settingsStore.js";
   import { settingsStore as settings, onChange } from "../store/settingsStore.js";
   import { sendModemTestFrame, sendSineTone } from "../js/api";
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
     BarElement,
   } from "chart.js";
   import { Line, Bar } from "vue-chartjs";
   
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
      class="modal fade"
      ref=modalElement
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
      ref=modalElement
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
      ref=modalElement
      id="deleteChatModal"
      tabindex="-1"
      aria-labelledby="exampleModalLabel"
      aria-hidden="true"
      >
      <div class="modal-dialog">
         <div class="modal-content">
            <div class="modal-header">
               <h1 class="modal-title fs-5" id="deleteChatModalLabel">
                   {{ chat.selectedCallsign }} Options
               </h1>
               <button
                  type="button"
                  class="btn-close"
                  data-bs-dismiss="modal"
                  aria-label="Close"
                  ></button>
            </div>
            <div class="modal-body">



            <div class="card">
  <div class="card-header">
    <strong>Beacon histogram</strong>
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
    <strong>Further options</strong>
  </div>
  <div class="card-body">
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
   <!-- Message Info Modal -->
   <div
      class="modal fade"
      ref=modalElement
      id="messageInfoModal"
      tabindex="-1"
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

              <div class="card mt-2">
                  <div class="card-header">Statistics</div>
<div class="card-body">
  <div class="container">
    <div class="row">
      <!-- Bytes per Minute -->
      <div class="auto mb-2">
        <div class="input-group">
          <span class="input-group-text">Speed</span>
          <span class="input-group-text">{{ chat.messageInfoById?.statistics?.bytes_per_minute ?? 'NaN' }} bpm / {{ chat.messageInfoById?.statistics?.bits_per_second ?? 'NaN' }} bps</span>
        </div>
      </div>
    </div>

    <div class="row">

      <!-- Duration [s] -->
      <div class="col-auto mb-2">
        <div class="input-group">
          <span class="input-group-text">Duration [s]</span>
          <span class="input-group-text">{{ Math.round(chat.messageInfoById?.statistics?.duration) ?? 'NaN' }}</span>
        </div>
      </div>
      <!-- Size -->
      <div class="col-auto mb-2">
        <div class="input-group">
          <span class="input-group-text">Size</span>
          <span class="input-group-text">{{ chat.messageInfoById?.statistics?.total_bytes ?? 'NaN'  }} Bytes</span>
        </div>
      </div>
    </div>
  </div>
</div>




               </div>


                              <div class="card mt-2">
                  <div class="card-header">Chart</div>
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
      ref=modalElement
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
                  Transmit ( 5s )
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


              <div class="input-group input-group-sm mb-1">
                  <span class="input-group-text">Transmit sine</span>
                  <button
                     type="button"
                     id="sendTestFrame"
                     @click="sendSineTone(true)"
                     class="btn btn-success"
                     >
                  Transmit ( max 30s )
                  </button>

                                <button
                     type="button"
                     id="sendTestFrame"
                     @click="sendSineTone(false)"
                     class="btn btn-danger"
                     >
                  Stop
                  </button>

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