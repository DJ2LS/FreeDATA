<script setup>
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);

import { settingsStore } from "../../store/settingsStore.js";
</script>

<template>
  <div
    class="d-flex justify-content-center align-items-center object-fill border rounded w-100 h-100"
  >
    <h2>
      {{ settingsStore.remote.STATION.mycall }}-{{
        settingsStore.remote.STATION.myssid
      }}
    </h2>
  </div>
</template>
