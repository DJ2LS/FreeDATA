<script setup>

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings, onChange } from "../store/settingsStore.js";
</script>

<template>
  <!-- Top Info Area for Explorer Settings -->
  <div class="alert alert-info" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i></strong>{{ $t('settings.web.introduction') }}
  </div>

    <div class="alert alert-light" role="alert">
      {{ $t('settings.web.description') }}
  </div>

  <!-- Explorer Publishing -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.web.enableexplorer') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.web.enableexplorer_help')"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="ExplorerSwitch"
          @change="onChange"
          v-model="settings.remote.STATION.enable_explorer"
        />
        <label class="form-check-label" for="ExplorerSwitch">{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>

  <!-- Explorer Stats Publishing -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.web.enablestats') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.web.enablestats_help')"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="ExplorerStatsSwitch"
          @change="onChange"
          v-model="settings.remote.STATION.enable_stats"
        />
        <label class="form-check-label" for="ExplorerStatsSwitch">{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>
</template>


