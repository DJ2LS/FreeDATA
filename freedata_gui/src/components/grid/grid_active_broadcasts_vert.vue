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

// Reactive references to manage button states
const isCQButtonDisabled = ref(false);
const isPingButtonDisabled = ref(false);

// Function to transmit a ping
async function transmitPing() {
  isPingButtonDisabled.value = true;

  // Send Ping message
  await sendModemPing(dxcallPing.value.toUpperCase());

  // Wait for 6 seconds (cooldown period)
  setTimeout(() => {
    isPingButtonDisabled.value = false;
  }, 6000);
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

// Function to send CQ and handle button disable and cooldown
async function handleSendCQ() {
  isCQButtonDisabled.value = true;

  // Send CQ message
  await sendModemCQ();

  // Wait for 6 seconds (cooldown period)
  setTimeout(() => {
    isCQButtonDisabled.value = false;
  }, 10000);
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
    <div class="card-header">
      <i
        class="bi bi-broadcast"
        style="font-size: 1.2rem"
      />&nbsp;
      <strong>{{ $t('grid.components.broadcasts') }}</strong>
    </div>
    <div class="card-body overflow-auto p-0">
      <div class="container text-center">
        <div class="row mb-2 mt-2">
          <div class="col">
            <div class="input-group w-100">
              <div class="form-floating">
                <input
                  id="floatingInput"
                  v-model="dxcallPing"
                  type="text"
                  class="form-control"
                  style="text-transform: uppercase"
                  placeholder="dx-callsign"
                  maxlength="11"
                  pattern="[A-Z]*"
                >
                <label for="floatingInput">{{ $t('grid.components.dxcall') }}</label>
              </div>
              <button
                id="sendPing"
                class="btn btn-sm btn-outline-secondary"
                type="button"
                data-bs-placement="bottom"
                data-bs-toggle="tooltip"
                data-bs-trigger="hover"
                data-bs-html="false"
                :title="$t('grid.components.ping_help') "
                :disabled="isPingButtonDisabled"
                @click="transmitPing"
              >
                <strong v-if="!isPingButtonDisabled">{{ $t('grid.components.pingstation') }}</strong>
                <strong v-else>{{ $t('grid.components.sendingping') }}</strong>
              </button>
            </div>
          </div>
        </div>

        <div class="row">
          <div class="col">
            <button
              id="sendCQ"
              class="btn btn-sm btn-outline-secondary w-100"
              type="button"
              :title=" $t('grid.components.cqcqcq_help')"
              :disabled="isCQButtonDisabled"
              @click="handleSendCQ"
            >
              <h3>
                <span v-if="!isCQButtonDisabled">{{ $t('grid.components.cqcqcq') }}</span>
                <span v-else>{{ $t('grid.components.sendingcq') }}</span>
              </h3>
            </button>
          </div>
        </div>

        <div class="row">
          <div class="col">
            <div class="form-check form-switch">
              <input
                id="flexSwitchBeacon"
                v-model="state.beacon_state"
                class="form-check-input"
                type="checkbox"
                role="switch"
                @click="startStopBeacon"
              >
              <label
                class="form-check-label"
                for="flexSwitchBeacon"
              >{{ $t('grid.components.enablebeacon') }}</label>
            </div>
          </div>

          <div class="col">
            <div class="form-check form-switch">
              <input
                id="flexSwitchAFK"
                v-model="state.away_from_key"
                class="form-check-input"
                type="checkbox"
                role="switch"
                @change="setAwayFromKey"
              >
              <label
                class="form-check-label"
                for="flexSwitchAFK"
              >{{ $t('grid.components.awayfromkey') }}</label>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
