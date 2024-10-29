<template>

  <!-- PTT COM Port Selector -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      PTT COM port
      <span id="pttComPortHelp" class="ms-2 badge bg-secondary text-wrap">
        Select the COM port connected to your radio for PTT control
      </span>
    </label>
    <select
      class="form-select form-select-sm w-50"
      aria-describedby="pttComPortHelp"
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
      <span id="pttDtrHelp" class="ms-2 badge bg-secondary text-wrap">
        Configure DTR line behavior for PTT control
      </span>
    </label>
    <select
      class="form-select form-select-sm w-50"
      id="pttDtrSelect"
      aria-describedby="pttDtrHelp"
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
      <span id="pttRtsHelp" class="ms-2 badge bg-secondary text-wrap">
        Configure RTS line behavior for PTT control
      </span>
    </label>
    <select
      class="form-select form-select-sm w-50"
      id="pttRtsSelect"
      aria-describedby="pttRtsHelp"
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