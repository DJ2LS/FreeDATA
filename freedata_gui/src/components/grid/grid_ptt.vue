<script setup>
import { setActivePinia } from 'pinia';
import pinia from '../../store/index';
setActivePinia(pinia);

import { useStateStore } from '../../store/stateStore.js';
const state = useStateStore(pinia);
</script>

<template>
  <div
    class="d-flex justify-content-center align-items-center object-fill border rounded w-100 h-100"
    :class="state.ptt_state ? 'text-bg-warning' : 'text-bg-white'"
  >
    <h2>{{ $t('grid.components.onair').toUpperCase() }}</h2>
  </div>
</template>
