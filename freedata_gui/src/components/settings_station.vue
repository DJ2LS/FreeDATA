<template>

  <div class="alert alert-info" role="alert">
  <strong><i class="bi bi-gear-wide-connected me-1"></i>Station</strong> related settings, like changing your <strong>callsign</strong>, <strong>location</strong> and <strong>general behaviour</strong>.
  </div>

  <!-- station callsign -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">Callsign <div class="ms-2 badge text-bg-secondary text-wrap">
maximum 7 characters are allowed. No special characters. No SSID </div> </span>
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
    <span class="input-group-text w-50 text-wrap" >Callsign SSID <div class="ms-2 badge text-bg-secondary text-wrap">
Set the SSID of your callsign. This allows running several stations with one callsign, but different SSID </div></span>
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
    <span class="input-group-text w-50 text-wrap">Grid Locator / Maidenhead <div class="ms-2 badge text-bg-secondary text-wrap">
max 6 characters of precision, less (2, 4) will be randomized</div> </span>
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
    <label class="input-group-text w-50 text-wrap">Respond to CQ callings with a QRV reply <div class="ms-2 badge text-bg-secondary text-wrap">
The QRV reply will be sent with a random delay. </div> </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="respondCQSwitch"
          v-model="settings.remote.STATION.respond_to_cq"
          @change="onChange"
        />
        <label class="form-check-label" for="respondCQSwitch">Enable</label>
      </div>
    </label>
  </div>

   <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">Enable callsign blacklist <div class="ms-2 badge text-bg-secondary text-wrap">
This allows ignoring requests from blacklisted callsigns. </div></label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="respondEnableBlacklistSwitch"
          v-model="settings.remote.STATION.enable_callsign_blacklist"
          @change="onChange"
        />
        <label class="form-check-label" for="respondEnableBlacklistSwitch">Enable</label>
      </div>
    </label>
  </div>

   <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">Callsign blacklist <div class="ms-2 badge text-bg-secondary text-wrap">
One callsign per line </div></label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">

        <div class="form-floating">
  <textarea class="form-control"
  placeholder="one call per line"
  id="callsignBlacklistfloatingTextarea"
  style="height: 150px"
  v-model="settings.remote.STATION.callsign_blacklist"
  @change="onChange"
  ></textarea>
  <label for="callsignBlacklistfloatingTextarea">One call per line</label>
</div>

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
