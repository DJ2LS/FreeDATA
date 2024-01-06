<script setup lang="ts">
import { reactive, ref } from "vue";
import { setActivePinia } from "pinia";
import { setConfig } from "../../js/api";
import pinia from "../../store/index";
setActivePinia(pinia);

import { stopTransmission } from "../../js/api";

function stopAllTransmissions() {
  console.log("stopping transmissions");
  stopTransmission();
}
</script>
<template>
  <div
    class="d-flex justify-content-center align-items-center object-fill rounded w-100 h-100"
  >
    <button
      class="btn border btn-outline-danger list-group-item w-100 h-100"
      id="stop_transmission_connection"
      data-bs-toggle="tooltip"
      data-bs-trigger="hover"
      data-bs-html="false"
      @click="stopAllTransmissions()"
      title="Abort session and stop transmissions"
    >
      <i class="bi bi-sign-stop-fill h1"></i>
    </button>
  </div>
</template>
