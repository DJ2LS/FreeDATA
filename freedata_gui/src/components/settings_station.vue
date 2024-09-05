<template>
  <!-- station callsign -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Your station callsign</span>
    <input
      type="text"
      class="form-control"
      style="text-transform: uppercase"
      placeholder="Enter your callsign and save it"
      id="myCall"
      aria-label="Station Callsign"
      aria-describedby="basic-addon1"
      v-model="settings.remote.STATION.mycall"
      @change="validateCall"
    />
  </div>

  <!-- station ssid -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Call SSID</span>
    <select
      class="form-select form-select-sm w-50"
      id="myCallSSID"
      @change="onChange"
      v-model.number="settings.remote.STATION.myssid"
    >
      <option value="0">0</option>
      <option value="1">1</option>
      <option value="2">2</option>
      <option value="3">3</option>
      <option value="4">4</option>
      <option value="5">5</option>
      <option value="6">6</option>
      <option value="7">7</option>
      <option value="8">8</option>
      <option value="9">9</option>
      <option value="10">10</option>
      <option value="11">11</option>
      <option value="12">12</option>
      <option value="13">13</option>
      <option value="14">14</option>
      <option value="15">15</option>
    </select>
  </div>

  <!-- station grid locator -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Grid Locator</span>
    <input
      type="text"
      class="form-control"
      placeholder="Your grid locator"
      id="myGrid"
      maxlength="6"
      aria-label="Station Grid Locator"
      aria-describedby="basic-addon1"
      @change="onChange"
      v-model="settings.remote.STATION.mygrid"
    />
  </div>

  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50">Respond to CQ</label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="respondCQSwitch"
          v-model="settings.remote.STATION.respond_to_cq"
          @change="onChange"
        />
        <label class="form-check-label" for="respondCQSwitch">QRV</label>
      </div>
    </label>
  </div>


</template>

<script setup>
import { settingsStore as settings, onChange, getRemote } from "../store/settingsStore.js";
import { validateCallsignWithoutSSID } from "../js/freedata";

// Function to validate and update callsign
function validateCall() {
  // Ensure callsign is uppercase
  let call = settings.remote.STATION.mycall;
  settings.remote.STATION.mycall = call.toUpperCase();

  if (validateCallsignWithoutSSID(settings.remote.STATION.mycall)) {
    // Send new callsign to modem if valid
    onChange();
  } else {
    // Reload settings from modem as invalid callsign was passed in
    getRemote();
  }
}
</script>
