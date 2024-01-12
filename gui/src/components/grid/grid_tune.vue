<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);
</script>
<template>
  <a
    class="btn btn-outline-primary d-flex border justify-content-center align-items-center object-fill rounded w-100 h-100"
    id="stop_transmission_connection"
    data-bs-trigger="hover"
    data-bs-html="false"
    data-bs-toggle="modal"
    data-bs-target="#audioModal"
    title="Tune"
  >
    <h5>Tune</h5>
  </a>
</template>
