<script setup lang="ts">
import { Modal } from "bootstrap";
import { onMounted } from "vue";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { sendModemCQ } from "../js/api.js";

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { useAudioStore } from "../store/audioStore";
const audioStore = useAudioStore();
import { useSerialStore } from "../store/serialStore";
const serialStore = useSerialStore();

import {
  getVersion,
  setConfig,
  startModem,
  stopModem,
  getModemState,
} from "../js/api";

const version = import.meta.env.PACKAGE_VERSION;

// start modemCheck modal once on startup
onMounted(() => {
  getVersion().then((res) => {
    state.modem_version = res;
  });
  new Modal("#modemCheck", {}).show();
});

function getModemStateLocal() {
  // Returns active/inactive if modem is running for modem status label
  if (state.is_modem_running == true) return "Active";
  else return "Inactive";
}
function getNetworkState() {
  // Returns active/inactive if modem is running for modem status label
  if (state.modem_connection === "connected") return "Connected";
  else return "Disconnected";
}

function getRigControlStuff() {
  switch (settings.remote.RADIO.control) {
    case "disabled":
      return true;
    case "serial_ptt":
    case "rigctld":
    case "rigctld_bundle":
    case "tci":
      return state.radio_status;
    default:
      console.error(
        "Unknown radio control mode " + settings.remote.RADIO.control,
      );
      return "Unknown control type" + settings.remote.RADIO.control;
  }
}

