<script setup lang="ts">
import { saveSettingsToFile } from "../js/settingsHandler";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

function selectRadioControl(obj) {
  switch (event.target.id) {
    case "list-rig-control-none-list":
      settings.radiocontrol = "disabled";
      break;
    case "list-rig-control-rigctld-list":
      settings.radiocontrol = "rigctld";
      break;
    case "list-rig-control-tci-list":
      settings.radiocontrol = "tci";
      break;
    default:
      console.log("default=!==");
      settings.radiocontrol = "disabled";
  }
  saveSettingsToFile();
}
</script>

<template>
  <div class="card mb-0">
    <div class="card-header p-1">
      <div class="container">
        <div class="row">
          <div class="col-1">
            <i class="bi bi-projector" style="font-size: 1.2rem"></i>
          </div>
          <div class="col-4">
            <strong class="fs-5">Rig control</strong>
          </div>

          <div class="col-6">
            <div
              class="list-group list-group-horizontal"
              id="rig-control-list-tab"
              role="rig-control-tablist"
            >
              <a
                class="py-1 list-group-item list-group-item-action"
                id="list-rig-control-none-list"
                data-bs-toggle="list"
                href="#list-rig-control-none"
                role="tab"
                aria-controls="list-rig-control-none"
                v-bind:class="{ active: settings.radiocontrol === 'disabled' }"
                @click="selectRadioControl()"
                >None/Vox</a
              >
              <a
                class="py-1 list-group-item list-group-item-action"
                id="list-rig-control-rigctld-list"
                data-bs-toggle="list"
                href="#list-rig-control-rigctld"
                role="tab"
                aria-controls="list-rig-control-rigctld"
                v-bind:class="{ active: settings.radiocontrol === 'rigctld' }"
                @click="selectRadioControl()"
                >Rigctld</a
              >
              <a
                class="py-1 list-group-item list-group-item-action"
                id="list-rig-control-tci-list"
                data-bs-toggle="list"
                href="#list-rig-control-tci"
                role="tab"
                aria-controls="list-rig-control-tci"
                v-bind:class="{ active: settings.radiocontrol === 'tci' }"
                @click="selectRadioControl()"
                >TCI</a
              >
            </div>
          </div>

          <div class="col-1 text-end">
            <button
              type="button"
              id="openHelpModalRigControl"
              data-bs-toggle="modal"
              data-bs-target="#rigcontrolHelpModal"
              class="btn m-0 p-0 border-0"
            >
              <i class="bi bi-question-circle" style="font-size: 1rem"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="card-body p-2" style="height: 100px">
      <div class="tab-content" id="rig-control-nav-tabContent">
        <div
          class="tab-pane fade"
          v-bind:class="{ 'show active': settings.radiocontrol === 'disabled' }"
          id="list-rig-control-none"
          role="tabpanel"
          aria-labelledby="list-rig-control-none-list"
        >
          <p class="small">
            TNC will not utilize rig control and features will be limited. While
            functional; it is recommended to configure hamlib.
          </p>
        </div>
        <div
          class="tab-pane fade"
          id="list-rig-control-rigctld"
          v-bind:class="{ 'show active': settings.radiocontrol === 'rigctld' }"
          role="tabpanel"
          aria-labelledby="list-rig-control-rigctld-list"
        >
          <div class="input-group input-group-sm mb-1">
            <div class="input-group input-group-sm mb-1">
              <span class="input-group-text">Rigctld</span>
              <span class="input-group-text">Address</span>
              <input
                type="text"
                class="form-control"
                placeholder="rigctld IP"
                id="hamlib_rigctld_ip"
                aria-label="Device IP"
                v-model="settings.hamlib_rigctld_ip"
              />
              <span class="input-group-text">Port</span>
              <input
                type="text"
                class="form-control"
                placeholder="rigctld port"
                id="hamlib_rigctld_port"
                aria-label="Device Port"
                v-model="settings.hamlib_rigctld_port"
              />
            </div>

            <div class="input-group input-group-sm mb-1">
              <span class="input-group-text">Rigctld</span>
              <button
                class="btn btn-outline-success"
                type="button"
                id="hamlib_rigctld_start"
              >
                Start
              </button>
              <button
                class="btn btn-outline-danger"
                type="button"
                id="hamlib_rigctld_stop"
              >
                Stop
              </button>
              <input
                type="text"
                class="form-control"
                placeholder="Status"
                id="hamlib_rigctld_status"
                aria-label="State"
                aria-describedby="basic-addon1"
              />

              <button
                type="button"
                id="testHamlib"
                class="btn btn-sm btn-outline-secondary ms-1"
                data-bs-placement="bottom"
                data-bs-toggle="tooltip"
                data-bs-trigger="hover"
                data-bs-html="true"
                @click="testHamlib"
                title="Test your hamlib settings and toggle PTT once. Button will become <strong class='text-success'>green</strong> on success and <strong class='text-danger'>red</strong> if fails."
              >
                PTT Test
              </button>
            </div>
          </div>
        </div>
        <div
          class="tab-pane fade"
          id="list-rig-control-tci"
          v-bind:class="{ 'show active': settings.radiocontrol === 'tci' }"
          role="tabpanel"
          aria-labelledby="list-rig-control-tci-list"
        >
          <div class="input-group input-group-sm mb-1">
            <div class="input-group input-group-sm mb-1">
              <span class="input-group-text">TCI</span>
              <span class="input-group-text">Address</span>
              <input
                type="text"
                class="form-control"
                placeholder="tci IP"
                id="tci_ip"
                aria-label="Device IP"
                v-model="settings.tci_ip"
              />
            </div>

            <div class="input-group input-group-sm mb-1">
              <span class="input-group-text">Port</span>
              <input
                type="text"
                class="form-control"
                placeholder="tci port"
                id="tci_port"
                aria-label="Device Port"
                v-model="settings.tci_port"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- RADIO CONTROL DISABLED -->
      <div id="radio-control-disabled"></div>

      <!-- RADIO CONTROL RIGCTLD -->
      <div id="radio-control-rigctld"></div>
      <!-- RADIO CONTROL TCI-->
      <div id="radio-control-tci"></div>
      <!-- RADIO CONTROL HELP -->
      <div id="radio-control-help">
        <!--
                  <strong>VOX:</strong> Use rig control mode 'none'
                  <br />
                  <strong>HAMLIB locally:</strong> configure in settings, then
                  start/stop service.
                  <br />
                  <strong>HAMLIB remotely:</strong> Enter IP/Port, connection
                  happens automatically.
                -->
      </div>
    </div>
    <!--<div class="card-footer text-muted small" id="hamlib_info_field">
                Define TNC rig control mode (none/hamlib)
              </div>
              -->
  </div>
</template>
