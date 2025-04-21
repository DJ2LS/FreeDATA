<template>

     <!-- Flrig host -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.radio.flrighost') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.radio.flrighost_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>

    <input
      id="flrighost"
      v-model="settings.remote.FLRIG.ip"
      type="text"
      class="form-control"
      placeholder="127.0.0.1"
      aria-label="flrig host"
      @change="onChange"
    >
  </div>
     <!-- Flrig port -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.radio.flrigport') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.radio.flrigport_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>

    <input
      id="flrigport"
      v-model.number="settings.remote.FLRIG.port"
      type="number"
      class="form-control"
      placeholder="12345"
      aria-label="flrig port"
      @change="onChange"
    >
  </div>


</template>


<script setup>
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { useSerialStore } from "../store/serialStore";
import { setActivePinia } from "pinia";
import pinia from "../store/index";

setActivePinia(pinia);
const serialStore = useSerialStore(pinia);
</script>