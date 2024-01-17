<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore.js";
import { settingsStore } from "../store/settingsStore";
import { onMounted } from "vue";
import { ipcRenderer } from "electron";
const state = useStateStore(pinia);
onMounted(() => {
  window.addEventListener("DOMContentLoaded", () => {
    // we are using this area for implementing the electron runUpdater
    // we need access to DOM for displaying updater results in GUI
    // close app, update and restart
    document
      .getElementById("update_and_install")
      .addEventListener("click", () => {
        ipcRenderer.send("request-restart-and-install-update");
      });
  });
});
</script>

<template>
  <div class="card m-2">
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
        class="btn btn-secondary btn-sm ms-1 me-1"
        id="updater_channel"
        type="button"
        disabled
      >
        Update channel:&nbsp; {{ settingsStore.local.update_channel }}
      </button>
      <button
        class="btn btn-secondary btn-sm ms-1"
        id="updater_status"
        type="button"
        disabled
      >
        ...
      </button>
      <button
        class="btn btn-secondary btn-sm ms-1"
        id="updater_changelog"
        type="button"
        data-bs-toggle="modal"
        data-bs-target="#updaterReleaseNotes"
      >
        Changelog
      </button>
      <button
        class="btn btn-primary btn-sm ms-1"
        id="update_and_install"
        type="button"
        style="display: none"
      >
        Install & Restart
      </button>
    </div>
  </div>
</template>
