<template>
  <!-- PTT COM Port Selector -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.radio.serialpttcomport') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.radio.serialpttcomport_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <select
      v-model="settings.remote.RADIO.ptt_port"
      class="form-select form-select-sm w-50"
      @change="onChange"
    >
      <option
        v-for="device in serialStore.serialDevices"
        :key="device.port"
        :value="device.port"
      >
        {{ device.description }}
      </option>
    </select>
  </div>

  <!-- Radio Custom Port -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.radio.serialpttcustomcomport') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.radio.serialpttcustomcomport_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>

    <input
      id="rigctldIp"
      v-model="settings.remote.RADIO.ptt_port"
      type="text"
      class="form-control"
      placeholder="settings.remote.RADIO.ptt_port.port"
      aria-label="Rigctld IP"
      @change="onChange"
    >
  </div>
  <!-- PTT via DTR Selector -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.radio.serialpttviadtr') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.radio.serialpttviadtr_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <select
      id="pttDtrSelect"
      v-model="settings.remote.RADIO.serial_dtr"
      class="form-select form-select-sm w-50"
      @change="onChange"
    >
      <option value="ignore">
        -- Disabled --
      </option>
      <option value="OFF">
        LOW
      </option>
      <option value="ON">
        HIGH
      </option>
    </select>
  </div>

  <!-- PTT via RTS Selector -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.radio.serialpttviarts') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.radio.serialpttviarts_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <select
      id="pttRtsSelect"
      v-model="settings.remote.RADIO.serial_rts"
      class="form-select form-select-sm w-50"
      @change="onChange"
    >
      <option value="ignore">
        -- Disabled --
      </option>
      <option value="OFF">
        LOW
      </option>
      <option value="ON">
        HIGH
      </option>
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