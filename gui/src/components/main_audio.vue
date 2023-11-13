<script setup>
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useAudioStore } from "../store/audioStore.js";
const audio = useAudioStore(pinia);

import { saveModemConfig } from "../js/api";



</script>

<template>
  <div class="card mb-0">
    <div class="card-header p-1">
      <div class="container">
        <div class="row">
          <div class="col-1">
            <i class="bi bi-volume-up" style="font-size: 1.2rem"></i>
          </div>
          <div class="col-10">
            <strong class="fs-5">Audio devices</strong>
          </div>
          <div class="col-1 text-end">
            <button
              type="button"
              data-bs-toggle="modal"
              data-bs-target="#audioHelpModal"
              class="btn m-0 p-0 border-0"
            >
              <i class="bi bi-question-circle" style="font-size: 1rem"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="card-body p-2" style="height: 100px">
      <div class="input-group input-group-sm mb-1">
        <span class="input-group-text">
          <i class="bi bi-mic-fill" style="font-size: 1rem"></i>
        </span>
        <select
          class="form-select form-select-sm"
          aria-label=".form-select-sm"
          v-html="audio.getInputDevices()"
          @change="saveModemConfig"
        ></select>
      </div>
      <div class="input-group input-group-sm">
        <span class="input-group-text">
          <i class="bi bi-volume-up" style="font-size: 1rem"></i>
        </span>
        <select
          class="form-select form-select-sm"
          aria-label=".form-select-sm"
          v-html="audio.getOutputDevices()"
          @change="saveModemConfig"
        ></select>
      </div>
    </div>
  </div>
</template>
