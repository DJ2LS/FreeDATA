<template>
   <div
      class="modal modal-lg fade"
      id="modemCheck"
      data-bs-backdrop="static"
      data-bs-keyboard="false"
      tabindex="-1"
      aria-hidden="true"
      >
      <div class="modal-dialog">
         <div class="modal-content">
            <div class="modal-header">
               <h1 class="modal-title fs-5">Modem check</h1>
               <button
                  type="button"
                  class="ms-5 btn btn-secondary"
                  aria-label="Reload GUI"
                  @click="reloadGUI"
                  >
               GUI problems? Reload it!
               </button>
               <button
                  type="button"
                  class="btn-close"
                  data-bs-dismiss="modal"
                  aria-label="Close"
                  ></button>
            </div>
            <div class="modal-body">
               <div class="accordion" id="startupCheckAccordion">
                  <!-- Network Section -->
                  <div class="accordion-item">
                     <h2 class="accordion-header">
                        <button
                           class="accordion-button collapsed"
                           type="button"
                           data-bs-target="#networkStatusCollapse"
                           data-bs-toggle="collapse"
                           >
                        Network
                        <span
                           class="badge ms-2"
                           :class="state.modem_connection === 'connected' ? 'bg-success' : 'bg-danger'"
                           >
                        {{ getNetworkState() }}
                        </span>
                        </button>
                     </h2>
                     <div id="networkStatusCollapse" class="accordion-collapse collapse">
                        <div class="accordion-body">
                           <div class="input-group input-group-sm mb-1">
                              <span class="input-group-text w-25">API URL</span>
                              <input
                                 type="text"
                                 class="form-control"
                                 :value="apiUrl"
                                 disabled
                                 />
                           </div>
                        </div>
                     </div>
                  </div>
                  <!-- Modem Section -->
                  <div class="accordion-item">
                     <h2 class="accordion-header">
                        <button
                           class="accordion-button collapsed"
                           type="button"
                           data-bs-target="#modemStatusCollapse"
                           data-bs-toggle="collapse"
                           >
                        Modem
                        <span
                           class="badge ms-2"
                           :class="state.is_modem_running ? 'bg-success' : 'bg-danger'"
                           >
                        {{ getModemStateLocal() }}
                        </span>
                        </button>
                     </h2>
                     <div id="modemStatusCollapse" class="accordion-collapse collapse">
                        <div class="accordion-body">
                           <div class="input-group input-group-sm mb-1">
                              <label class="input-group-text w-50">Manual modem restart</label>
                              <label class="input-group-text">
                              <button
                                 type="button"
                                 id="startModem"
                                 class="btn btn-sm btn-outline-success"
                                 data-bs-toggle="tooltip"
                                 data-bs-trigger="hover"
                                 data-bs-html="false"
                                 title="Start the Modem. Please set your audio and radio settings first!"
                                 @click="startModem"
                                 :class="{ disabled: state.is_modem_running }"
                                 >
                              <i class="bi bi-play-fill"></i>
                              </button>
                              </label>
                              <label class="input-group-text">
                              <button
                                 type="button"
                                 id="stopModem"
                                 class="btn btn-sm btn-outline-danger"
                                 data-bs-toggle="tooltip"
                                 data-bs-trigger="hover"
                                 data-bs-html="false"
                                 title="Stop the Modem."
                                 @click="stopModem"
                                 :class="{ disabled: !state.is_modem_running }"
                                 >
                              <i class="bi bi-stop-fill"></i>
                              </button>
                              </label>
                           </div>
                           <!-- Audio Input Device -->
                           <div class="input-group input-group-sm mb-1">
                              <label class="input-group-text w-50">Audio Input device</label>
                              <select
                                 class="form-select form-select-sm"
                                 aria-label=".form-select-sm"
                                 @change="onChange"
                                 v-model="settings.remote.AUDIO.input_device"
                                 >
                                 <option
                                    v-for="device in audioStore.audioInputs"
                                    :value="device.id"
                                    :key="device.id"
                                    >
                                    {{ device.name }} [{{ device.api }}]
                                 </option>
                              </select>
                           </div>
                           <!-- Audio Output Device -->
                           <div class="input-group input-group-sm mb-1">
                              <label class="input-group-text w-50">Audio Output device</label>
                              <select
                                 class="form-select form-select-sm"
                                 aria-label=".form-select-sm"
                                 @change="onChange"
                                 v-model="settings.remote.AUDIO.output_device"
                                 >
                                 <option
                                    v-for="device in audioStore.audioOutputs"
                                    :value="device.id"
                                    :key="device.id"
                                    >
                                    {{ device.name }} [{{ device.api }}]
                                 </option>
                              </select>
                           </div>
                        </div>
                     </div>
                  </div>
                  <!-- Radio Control Section -->
                  <div class="accordion-item">
                     <h2 class="accordion-header">
                        <button
                           class="accordion-button collapsed"
                           type="button"
                           data-bs-target="#radioControlCollapse"
                           data-bs-toggle="collapse"
                           >
                        Radio control
                        <span
                           class="badge ms-2"
                           :class="getRigControlStatus() ? 'bg-success' : 'bg-danger'"
                           >
                        {{ getRigControlStatus() ? "Online" : "Offline" }}
                        </span>
                        </button>
                     </h2>
                     <div id="radioControlCollapse" class="accordion-collapse collapse">
                        <div class="accordion-body">
                           <div class="input-group input-group-sm mb-1">
                              <span class="input-group-text" style="width: 180px">Rig control method</span>
                              <select
                                 class="form-select form-select-sm"
                                 aria-label=".form-select-sm"
                                 id="rigcontrol_radiocontrol"
                                 @change="onChange"
                                 v-model="settings.remote.RADIO.control"
                                 >
                                 <option value="disabled">Disabled (no rig control; use with VOX)</option>
                                 <option value="serial_ptt">Serial PTT via DTR/RTS</option>
                                 <option value="rigctld">Rigctld (external Hamlib)</option>
                                 <option value="rigctld_bundle">Rigctld (internal Hamlib)</option>
                                 <option value="tci">TCI</option>
                              </select>
                           </div>
                           <!-- Shown when rigctld_bundle is selected -->
                           <div :class="{ 'd-none': settings.remote.RADIO.control !== 'rigctld_bundle' }">
                              <div class="input-group input-group-sm mb-1">
                                 <span class="input-group-text" style="width: 180px"
                                    >Radio port</span
                                    >
                                 <select
                                    @change="onChange"
                                    v-model="settings.remote.RADIO.serial_port"
                                    class="form-select form-select-sm"
                                    >
                                    <option
                                       v-for="device in serialStore.serialDevices"
                                       :value="device.port"
                                       :key="device.port"
                                       >
                                       {{ device.description }}
                                    </option>
                                 </select>
                              </div>
                              <!-- Test Hamlib Button -->
                              <div class="input-group input-group-sm mb-1">
                                 <button
                                    type="button"
                                    class="btn btn-sm btn-outline-secondary"
                                    @click="testHamlib"
                                    >
                                 Test Hamlib
                                 </button>
                              </div>
                           </div>
                        </div>
                     </div>
                  </div>
               </div>
            </div>
         </div>
      </div>
   </div>
