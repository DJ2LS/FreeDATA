<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { settingsStore as settings} from "../store/settingsStore.js";

import { useAudioStore } from "../store/audioStore.js";
const audioStore = useAudioStore(pinia);

</script>

<template>
  <nav class="navbar bg-body-tertiary border-bottom">
    <div class="mx-auto">
      <span class="badge bg-secondary me-4">
        Modem Connection {{ state.modem_connection }}
      </span>
      <span class="badge bg-secondary me-4">
        Modem {{ state.is_modem_running }}
      </span>
      <span class="badge bg-secondary me-4">
        RIG Control {{ state.rigctld_started }}
      </span>
    </div>
  </nav>
</template>
