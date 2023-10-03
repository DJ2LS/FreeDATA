<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);
</script>

<template>
  <div class="card mb-0">
    <div class="card-header p-1 d-flex">
      <div class="container">
        <div class="row">
          <div class="col-1">
            <i class="bi bi-cloud-download" style="font-size: 1.2rem"></i>
          </div>
          <div class="col-3">
            <strong class="fs-5">Updater</strong>
          </div>
          <div class="col-7">
            <div class="progress w-100 ms-1 m-1">
              <div
                class="progress-bar"
                style="width: 0%"
                role="progressbar"
                id="UpdateProgressBar"
                aria-valuenow="0"
                aria-valuemin="0"
                aria-valuemax="100"
              >
                <span id="UpdateProgressInfo"></span>
              </div>
            </div>
          </div>

          <div class="col-1 text-end">
            <button
              type="button"
              id="openHelpModalUpdater"
              data-bs-toggle="modal"
              data-bs-target="#updaterHelpModal"
              class="btn m-0 p-0 border-0"
            >
              <i class="bi bi-question-circle" style="font-size: 1rem"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="card-body p-2 mb-1">
      <button
        class="btn btn-secondary btn-sm"
        id="updater_channel"
        type="button"
        disabled
      >
        {{ settings.update_channel }}
      </button>
      <button
        class="btn btn-secondary btn-sm"
        id="updater_status"
        type="button"
        disabled
      >
        ...
      </button>
      <button
        class="btn btn-secondary btn-sm"
        id="updater_changelog"
        type="button"
        style="display: none"
      >
        Changelog
      </button>
      <button
        class="btn btn-primary btn-sm"
        id="update_and_install"
        type="button"
        style="display: none"
      >
        Install & Restart
      </button>
    </div>
  </div>
</template>
