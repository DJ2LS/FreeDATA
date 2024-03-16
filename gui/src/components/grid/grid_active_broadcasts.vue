<script setup lang="ts">
import { ref } from "vue";
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);

import { useStateStore } from "../../store/stateStore.js";
const state = useStateStore(pinia);

import { sendModemCQ, sendModemPing, setModemBeacon } from "../../js/api.js";

function transmitPing() {
  sendModemPing(dxcallPing.value.toUpperCase());
}

function startStopBeacon() {
  if (state.beacon_state === true) {
    setModemBeacon(false);
  } else {
    setModemBeacon(true);
  }
}
var dxcallPing = ref("");
window.addEventListener(
      "stationSelected",
      function (eventdata) {
        let evt = <CustomEvent>eventdata;
        dxcallPing.value = evt.detail;
      },
      false,
    );
</script>
<template>
  <div class="card h-100">
    <div class="card-header p-0">
      <i class="bi bi-broadcast" style="font-size: 1.2rem"></i>&nbsp;
      <strong>Broadcasts</strong>
    </div>
    <div class="card-body overflow-auto p-0">
      <div class="input-group input-group-sm mb-0">
        <input
          type="text"
          class="form-control"
          style="max-width: 6rem; min-width: 3rem; text-transform: uppercase"
          placeholder="DXcall"
          pattern="[A-Z]*"
          maxlength="11"
          aria-label="Input group"
          aria-describedby="btnGroupAddon"
          v-model="dxcallPing"
        />
        <button
          class="btn btn-sm btn-outline-secondary"
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
          Toggle beacon
        </button>
      </div>
      <!-- end of row-->
    </div>
  </div>
</template>
