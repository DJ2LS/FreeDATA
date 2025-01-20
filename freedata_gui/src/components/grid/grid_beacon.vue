<script setup>
import { setActivePinia } from 'pinia';
import pinia from '../../store/index';
setActivePinia(pinia);

import { setModemBeacon } from '../../js/api.js';
import { useStateStore } from '../../store/stateStore.js';
const state = useStateStore(pinia);

function startStopBeacon() {
  if (state.beacon_state === true) {
    setModemBeacon(false);
  } else {
    setModemBeacon(true);
  }
}
</script>

<template>
  <div class="fill h-100" style="width: calc(100% - 24px)">
    <a
      class="btn btn-sm btn-secondary d-flex justify-content-center align-items-center object-fill border rounded w-100 h-100"
      @click="startStopBeacon"
      title="Enable/disable periodic beacons"
    >
      Beacon&nbsp;
      <span
        role="status"
        :class="{
          'spinner-grow spinner-grow-sm': state.beacon_state === true,
          'disabled': state.beacon_state === false,
        }"
      ></span>
    </a>
  </div>
</template>
