<script setup lang="ts">
import { saveSettingsToFile } from "../js/settingsHandler";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { sendPing, startBeacon, stopBeacon } from "../js/sock.js";
import { postToServer } from "../js/rest.js";


function transmitCQ() {
  postToServer("localhost", 5000, "modem/cqcqcq", null);
}

function transmitPing() {
  sendPing((<HTMLInputElement>document.getElementById("dxCall")).value);
}

function startStopBeacon() {
  switch (state.beacon_state) {
    case "False":
      startBeacon(settings.beacon_interval);

      break;
    case "True":
      stopBeacon();

      break;
    default:
  }
}
</script>
<template>
  <div class="card mb-1">
    <div class="card-header p-1">
      <div class="container">
        <div class="row">
          <div class="col-1">
            <i class="bi bi-broadcast" style="font-size: 1.2rem"></i>
          </div>
          <div class="col-10">
            <strong class="fs-5">Broadcasts</strong>
          </div>
          <div class="col-1 text-end">
            <button
              type="button"
              id="openHelpModalBroadcasts"
              data-bs-toggle="modal"
              data-bs-target="#broadcastsHelpModal"
              class="btn m-0 p-0 border-0"
            >
              <i class="bi bi-question-circle" style="font-size: 1rem"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="card-body p-2">
      <div class="row">
        <div class="col-md-auto">
          <div class="input-group input-group-sm mb-0">
            <input
              type="text"
              class="form-control"
              style="max-width: 6rem; text-transform: uppercase"
              placeholder="DXcall"
              pattern="[A-Z]*"
              id="dxCall"
              maxlength="11"
              aria-label="Input group"
              aria-describedby="btnGroupAddon"
            />
            <button
              class="btn btn-sm btn-outline-secondary ms-1"
              id="sendPing"
              type="button"
              data-bs-placement="bottom"
              data-bs-toggle="tooltip"
              data-bs-trigger="hover"
              data-bs-html="false"
              title="Send a ping request to a remote station"
              @click="transmitPing()"
            >
              Ping
            </button>

            <button
              class="btn btn-sm btn-outline-secondary ms-1"
              id="sendCQ"
              type="button"
              title="Send a CQ to the world"
              @click="transmitCQ()"
            >
              Call CQ
            </button>

            <button
              type="button"
              id="startBeacon"
              class="btn btn-sm ms-1"
              @click="startStopBeacon()"
              v-bind:class="{
                'btn-success': state.beacon_state === 'True',
                'btn-outline-secondary': state.beacon_state === 'False',
              }"
              title="Toggle beacon mode. The interval can be set in settings. While sending a beacon, you can receive ping requests and open a datachannel. If a datachannel is opened, the beacon pauses."
            >
              <i class="bi bi-soundwave"></i> Toggle beacon
            </button>
          </div>
        </div>
      </div>
      <!-- end of row-->
    </div>
  </div>
</template>
