<script setup lang="ts">
import { setConfig } from "../js/api";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings } from "../store/settingsStore.js";
</script>

<template>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Enable "is typing"</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="enable_is_writing"
          @change="setConfig"
          v-model="settings.enable_is_writing"
          disabled
        />
        <label class="form-check-label" for="GraphicsSwitch"
          >Additional broadcast burst</label
        >
      </div>
    </label>
  </div>

  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Allow requesting "user profile"</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="enable_request_profile"
          @change="setConfig"
          v-model="settings.enable_request_profile"
          disabled
        />
      </div>
    </label>
  </div>

  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50"
      >Allow requesting "shared folder"</label
    >
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="enable_request_shared_folder"
          @change="setConfig"
          v-model="settings.enable_request_shared_folder"
          disabled
        />
      </div>
    </label>
  </div>

  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Shared folder path</label>
    <input
      type="text"
      class="form-control w-50"
      id="shared_folder_path"
      @change="setConfig"
      v-model="settings.shared_folder_path"
      disabled
    />
  </div>

  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50"
      >Enable auto retry on Beacon or Ping
    </label>

    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="enable_auto_retry"
          @change="setConfig"
          v-model="settings.enable_auto_retry"
        />
      </div>
    </label>
  </div>

  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50">message retry attempts</span>
    <select
      class="form-select form-select-sm w-50"
      id="max_retry_attempts"
      @change="setConfig"
      v-model="settings.max_retry_attempts"
    >
      <option value="1">1</option>
      <option value="2">2</option>
      <option value="3">3</option>
      <option value="4">4</option>
      <option value="5">5</option>
      <option value="6">6</option>
      <option value="7">7</option>
      <option value="8">8</option>
      <option value="9">9</option>
    </select>
  </div>
</template>
