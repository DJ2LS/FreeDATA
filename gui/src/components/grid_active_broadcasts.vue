<script setup lang="ts">

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings} from "../store/settingsStore.js";

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { sendModemCQ, sendModemPing, setModemBeacon } from "../js/api.js";

function transmitPing() {
  sendModemPing((<HTMLInputElement>document.getElementById("dxCall")).value);
}

function startStopBeacon() {
  if (state.beacon_state === true) {
    setModemBeacon(false);
  }
  else {
    setModemBeacon(true);
  }
}
</script>
<template>
  <div class="card h-100">
    <div class="card-header">
      <div>
        <div>
            <i class="bi bi-broadcast" style="font-size: 1.2rem"></i>&nbsp;
            <strong>Broadcasts</strong>
        </div>
      </div>
    </div>
    <div class="card-body overflow-auto">
      <div>
        <div >
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
              @click="sendModemCQ()"
            >
              Call CQ
            </button>

            <button
              type="button"
              id="startBeacon"
              class="btn btn-sm ms-1"
              @click="startStopBeacon()"
              v-bind:class="{
                'btn-success': state.beacon_state === true,
                'btn-outline-secondary': state.beacon_state === false,
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