function testHamlib() {
  sendModemCQ();
}
</script>

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
                    class="badge ms-2 bg-success"
                    :class="
                      state.modem_connection === 'connected'
                        ? 'bg-success'
                        : 'bg-danger'
                    "
                    >{{ getNetworkState() }}</span
                  >
                </button>
              </h2>
              <div
                id="networkStatusCollapse"
                class="accordion-collapse collapse"
              >
                <div class="accordion-body">
                  <div class="input-group input-group-sm mb-1">
                    <span class="input-group-text w-25">Modem port</span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="modem port (def 5000)"
                      id="modem_port"
                      maxlength="5"
                      max="65534"
                      min="1025"
                      v-model="settings.local.port"
                      @change="onChange"
                    />
                  </div>

                  <div class="input-group input-group-sm mb-1">
                    <span class="input-group-text w-25">Modem host</span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="modem host (default 127.0.0.1)"
                      id="modem_port"
                      v-model="settings.local.host"
                      @change="onChange"
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
                    :class="
                      state.is_modem_running === true
                        ? 'bg-success'
                        : 'bg-danger'
                    "
                    >{{ getModemStateLocal() }}</span
                  >
                </button>
              </h2>
              <div id="modemStatusCollapse" class="accordion-collapse collapse">
                <div class="accordion-body">
                  <div class="input-group input-group-sm mb-1">
                    <label class="input-group-text w-50"
                      >Manual modem restart</label
                    >
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
                        v-bind:class="{
                          disabled: state.is_modem_running === true,
                        }"
                      >
                        <i class="bi bi-play-fill"></i>
                      </button> </label
                    ><label class="input-group-text">
                      <button
                        type="button"
                        id="stopModem"
                        class="btn btn-sm btn-outline-danger"
                        data-bs-toggle="tooltip"
                        data-bs-trigger="hover"
                        data-bs-html="false"
                        title="Stop the Modem."
                        @click="stopModem"
                        v-bind:class="{
                          disabled: state.is_modem_running === false,
                        }"
                      >
                        <i class="bi bi-stop-fill"></i>
                      </button>
                    </label>
                  </div>

                  <!-- Audio Input Device -->
                  <div class="input-group input-group-sm mb-1">
                    <label class="input-group-text w-50"
                      >Audio Input device</label
                    >
                    <select
                      class="form-select form-select-sm"
                      aria-label=".form-select-sm"
                      @change="onChange"
                      v-model="settings.remote.AUDIO.input_device"
                    >
                      <option
                        v-for="device in audioStore.audioInputs"
                        :value="device.id"
                      >
                        {{ device.name }} [{{ device.api }}]
                      </option>
                    </select>
                  </div>

                  <!-- Audio Output Device -->
                  <div class="input-group input-group-sm mb-1">
                    <label class="input-group-text w-50"
                      >Audio Output device</label
                    >
                    <select
                      class="form-select form-select-sm"
                      aria-label=".form-select-sm"
                      @change="onChange"
                      v-model="settings.remote.AUDIO.output_device"
                    >
                      <option
                        v-for="device in audioStore.audioOutputs"
                        :value="device.id"
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
                    :class="
                      getRigControlStuff() === true ? 'bg-success' : 'bg-danger'
                    "
                    >{{
                      getRigControlStuff() === true ? "Online" : "Offline"
                    }}</span
                  >
                </button>
              </h2>
              <div
                id="radioControlCollapse"
                class="accordion-collapse collapse"
              >
                <div class="accordion-body">
                  <div class="input-group input-group-sm mb-1">
                    <span class="input-group-text" style="width: 180px"
                      >Rig control method</span
                    >

                    <select
                      class="form-select form-select-sm"
                      aria-label=".form-select-sm"
                      id="rigcontrol_radiocontrol"
                      @change="onChange"
                      v-model="settings.remote.RADIO.control"
                    >
                      <option selected value="disabled">
                        Disabled (no rig control; use with VOX)
                      </option>
                      <option selected value="serial_ptt">Serial PTT via DTR/RTS</option>
                      <option selected value="rigctld">
                        Rigctld (external Hamlib)
                      </option>
                      <option selected value="rigctld_bundle">
                        Rigctld (internal Hamlib)
                      </option>
                      <option selected value="tci">TCI</option>
                    </select>
                  </div>
                  <div
                    :class="
                      settings.remote.RADIO.control == 'rigctld_bundle'
                        ? ''
                        : 'd-none'
                    "
                  >
                    <!-- Shown when rigctld is selected-->

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

                    <div class="input-group input-group-sm mb-1">
                      <label class="input-group-text w-25">Rigctld Test</label>

                      <label class="input-group-text">
                        <button
                          type="button"
                          id="testHamlib"
                          class="btn btn-sm btn-outline-secondary"
                          data-bs-placement="bottom"
                          data-bs-toggle="tooltip"
                          data-bs-trigger="hover"
                          data-bs-html="true"
                          @click="testHamlib"
                          title="Test your hamlib settings and toggle PTT once. Button will become <strong class='text-success'>green</strong> on success and <strong class='text-danger'>red</strong> if fails."
                        >
                          Send a CQ
                        </button>
                      </label>
                    </div>
                  </div>
                  <div
                    :class="
                      settings.remote.RADIO.control == 'tci' ? '' : 'd-none'
                    "
                  >
                    <!-- Shown when tci is selected-->

                    <div class="input-group input-group-sm mb-1">
                      <span class="input-group-text w-25">TCI IP address</span>
                      <input
                        type="text"
                        class="form-control"
                        placeholder="TCI IP"
                        id="rigcontrol_tci_ip"
                        aria-label="Device IP"
                        v-model="settings.remote.TCI.tci_ip"
                        @change="onChange"
                      />
                    </div>

                    <div class="input-group input-group-sm mb-1">
                      <span class="input-group-text w-25">TCI port</span>
                      <input
                        type="text"
                        class="form-control"
                        placeholder="TCI port"
                        id="rigcontrol_tci_port"
                        aria-label="Device Port"
                        v-model="settings.remote.TCI.tci_port"
                        @change="onChange"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- Version Section -->
            <div class="accordion-item">
              <h2 class="accordion-header">
                <button
                  class="accordion-button collapsed"
                  type="button"
                  data-bs-target="#versionCheckCollapse"
                  data-bs-toggle="collapse"
                >
                  Version
                </button>
              </h2>
              <div
                id="versionCheckCollapse"
                class="accordion-collapse collapse"
              >
                <div class="accordion-body">
                  <button
                    class="btn btn-secondary btn-sm ms-1 me-1"
                    type="button"
                    disabled
                  >
                    GUI version | {{ version }}
                  </button>

                  <button
                    class="btn btn-secondary btn-sm ms-1 me-1"
                    type="button"
                    disabled
                  >
                    Modem version | {{ state.modem_version }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
            Continue
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
