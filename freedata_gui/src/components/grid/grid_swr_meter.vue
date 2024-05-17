<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);

import { useStateStore } from "../../store/stateStore.js";
const state = useStateStore(pinia);
</script>
<template>
  <div class="progress mb-0 rounded-0 rounded-top" style="height: 22px">
    <div
      class="progress-bar progress-bar-striped bg-primary force-gpu"
      id="swr_level"
      role="progressbar"
      :style="{ width: state.swr_percent + '%' }"
      aria-valuenow="{{state.swr_percent}}"
      aria-valuemin="0"
      aria-valuemax="5"
    ></div>
    <p
      class="justify-content-center d-flex position-absolute w-100"
      id="swr_level_value"
    >
      SWR 1:{{ state.swr_raw }}
    </p>
  </div>
  <div class="progress mb-0 rounded-0 rounded-bottom" style="height: 8px">
    <div
      class="progress-bar bg-success"
      role="progressbar"
      style="width: 25%"
      aria-valuenow="25"
      aria-valuemin="0"
      aria-valuemax="100"
    ></div>
    <div
      class="progress-bar progress-bar-striped bg-warning"
      role="progressbar"
      style="width: 50%"
      aria-valuenow="50"
      aria-valuemin="0"
      aria-valuemax="100"
    ></div>
    <div
      class="progress-bar progress-bar-striped bg-danger"
      role="progressbar"
      style="width: 25%"
      aria-valuenow="25"
      aria-valuemin="0"
      aria-valuemax="100"
    ></div>
  </div>
</template>
