<script setup lang="ts">
import { ref } from "vue";
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);

import { useStateStore } from "../../store/stateStore.js";
import { sendModemPing } from "../../js/api.js";

const state = useStateStore(pinia);
function transmitPing() {
  sendModemPing(dxcallPing.value.toUpperCase());
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
  <div class="input-group" style="width: calc(100% - 24px)">
    <input
      type="text"
      class="form-control"
      style="min-width: 3rem; text-transform: uppercase; height: 31px"
      placeholder="DXcall"
      pattern="[A-Z]*"
      maxlength="11"
      aria-label="Input group"
      aria-describedby="btnGroupAddon"
      v-model="dxcallPing"
    />
    <a
      class="btn btn-sm btn-secondary"
      style="max-width: 3em"
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
    </a>
  </div>
</template>
