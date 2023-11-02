<script setup lang="ts">
import { ref } from 'vue'

import { saveSettingsToFile } from "../js/settingsHandler";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { sendCQ, sendPing, startBeacon, stopBeacon } from "../js/sock.js";

// dxcallsign component global
var dxcallsign = ref()

function transmitCQ() {
  sendCQ();
}

function transmitPing() {
  sendPing((<HTMLInputElement>document.getElementById("dxCall")).value);
}

</script>


<template>

<div class="card border-dark mb-3 h-100">
  <div class="card-body">


<div class="row h-25">
        <div class="col">
<div class="input-group input-group-sm mb-1 w-100 h-100">
            <button
              class="btn btn-sm btn-outline-secondary w-100 h-100"
              type="button"
              data-bs-placement="bottom"
              data-bs-toggle="tooltip"
              data-bs-trigger="hover"
              data-bs-html="false"
              title="Send a CQ to the world"
              @click="transmitCQ()"
            >
              <strong>Call CQ</strong>
            </button>
</div>
</div>
</div>

<div class="row mt-1 h-25">
        <div class="col">
          <div class="input-group input-group-sm h-100">

            <input
              type="text"
              class="form-control h-100"
              style="text-transform: uppercase"
              placeholder="DXcall"
              pattern="[A-Z]*"
              maxlength="11"
              aria-label="Input group"
              data-bs-placement="bottom"
              data-bs-toggle="tooltip"
              data-bs-trigger="hover"
              data-bs-html="false"
              title="Enter the callsign of the dx station here"
              v-model="dxcallsign"
            />
            <button
              class="btn btn-sm btn-outline-secondary ms-1 w-50 h-100"
              type="button"
              data-bs-placement="bottom"
              data-bs-toggle="tooltip"
              data-bs-trigger="hover"
              data-bs-html="false"
              title="Send a ping request to a remote station"
              @click="transmitPing()"
              v-bind:class="{ disabled: dxcallsign == '' }"
            >
              Ping
            </button>



          </div>
        </div>
      </div>












  </div>
</div>

</template>
