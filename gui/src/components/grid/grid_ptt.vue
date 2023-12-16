<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);

import { useStateStore } from "../../store/stateStore.js";
const state = useStateStore(pinia);
</script>
<template>
  <div class="d-flex justify-content-center align-items-center object-fill border rounded w-100 h-100" :class="state.ptt_state === true ? 'text-bg-warning' : 'text-bg-light'">TX</div>
</template>
