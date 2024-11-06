<script setup>
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { useSerialStore } from "../store/serialStore.js";


// Pinia setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

const serialStore = useSerialStore(pinia);
/*
const settings = ref({
  remote: {
    RIGCTLD: {
      ip: '',
      port: 0,
      enable_vfo: false
    },
    RADIO: {
      control: '',
      model_id: 0
    }
  }
});
*/

</script>

<template>

  <!-- Rigctld IP -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Rigctld IP
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Enter the IP address of the rigctld server"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <input
      type="text"
      class="form-control"
      placeholder="Enter Rigctld IP"
      id="rigctldIp"
      aria-label="Rigctld IP"
      @change="onChange"
      v-model="settings.remote.RIGCTLD.ip"
    />
  </div>

  <!-- Rigctld Port -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Rigctld Port
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Enter the port number of the rigctld server"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <input
      type="number"
      class="form-control"
      placeholder="Enter Rigctld port"
      id="rigctldPort"
      aria-label="Rigctld Port"
      @change="onChange"
      v-model.number="settings.remote.RIGCTLD.port"
    />
  </div>

  <!-- Rigctld VFO Parameter -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Rigctld VFO parameter
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Enable VFO support in rigctld"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="enableVfoSwitch"
          v-model="settings.remote.RIGCTLD.enable_vfo"
          @change="onChange"
        />
        <label class="form-check-label" for="enableVfoSwitch">Enable</label>
      </div>
    </label>
  </div>

  <!-- Conditional Section for Rigctld Bundle -->
  <div :class="settings.remote.RADIO.control == 'rigctld_bundle' ? '' : 'd-none'">
    <!-- Radio Model -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        Radio model
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          title="Select your radio model for rig control"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <select
        class="form-select form-select-sm w-50"
        id="radioModelSelect"
        @change="onChange"
        v-model.number="settings.remote.RADIO.model_id"
      >
        <option selected value="0">-- ignore --</option>
        <option value="2">Hamlib NET rigctl</option>
        <option value="2021">Elecraft K2</option>
      </select>
    </div>

    <!-- Radio Port -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        Radio port
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          title="Select the serial port connected to your radio"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <select
        class="form-select form-select-sm w-50"
        @change="onChange"
        v-model="settings.remote.RADIO.serial_port"
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

    <!-- Serial Speed -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        Serial speed
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          title="Set the baud rate for serial communication"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <select
        class="form-select form-select-sm w-50"
        id="serialSpeedSelect"
        @change="onChange"
        v-model.number="settings.remote.RADIO.serial_speed"
      >
        <option selected value="0">-- ignore --</option>
        <option value="9600">9600</option>
        <option value="19200">19200</option>
        <option value="115200">115200</option>
      </select>
    </div>
  </div>
</template>


