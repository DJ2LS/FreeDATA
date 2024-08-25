<script setup>
import { ref } from "vue";
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
import { useStateStore } from "../../store/stateStore.js";
import { sendModemCQ, sendModemPing, setModemBeacon } from "../../js/api.js";

// Set the active Pinia store
setActivePinia(pinia);
const state = useStateStore(pinia);

// Define the reactive reference for DX Call
const dxcallPing = ref("");

// Reactive reference to manage CQ button state
const isCQButtonDisabled = ref(false);
const isCQButtonLoading = ref(false);

// Function to transmit a ping
function transmitPing() {
  sendModemPing(dxcallPing.value.toUpperCase());
}

// Function to start or stop the beacon
function startStopBeacon() {
  if (state.beacon_state) {
    setModemBeacon(false, state.away_from_key);
  } else {
    setModemBeacon(true, state.away_from_key);
  }
}

// Function to set away from key state
function setAwayFromKey() {
  setModemBeacon(state.beacon_state, state.away_from_key);
}

// Function to send CQ and handle button disable and spinner
async function handleSendCQ() {
  isCQButtonDisabled.value = true;
  isCQButtonLoading.value = true;

  // Send CQ message
  await sendModemCQ();

  // Wait for 3 seconds
  setTimeout(() => {
    isCQButtonDisabled.value = false;
    isCQButtonLoading.value = false;
  }, 6000);
}

// Listen for the stationSelected event and update dxcallPing
window.addEventListener(
  "stationSelected",
  function (eventdata) {
    const evt = eventdata;
    dxcallPing.value = evt.detail;
  },
  false
);
</script>

<template>
  <div class="card h-100">
    <div class="card-header p-0">
      <i class="bi bi-broadcast" style="font-size: 1.2rem"></i>&nbsp;
      <strong>Broadcasts</strong>
    </div>
    <div class="card-body overflow-auto p-0">
      <div class="container text-center">
        <div class="row mb-2 mt-2">
          <div class="col">
            <div class="input-group w-100">
              <div class="form-floating">
                <input
                  type="text"
                  class="form-control"
                  style="text-transform: uppercase"
                  id="floatingInput"
                  placeholder="dx-callsign"
                  v-model="dxcallPing"
                  maxlength="11"
                  pattern="[A-Z]*"
                />
                <label for="floatingInput">DX-Callsign</label>
              </div>
              <button
                class="btn btn-sm btn-outline-secondary"
                id="sendPing"
                type="button"
                data-bs-placement="bottom"
                data-bs-toggle="tooltip"
                data-bs-trigger="hover"
                data-bs-html="false"
                title="Send a ping request to a remote station"
                @click="transmitPing"
              >
                <strong>PING Station</strong>
              </button>
            </div>
          </div>
        </div>

         <div class="row">
          <div class="col">
            <button
              class="btn btn-sm btn-outline-secondary w-100"
              id="sendCQ"
              type="button"
              title="Send a CQ to the world"
              @click="handleSendCQ"
              :disabled="isCQButtonDisabled"
            >
              <h3>
                <span v-if="!isCQButtonLoading">CQ CQ CQ</span>
                <span v-if="isCQButtonLoading" class="sr-only">Cooldown...</span>
              </h3>
            </button>
          </div>
        </div>

        <div class="row">
          <div class="col">
            <div class="form-check form-switch">
              <input
                class="form-check-input"
                type="checkbox"
                role="switch"
                id="flexSwitchBeacon"
                v-model="state.beacon_state"
                @click="startStopBeacon"
              />
              <label class="form-check-label" for="flexSwitchBeacon">Enable Beacon</label>
            </div>
          </div>

          <div class="col">
            <div class="form-check form-switch">
              <input
                class="form-check-input"
                type="checkbox"
                role="switch"
                id="flexSwitchAFK"
                v-model="state.away_from_key"
                @change="setAwayFromKey"
              />
              <label class="form-check-label" for="flexSwitchAFK">Away From Key</label>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
