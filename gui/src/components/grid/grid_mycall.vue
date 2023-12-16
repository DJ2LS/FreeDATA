<script setup lang="ts">
import { reactive, ref } from "vue";
import { setActivePinia } from "pinia";
import { setConfig } from "../../js/api";
import pinia from "../../store/index";
setActivePinia(pinia);

import { settingsStore } from "../../store/settingsStore.js";

function updateMyCall() {
  setConfig();
}
</script>
<template>
  <div
    class="d-flex justify-content-center align-items-center object-fill border rounded text-bg-light w-100 h-100"
  ><strong>
    {{ settingsStore.remote.STATION.mycall}}-{{ settingsStore.remote.STATION.myssid}}
  </strong>
  </div>
  
</template>
