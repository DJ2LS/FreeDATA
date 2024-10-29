<template>

  <div class="alert alert-info" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i>Station</strong> related settings, like changing your <strong>callsign</strong>, <strong>location</strong>, and <strong>general behaviour</strong>.
  </div>

  <!-- Station Callsign -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      Callsign
      <span id="myCallHelp" class="ms-2 badge bg-secondary text-wrap">
        Max 7 chars. No special chars.
      </span>
    </span>
    <input
      type="text"
      class="form-control"
      style="text-transform: uppercase"
      placeholder="Enter your callsign and save it"
      id="myCall"
      aria-label="Station Callsign"
      aria-describedby="myCallHelp"
      v-model="settings.remote.STATION.mycall"
      @change="validateCall"
    />
  </div>

  <!-- Station SSID -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      Callsign SSID
      <span id="myCallSSIDHelp" class="ms-2 badge bg-secondary text-wrap">
        Set the SSID for multiple stations
      </span>
    </span>
    <select
      class="form-select form-select-sm w-50"
      id="myCallSSID"
      aria-describedby="myCallSSIDHelp"
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

  <!-- Station Grid Locator -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      Grid Locator / Maidenhead
      <span id="myGridHelp" class="ms-2 badge bg-secondary text-wrap">
        Max 6 chars; shorter will randomize
      </span>
    </span>
    <input
      type="text"
      class="form-control"
      placeholder="Your grid locator"
      id="myGrid"
      maxlength="6"
      aria-label="Station Grid Locator"
      aria-describedby="myGridHelp"
      @change="onChange"
      v-model="settings.remote.STATION.mygrid"
    />
  </div>

  <!-- Respond to CQ Callings -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Respond to CQ callings with a QRV reply
      <span id="respondCQHelp" class="ms-2 badge bg-secondary text-wrap">
        QRV reply sent with random delay.
      </span>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="respondCQSwitch"
          aria-describedby="respondCQHelp"
          v-model="settings.remote.STATION.respond_to_cq"
          @change="onChange"
        />
        <label class="form-check-label" for="respondCQSwitch">Enable</label>
      </div>
    </label>
  </div>

  <!-- Enable Callsign Blacklist -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Enable callsign blacklist
      <span id="enableBlacklistHelp" class="ms-2 badge bg-secondary text-wrap">
        Ignore requests from blacklisted callsigns.
      </span>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="respondEnableBlacklistSwitch"
          aria-describedby="enableBlacklistHelp"
          v-model="settings.remote.STATION.enable_callsign_blacklist"
          @change="onChange"
        />
        <label class="form-check-label" for="respondEnableBlacklistSwitch">Enable</label>
      </div>
    </label>
  </div>

  <!-- Callsign Blacklist Textarea -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Callsign blacklist
      <span id="callsignBlacklistHelp" class="ms-2 badge bg-secondary text-wrap">
        One callsign per line
      </span>
    </label>
    <div class="w-50">
      <div class="form-floating">
        <textarea
          class="form-control"
          placeholder="One call per line"
          id="callsignBlacklistfloatingTextarea"
          style="height: 150px"
          aria-describedby="callsignBlacklistHelp"
          v-model="settings.remote.STATION.callsign_blacklist"
          @change="onChange"
        ></textarea>
        <label for="callsignBlacklistfloatingTextarea">One call per line</label>
      </div>
    </div>
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
