<script setup>
import { ref } from "vue";
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);

import { sendModemPing } from "../../js/api.js";

const dxcallPing = ref("");

function transmitPing() {
  sendModemPing(dxcallPing.value.toUpperCase());
}

window.addEventListener(
  "stationSelected",
  function (eventdata) {
    dxcallPing.value = eventdata.detail;
  },
  false,
);
</script>

<template>
  <div
    class="input-group"
    style="width: calc(100% - 24px)"
  >
    <input
      v-model="dxcallPing"
      type="text"
      class="form-control"
      style="min-width: 3rem; text-transform: uppercase; height: 31px"
      placeholder="DXcall"
      pattern="[A-Z]*"
      maxlength="11"
      aria-label="Input group"
      aria-describedby="btnGroupAddon"
    >
    <a
      id="sendPing"
      class="btn btn-sm btn-secondary"
      style="max-width: 3em"
      type="button"
      data-bs-placement="bottom"
      data-bs-toggle="tooltip"
      data-bs-trigger="hover"
      data-bs-html="false"
      :title="$t('grid.components.ping_help')"
      @click="transmitPing"
    >
      {{ $t('grid.components.ping') }}
    </a>
  </div>
</template>
