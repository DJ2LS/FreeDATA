<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);

import { stopTransmission } from "../../js/api";

function stopAllTransmissions() {
  console.log("stopping transmissions");
  stopTransmission();
}
</script>
<template>
  <a
    class="btn btn-outline-danger d-flex border justify-content-center align-items-center object-fill rounded w-100 h-100"
    id="stop_transmission_connection"
    data-bs-toggle="tooltip"
    data-bs-trigger="hover"
    data-bs-html="false"
    @click="stopAllTransmissions()"
    title="Abort session and stop transmissions"
  >
    <i class="bi bi-sign-stop-fill h1"></i>
  </a>
</template>
