<script setup>

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

</script>

<template>
  <!-- Top Warning Area -->
  <div
    class="alert alert-danger"
    role="alert"
  >
    <strong><i class="bi bi-shield-exclamation me-1" /></strong> {{ $t('settings.exp.introduction') }}
  </div>


  <div
    class="alert alert-info"
    role="alert"
  >
    <strong><i class="bi bi-info-circle me-1" /></strong>{{ $t('settings.exp.info') }}
  </div>
</template>

