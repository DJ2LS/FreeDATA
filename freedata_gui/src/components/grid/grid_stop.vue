<script setup>
import { setActivePinia } from 'pinia';
import pinia from '../../store/index';
setActivePinia(pinia);

import { stopTransmission } from '../../js/api';

function stopAllTransmissions() {
  console.log('stopping transmissions');
  stopTransmission();
}
</script>

<template>
  <a
    id="stop_transmission_connection"
    class="btn btn-outline-danger d-flex border justify-content-center align-items-center object-fill rounded w-100 h-100"
    data-bs-toggle="tooltip"
    data-bs-trigger="hover"
    data-bs-html="false"
    :title="$t('grid.components.stop_help')"
    @click="stopAllTransmissions"
  >
    <i class="bi bi-sign-stop-fill h1" />
  </a>
</template>
