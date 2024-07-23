<script setup>
// Import necessary modules and store
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
import { useStateStore } from '../store/stateStore.js';
import { settingsStore as settings } from '../store/settingsStore.js';

// Initialize Pinia and state store
setActivePinia(pinia);
const state = useStateStore(pinia);
</script>

<template>
  <nav class="navbar bg-body-tertiary border-bottom z-0">
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