</template>

<script setup>
import { Modal } from 'bootstrap/dist/js/bootstrap.esm.min.js';
import { onMounted } from "vue";

// Pinia setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

// Store imports
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { sendModemCQ } from "../js/api.js";
import { useStateStore } from "../store/stateStore.js";
import { useAudioStore } from "../store/audioStore";
import { useSerialStore } from "../store/serialStore.js";


// API imports
import {
  getVersion,
  startModem,
  stopModem,
} from "../js/api";

// Reactive state
const state = useStateStore(pinia);
const audioStore = useAudioStore(pinia);
const serialStore = useSerialStore(pinia);

// Get the full API URL
const apiUrl = `${window.location.protocol}//${window.location.hostname}:${window.location.port}`;

// Initialize modal on mount
onMounted(() => {
  getVersion().then((res) => {
    state.modem_version = res;
  });
  new Modal("#modemCheck", {}).show();
});

// Helper functions
function getModemStateLocal() {
  return state.is_modem_running ? "Active" : "Inactive";
}

function getNetworkState() {
  return state.modem_connection === "connected" ? "Connected" : "Disconnected";
}

function getRigControlStatus() {
  switch (settings.remote.RADIO.control) {
    case "disabled":
      return true;
    case "serial_ptt":
    case "rigctld":
    case "rigctld_bundle":
    case "tci":
      return state.radio_status;
    default:
      console.error("Unknown radio control mode " + settings.remote.RADIO.control);
      return "Unknown control type" + settings.remote.RADIO.control;
  }
}

function testHamlib() {
  sendModemCQ();
}

function reloadGUI() {
  location.reload();
}
</script>
