<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

function getOverallHealth() {
  //Return a number indicating health for icon bg color; lower the number the healthier
  let health = 0;
  if (state.modem_connection !== "connected") health += 5;
  if (!state.is_modem_running) health += 3;
  if (
    settings.radiocontrol === "rigctld" &&
    (state.rigctld_started === undefined || state.rigctld_started === "false")
  )
    health += 2;
  if (process.env.FDUpdateAvail === "1") health += 1;
  return health;
}
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
