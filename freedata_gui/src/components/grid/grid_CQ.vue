<script setup>
import { setActivePinia } from 'pinia';
import pinia from '../../store/index';
setActivePinia(pinia);
import { ref } from "vue";


import { sendModemCQ } from '../../js/api.js';
const isCQButtonDisabled = ref(false);

// Function to send CQ and handle button disable and cooldown
async function handleCQCall() {
  isCQButtonDisabled.value = true;

  // Send CQ message
  await sendModemCQ();

  // Wait for 6 seconds (cooldown period)
  setTimeout(() => {
    isCQButtonDisabled.value = false;
  }, 6000);
}


</script>

<template>
  <div class="fill h-100" style="width: calc(100% - 24px)">
    <a
      class="btn btn-sm btn-secondary d-flex justify-content-center align-items-center object-fill border rounded w-100 h-100"
      @click="handleCQCall"
      title="Send a CQ call!"
    >
      <span v-if="!isCQButtonDisabled">CQ</span>
      <span v-else>...</span>
    </a>
  </div>
</template>
