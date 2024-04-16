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
      id="dbfs_level"
      role="progressbar"
      :style="{ width: state.dbfs_level_percent + '%' }"
      aria-valuenow="0"
      aria-valuemin="0"
      aria-valuemax="100"
    ></div>
    <p
      class="justify-content-center d-flex position-absolute w-100"
      id="dbfs_level_value"
    >
      {{ state.dbfs_level }} dBFS
    </p>
  </div>
  <div class="progress mb-0 rounded-0 rounded-bottom" style="height: 8px">
    <div
      class="progress-bar progress-bar-striped bg-warning"
      role="progressbar"
      style="width: 1%"
      aria-valuenow="1"
      aria-valuemin="0"
      aria-valuemax="100"
    ></div>
    <div
      class="progress-bar bg-success"
      role="progressbar"
      style="width: 89%"
      aria-valuenow="50"
      aria-valuemin="0"
      aria-valuemax="100"
    ></div>
    <div
      class="progress-bar progress-bar-striped bg-warning"
      role="progressbar"
      style="width: 20%"
      aria-valuenow="20"
      aria-valuemin="0"
      aria-valuemax="100"
    ></div>
    <div
      class="progress-bar progress-bar-striped bg-danger"
      role="progressbar"
      style="width: 29%"
      aria-valuenow="29"
      aria-valuemin="0"
      aria-valuemax="100"
    ></div>
  </div>
</template>
