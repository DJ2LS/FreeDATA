<script setup lang="ts">
import { Modal } from "bootstrap";
import { onMounted } from "vue";

import main_rig_control from "./main_rig_control.vue";
import main_audio from "./main_audio.vue";
import infoScreen_updater from "./infoScreen_updater.vue";

import { saveModemConfig } from "../js/api";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import { useAudioStore } from "../store/audioStore.js";
const audio = useAudioStore(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { startModem, stopModem } from "../js/api";
import { getModemConfig } from "../js/api";

// start modemCheck modal once on startup
onMounted(() => {
  getModemConfig();
  new Modal("#modemCheck", {}).show();
  if (state.is_modem_running == false) {
  }
});

function getModemState() {
  // Returns active/inactive if modem is running for modem status label
  console.log(state.is_modem_running);
  if (state.is_modem_running == true) return "Active";
  else return "Inactive";
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
                  <span class="badge ms-2 bg-warning">Update needed</span>
                </button>
              </h2>
              <div
                id="versionCheckCollapse"
                class="accordion-collapse collapse"
              >
                <div class="accordion-body">
                  <infoScreen_updater />
                </div>
              </div>
            </div>
            <!-- Network Section -->
            <div class="accordion-item">
              <h2 class="accordion-header">
                <button
                  class="accordion-button collapsed"
                  type="button"
                  data-bs-target="#networkStatusCollapse"
                  data-bs-toggle="collapse"
                >
                  Network <span class="badge ms-2 bg-success">Connected</span>
                </button>
              </h2>
              <div
                id="networkStatusCollapse"
                class="accordion-collapse collapse"
              >
                <div class="accordion-body">
                  Placeholder content for this accordion, which is intended to
                  demonstrate the <code>.accordion-flush</code> class. This is
                  the first item's accordion body.
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
                    >{{ getModemState() }}</span
                  >
                </button>
              </h2>
              <div id="modemStatusCollapse" class="accordion-collapse collapse">
                <div class="accordion-body">
                  <div class="input-group input-group-sm mb-1">
                    <label class="input-group-text w-25">Modem control</label>
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
                    <label class="input-group-text w-25">Input device</label>
                    <select
                      class="form-select form-select-sm"
                      id="rx_audio"
                      aria-label=".form-select-sm"
                      @change="saveModemConfig"
                      v-model="settings.input_device"
                      v-html="audio.getInputDevices()"
                    ></select>
                  </div>

                  <!-- Audio Output Device -->
                  <div class="input-group input-group-sm mb-1">
                    <label class="input-group-text w-25">Output device</label>
                    <select
                      class="form-select form-select-sm"
                      id="tx_audio"
                      aria-label=".form-select-sm"
                      @change="saveModemConfig"
                      v-model="settings.output_device"
                      v-html="audio.getOutputDevices()"
                    ></select>
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
                  <span class="badge ms-2 bg-danger">Disconnected</span>
                </button>
              </h2>
              <div
                id="radioControlCollapse"
                class="accordion-collapse collapse"
              >
                <div class="accordion-body">
                  <main_rig_control />
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
