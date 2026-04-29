<script setup>

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings, onChange } from "../store/settingsStore.js";
</script>

<template>
  <!-- Top Info Area for Explorer Settings -->
  <div
    class="alert alert-info"
    role="alert"
  >
    <strong><i class="bi bi-gear-wide-connected me-1" /></strong>{{ $t('settings.web.introduction') }}
  </div>

  <div
    class="alert alert-light"
    role="alert"
  >
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
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          id="ExplorerSwitch"
          v-model="settings.remote.STATION.enable_explorer"
          class="form-check-input"
          type="checkbox"
          @change="onChange"
        >
        <label
          class="form-check-label"
          for="ExplorerSwitch"
        >{{ $t('settings.enable') }}</label>
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
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          id="ExplorerStatsSwitch"
          v-model="settings.remote.STATION.enable_stats"
          class="form-check-input"
          type="checkbox"
          @change="onChange"
        >
        <label
          class="form-check-label"
          for="ExplorerStatsSwitch"
        >{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>
    <!-- Enable PSKReporter -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">

      {{ $t('settings.station.enable_pskreporter') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.station.enable_pskreporter_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline ms-2">
        <input
          id="enablePskreporterSwitch"
          v-model="settings.remote.STATION.enable_pskreporter"
          class="form-check-input"
          type="checkbox"
          @change="onChange"
        >
        <label
          class="form-check-label"
          for="enablePskreporterSwitch"
        >{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>

  <!-- PSKReporter fallback -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.station.pskreporter_fallback_frequency') }}

      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.station.pskreporter_fallback_frequency_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <input
      id="pskreporterFreq"
      v-model="settings.remote.STATION.pskreporter_fallback_frequency"
      type="number"
      class="form-control"
      :placeholder="$t('settings.station.pskreporterfallback_placeholder')"
      @change="onChange"
    >
  </div>
</template>


