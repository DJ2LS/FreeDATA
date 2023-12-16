<script setup lang="ts">
import { reactive, ref } from "vue";
import { setActivePinia } from "pinia";
import { setConfig } from "../../js/api";
import pinia from "../../store/index";
setActivePinia(pinia);

import { settingsStore as setting } from "../../store/settingsStore.js";
const settings = reactive(setting);
import { useStateStore } from "../../store/stateStore.js";

const state = useStateStore(pinia);

function updateMyCall()
{
  setConfig();
}

</script>
<template>
<div class="w-100">
  <div class="input-group input-group-sm" style="width: calc(100% - 24px);">
  
  <input type="text" class="form-control" style="min-width: 3em;" placeholder="mycall" v-model=settings.remote.STATION.mycall>
  <span class="input-group-text">-</span>
  <input type="text" class="form-control" style="min-width: 2em;max-width: 2.5em;" placeholder="id" v-model=settings.remote.STATION.myssid>
  <a class="btn btn-sm btn-secondary" title="Apply changes to callsign/ssid" @click="updateMyCall"><i class="bi bi-check"></i></a>
 </div>
</div>
</template>
