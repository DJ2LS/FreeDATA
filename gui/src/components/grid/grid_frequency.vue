<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);

import { useStateStore } from "../../store/stateStore.js";
const state = useStateStore(pinia);
</script>
<template>
  <a
    class="d-flex justify-content-center align-items-center object-fill border rounded w-100 h-100 link-underline link-underline-opacity-0 link-underline-opacity-75-hover text-bg-light"
    data-bs-toggle="offcanvas"
    data-bs-target="#offcanvasFrequency"
  >
    {{ state.frequency / 1000 }} kHz
  </a>
</template>
