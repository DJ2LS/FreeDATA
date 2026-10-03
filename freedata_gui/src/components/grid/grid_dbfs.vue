<script setup>
import { setActivePinia } from 'pinia';
import pinia from '../../store/index';
setActivePinia(pinia);

import { useStateStore } from '../../store/stateStore.js';
const state = useStateStore(pinia);
</script>

<template>
  <div
    class="progress mb-0 rounded-0 rounded-top"
    style="height: 22px"
  >
    <div
      class="progress-bar progress-bar-striped bg-primary force-gpu"
      role="progressbar"
      :style="{ width: state.dbfs_level_percent + '%' }"
      :aria-valuenow="state.dbfs_level_percent"
      aria-valuemin="0"
      aria-valuemax="100"
    />
    <p
      class="justify-content-center d-flex position-absolute w-100"
    >
      {{ state.dbfs_level }} dBFS
    </p>
  </div>
  <div
    class="progress mb-0 rounded-0 rounded-bottom"
    style="height: 8px"
  >
    <div
      class="progress-bar progress-bar-striped bg-warning"
      role="progressbar"
      style="width: 1%"
      aria-valuenow="1"
      aria-valuemin="0"
      aria-valuemax="100"
    />
    <div
      class="progress-bar bg-success"
      role="progressbar"
      style="width: 64%"
      aria-valuenow="64"
      aria-valuemin="0"
      aria-valuemax="100"
    />
    <div
      class="progress-bar progress-bar-striped bg-warning"
      role="progressbar"
      style="width: 14%"
      aria-valuenow="14"
      aria-valuemin="0"
      aria-valuemax="100"
    />
    <div
      class="progress-bar progress-bar-striped bg-danger"
      role="progressbar"
      style="width: 21%"
      aria-valuenow="21"
      aria-valuemin="0"
      aria-valuemax="100"
    />
  </div>
</template>
