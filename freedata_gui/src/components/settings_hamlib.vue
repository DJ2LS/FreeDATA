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
      <span id="rigctldIpHelp" class="ms-2 badge bg-secondary text-wrap">
        Enter the IP address of the rigctld server
      </span>
    </label>
    <input
      type="text"
      class="form-control"
      placeholder="Enter Rigctld IP"
      id="rigctldIp"
      aria-label="Rigctld IP"
      aria-describedby="rigctldIpHelp"
      @change="onChange"
      v-model="settings.remote.RIGCTLD.ip"
    />
  </div>

  <!-- Rigctld Port -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Rigctld Port
      <span id="rigctldPortHelp" class="ms-2 badge bg-secondary text-wrap">
        Enter the port number of the rigctld server
      </span>
    </label>
    <input
      type="number"
      class="form-control"
      placeholder="Enter Rigctld port"
      id="rigctldPort"
      aria-label="Rigctld Port"
      aria-describedby="rigctldPortHelp"
      @change="onChange"
      v-model.number="settings.remote.RIGCTLD.port"
    />
  </div>

  <!-- Rigctld VFO Parameter -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Rigctld VFO parameter
      <span id="rigctldVfoHelp" class="ms-2 badge bg-secondary text-wrap">
        Enable VFO support in rigctld
      </span>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="enableVfoSwitch"
          aria-describedby="rigctldVfoHelp"
          v-model="settings.remote.RIGCTLD.enable_vfo"
          @change="onChange"
        />
        <label class="form-check-label" for="enableVfoSwitch">Enable</label>
      </div>
    </label>
  </div>

  <hr class="m-2" />

  <!-- Conditional Section for Rigctld Bundle -->
  <div :class="settings.remote.RADIO.control == 'rigctld_bundle' ? '' : 'd-none'">
    <!-- Radio Model -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        Radio model
        <span id="radioModelHelp" class="ms-2 badge bg-secondary text-wrap">
          Select your radio model for rig control
        </span>
      </label>
      <select
        class="form-select form-select-sm w-50"
        aria-label="Radio Model"
        aria-describedby="radioModelHelp"
        id="radioModelSelect"
        @change="onChange"
        v-model.number="settings.remote.RADIO.model_id"
      >
        <option selected value="0">-- ignore --</option>
        <!-- Include your list of radio models here -->
        <!-- Example options -->
        <option value="2">Hamlib NET rigctl</option>
        <option value="2021">Elecraft K2</option>
        <!-- ... -->
      </select>
    </div>

    <!-- Radio Port -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        Radio port
        <span id="radioPortHelp" class="ms-2 badge bg-secondary text-wrap">
          Select the serial port connected to your radio
        </span>
      </label>
      <select
        class="form-select form-select-sm w-50"
        aria-describedby="radioPortHelp"
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
        <span id="serialSpeedHelp" class="ms-2 badge bg-secondary text-wrap">
          Set the baud rate for serial communication
        </span>
      </label>
      <select
        class="form-select form-select-sm w-50"
        aria-describedby="serialSpeedHelp"
        id="serialSpeedSelect"
        @change="onChange"
        v-model.number="settings.remote.RADIO.serial_speed"
      >
        <option selected value="0">-- ignore --</option>
        <option value="1200">1200</option>
        <option value="2400">2400</option>
        <option value="4800">4800</option>
        <option value="9600">9600</option>
        <option value="19200">19200</option>
        <option value="38400">38400</option>
        <option value="57600">57600</option>
        <option value="115200">115200</option>
      </select>
    </div>

    <!-- Data Bits -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        Data bits
        <span id="dataBitsHelp" class="ms-2 badge bg-secondary text-wrap">
          Choose the number of data bits
        </span>
      </label>
      <select
        class="form-select form-select-sm w-50"
        aria-describedby="dataBitsHelp"
        id="dataBitsSelect"
        @change="onChange"
        v-model.number="settings.remote.RADIO.data_bits"
      >
        <option selected value="0">-- ignore --</option>
        <option value="7">7</option>
        <option value="8">8</option>
      </select>
    </div>

    <!-- Stop Bits -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        Stop bits
        <span id="stopBitsHelp" class="ms-2 badge bg-secondary text-wrap">
          Choose the number of stop bits
        </span>
      </label>
      <select
        class="form-select form-select-sm w-50"
        aria-describedby="stopBitsHelp"
        id="stopBitsSelect"
        @change="onChange"
        v-model.number="settings.remote.RADIO.stop_bits"
      >
        <option selected value="0">-- ignore --</option>
        <option value="1">1</option>
        <option value="2">2</option>
      </select>
    </div>

    <!-- Serial Handshake -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        Serial handshake
        <span id="serialHandshakeHelp" class="ms-2 badge bg-secondary text-wrap">
          Set the serial handshake method
        </span>
      </label>
      <select
        class="form-select form-select-sm w-50"
        aria-describedby="serialHandshakeHelp"
        id="serialHandshakeSelect"
        @change="onChange"
        v-model="settings.remote.RADIO.serial_handshake"
      >
        <option selected value="ignore">-- ignore --</option>
        <option value="None">None (Default)</option>
        <!-- Add more options if needed -->
      </select>
    </div>

    <!-- PTT Device Port -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        PTT device port
        <span id="pttDevicePortHelp" class="ms-2 badge bg-secondary text-wrap">
          Select the port used for PTT control
        </span>
      </label>
      <select
        class="form-select form-select-sm w-50"
        aria-describedby="pttDevicePortHelp"
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

    <!-- PTT Type -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        PTT type
        <span id="pttTypeHelp" class="ms-2 badge bg-secondary text-wrap">
          Select the method for PTT control
        </span>
      </label>
      <select
        class="form-select form-select-sm w-50"
        aria-describedby="pttTypeHelp"
        id="pttTypeSelect"
        @change="onChange"
        v-model="settings.remote.RADIO.ptt_type"
      >
        <option selected value="ignore">-- ignore --</option>
        <option value="NONE">NONE</option>
        <option value="RIG">RIG</option>
        <option value="USB">USB</option>
        <option value="RTS">Serial RTS</option>
        <option value="PARALLEL">Rig PARALLEL</option>
        <option value="MICDATA">Rig MICDATA</option>
        <option value="CM108">Rig CM108</option>
      </select>
    </div>

    <!-- DCD -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        DCD
        <span id="dcdHelp" class="ms-2 badge bg-secondary text-wrap">
          Select the Data Carrier Detect method
        </span>
      </label>
      <select
        class="form-select form-select-sm w-50"
        aria-describedby="dcdHelp"
        id="dcdSelect"
        @change="onChange"
        v-model="settings.remote.RADIO.serial_dcd"
      >
        <option selected value="ignore">-- ignore --</option>
        <option value="NONE">NONE</option>
        <option value="RIG">RIG/CAT</option>
        <option value="DSR">DSR</option>
        <option value="CTS">CTS</option>
        <option value="CD">CD</option>
        <option value="PARALLEL">PARALLEL</option>
      </select>
    </div>

    <!-- DTR -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        DTR
        <span id="dtrHelp" class="ms-2 badge bg-secondary text-wrap">
          Set the DTR line state
        </span>
      </label>
      <select
        class="form-select form-select-sm w-50"
        aria-describedby="dtrHelp"
        id="dtrSelect"
        @change="onChange"
        v-model="settings.remote.RADIO.serial_dtr"
      >
        <option selected value="ignore">-- ignore --</option>
        <option value="OFF">OFF</option>
        <option value="ON">ON</option>
      </select>
    </div>

    <!-- Rigctld Command -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        Rigctld command
        <span id="rigctldCommandHelp" class="ms-2 badge bg-secondary text-wrap">
          Auto-populated command based on settings
        </span>
      </label>
      <input
        type="text"
        class="form-control"
        id="rigctldCommand"
        aria-label="Rigctld Command"
        aria-describedby="rigctldCommandHelp"
        disabled
        placeholder="Auto-populated from above settings"
      />
      <button
        class="btn btn-outline-secondary"
        type="button"
        id="btnHamlibCopyCommand"
      >
        <i id="btnHamlibCopyCommandBi" class="bi bi-clipboard"></i>
      </button>
    </div>

    <!-- Rigctld Custom Arguments -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        Rigctld custom arguments
        <span id="rigctldArgsHelp" class="ms-2 badge bg-secondary text-wrap">
          Additional arguments for rigctld (usually not needed)
        </span>
      </label>
      <input
        type="text"
        class="form-control"
        placeholder="Optional custom arguments"
        id="rigctldCustomArgs"
        aria-label="Rigctld Custom Arguments"
        aria-describedby="rigctldArgsHelp"
        @change="onChange"
        v-model="settings.remote.RIGCTLD.arguments"
      />
    </div>
  </div>
</template>

