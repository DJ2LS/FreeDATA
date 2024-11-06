<template>
  <div class="alert alert-info" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i>Station</strong> related settings, like changing your <strong>callsign</strong>, <strong>location</strong>, and <strong>general behaviour</strong>.
  </div>

  <!-- Station Callsign -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      Callsign
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Enter a valid callsign (Max 7 chars, no special chars)"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </span>
    <input
      type="text"
      class="form-control"
      style="text-transform: uppercase"
      placeholder="Enter your callsign and save it"
      id="myCall"
      aria-label="Station Callsign"
      v-model="settings.remote.STATION.mycall"
      @change="validateCall"
    />
  </div>

  <!-- Station SSID -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      Callsign SSID
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Set a unique SSID for this station"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </span>
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

  <!-- Station Grid Locator -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      Grid Locator / Maidenhead
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Enter a grid locator (Max 6 chars; shorter will randomize)"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </span>
    <input
      type="text"
      class="form-control"
      placeholder="Your grid locator"
      id="myGrid"
      maxlength="6"
      aria-label="Station Grid Locator"
      @change="onChange"
      v-model="settings.remote.STATION.mygrid"
    />
  </div>

  <!-- Respond to CQ Callings -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Respond to CQ callings with a QRV reply
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="QRV reply sent with random delay"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
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

  <!-- Enable Callsign Blacklist -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Enable callsign blacklist
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Ignore requests from blacklisted callsigns"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
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

  <!-- Callsign Blacklist Textarea -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Callsign blacklist
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="One callsign per line"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <div class="w-50">
      <div class="form-floating">
        <textarea
          class="form-control"
          placeholder="One call per line"
          id="callsignBlacklistfloatingTextarea"
          style="height: 150px"
          v-model="settings.remote.STATION.callsign_blacklist"
          @change="onChange"
        ></textarea>
        <label for="callsignBlacklistfloatingTextarea">One call per line</label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { settingsStore as settings, onChange, getRemote } from "../store/settingsStore.js";
import { validateCallsignWithoutSSID } from "../js/freedata";
import * as bootstrap from "bootstrap";

// Initialize Bootstrap tooltips
onMounted(() => {
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  [...tooltipTriggerList].forEach(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
});

// Function to validate and update callsign
function validateCall() {
  let call = settings.remote.STATION.mycall;
  settings.remote.STATION.mycall = call.toUpperCase();

  if (validateCallsignWithoutSSID(settings.remote.STATION.mycall)) {
    onChange();
  } else {
    getRemote();
  }
}
</script>
