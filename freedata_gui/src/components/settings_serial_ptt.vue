<template>
  <div>
    <hr class="m-2" />

    <!-- PTT COM port Selector -->
    <div class="input-group input-group-sm mb-1">
      <span class="input-group-text" style="width: 180px">PTT COM port</span>
      <select
        @change="onChange"
        v-model="settings.remote.RADIO.ptt_port"
        class="form-select form-select-sm"
      >
        <option
          v-for="device in serialDevices"
          :value="device.port"
          :key="device.port"
        >
          {{ device.description }}
        </option>
      </select>
    </div>

    <!-- PTT via DTR Selector -->
    <div class="input-group input-group-sm mb-1">
      <span class="input-group-text" style="width: 180px">PTT via DTR</span>
      <select
        class="form-select form-select-sm"
        aria-label=".form-select-sm"
        id="hamlib_dtrstate"
        style="width: 0.5rem"
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
      <span class="input-group-text" style="width: 180px">PTT via RTS</span>
      <select
        class="form-select form-select-sm"
        aria-label=".form-select-sm"
        id="hamlib_dtrstate"
        style="width: 0.5rem"
        @change="onChange"
        v-model="settings.remote.RADIO.serial_rts"
      >
        <option value="ignore">-- Disabled --</option>
        <option value="OFF">LOW</option>
        <option value="ON">HIGH</option>
      </select>
    </div>
  </div>
</template>

<script>
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { useSerialStore } from "../store/serialStore";

export default {
  data() {
    return {
      settings,
      serialDevices: useSerialStore().serialDevices
    };
  },
  methods: {
    onChange(event) {
      onChange(event);
    }
  }
};
</script>