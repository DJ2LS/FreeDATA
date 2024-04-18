<script setup lang="ts">
import { reactive, ref } from "vue";
import { setActivePinia } from "pinia";
import { setConfig } from "../../js/api";
import pinia from "../../store/index";
setActivePinia(pinia);

import { settingsStore } from "../../store/settingsStore.js";
</script>
<template>
  <div class="w-100">
    <div class="input-group input-group-sm" style="width: calc(100% - 24px)">
      <input
        type="text"
        class="form-control"
        disabled
        style="min-width: 3em; background-color: transparent"
        v-model="settingsStore.remote.STATION.mycall"
      />
      <span class="input-group-text">-</span>
      <input
        type="text"
        class="form-control"
        disabled
        style="min-width: 2em; max-width: 2.5em; background-color: transparent"
        v-model="settingsStore.remote.STATION.myssid"
      />
    </div>
  </div>
</template>
