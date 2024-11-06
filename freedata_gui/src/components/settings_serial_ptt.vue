<template>
  <!-- PTT COM Port Selector -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      PTT COM port
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Select the COM port connected to your radio for PTT control"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <select
      class="form-select form-select-sm w-50"
      @change="onChange"
      v-model="settings.remote.RADIO.ptt_port"
    >
      <option
        v-for="device in serialStore.serialDevices"
        :value="device.port"
        :key="device.port"
      >
        {{ device.description }}
      </option>
    </select>
  </div>

  <!-- PTT via DTR Selector -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      PTT via DTR
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Configure DTR line behavior for PTT control"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <select
      class="form-select form-select-sm w-50"
      id="pttDtrSelect"
      @change="onChange"
      v-model="settings.remote.RADIO.serial_dtr"
    >
      <option value="ignore">-- Disabled --</option>
      <option value="OFF">LOW</option>
      <option value="ON">HIGH</option>
    </select>
  </div>

  <!-- PTT via RTS Selector -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      PTT via RTS
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Configure RTS line behavior for PTT control"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <select
      class="form-select form-select-sm w-50"
      id="pttRtsSelect"
      @change="onChange"
      v-model="settings.remote.RADIO.serial_rts"
    >
      <option value="ignore">-- Disabled --</option>
      <option value="OFF">LOW</option>
      <option value="ON">HIGH</option>
    </select>
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