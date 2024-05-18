<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);

import { sendModemCQ } from "../../js/api.js";
</script>
<template>
  <div class="fill h-100" style="width: calc(100% - 24px)">
    <a
      class="btn btn-sm btn-secondary d-flex justify-content-center align-items-center object-fill border rounded w-100 h-100"
      @click="sendModemCQ"
      title="Send a CQ call!"
      >CQ</a
    >
  </div>
</template>
