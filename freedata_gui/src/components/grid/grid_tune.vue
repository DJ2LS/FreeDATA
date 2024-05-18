<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);
</script>
<template>
  <div class="fill h-100">
    <a
      class="btn btn-sm btn-secondary d-flex justify-content-center align-items-center object-fill border rounded w-100 h-100"
      data-bs-trigger="hover"
      data-bs-html="false"
      data-bs-toggle="modal"
      data-bs-target="#audioModal"
      title="Tune"
      >Tune</a
    >
  </div>
</template>
