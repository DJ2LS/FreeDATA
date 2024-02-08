<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { getOverallHealth } from "../js/eventHandler.js"

</script>
<template>
  <a
    class="btn border btn-outline-secondary list-group-item mb-5"
    data-bs-html="false"
    data-bs-toggle="modal"
    data-bs-target="#modemCheck"
    title="Check FreeDATA status"
    :class="
      getOverallHealth() > 4
        ? 'bg-danger'
        : getOverallHealth() < 2
          ? ''
          : 'bg-warning'
    "
    ><i class="bi bi-activity h3"></i>
  </a>
</template>
