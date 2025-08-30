<template>
  <div
    class="alert alert-info"
    role="alert"
  >
    <strong><i class="bi bi-gear-wide-connected me-1" /></strong>{{ $t('settings.station.introduction') }}
  </div>

  <!-- Station Callsign -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      {{ $t('settings.station.callsign') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.station.callsign_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </span>
    <input
      id="myCall"
      v-model="settings.remote.STATION.mycall"
      type="text"
      class="form-control"
      style="text-transform: uppercase"
      :placeholder="$t('settings.station.callsign_placeholder')"
      aria-label="Station Callsign"
      @change="validateCall"
    >
  </div>

  <!-- Station SSID -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      {{ $t('settings.station.callsignssid') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.station.callsignssid_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </span>
    <select
      id="myCallSSID"
      v-model.number="settings.remote.STATION.myssid"
      class="form-select form-select-sm w-50"
      @change="onChange"
    >
      <option value="0">
        0
      </option>
      <option value="1">
        1
      </option>
      <option value="2">
        2
      </option>
      <option value="3">
        3
      </option>
      <option value="4">
        4
      </option>
      <option value="5">
        5
      </option>
      <option value="6">
        6
      </option>
      <option value="7">
        7
      </option>
      <option value="8">
        8
      </option>
      <option value="9">
        9
      </option>
      <option value="10">
        10
      </option>
      <option value="11">
        11
      </option>
      <option value="12">
        12
      </option>
      <option value="13">
        13
      </option>
      <option value="14">
        14
      </option>
      <option value="15">
        15
      </option>
    </select>
  </div>

  <!-- Station Grid Locator -->
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text w-50 text-wrap">
      {{ $t('settings.station.locator') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.station.locator_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </span>

    <input
  id="myGrid"
  v-model="settings.remote.STATION.mygrid"
  type="text"
  class="form-control"
  :placeholder="$t('settings.station.locator_placeholder')"
  maxlength="6"
  aria-label="Station Grid Locator"
  @change="checkGridsquare"
/>

  </div>

  <!-- Respond to CQ Callings -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.station.respondtocq') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.station.respondtocq_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          id="respondCQSwitch"
          v-model="settings.remote.STATION.respond_to_cq"
          class="form-check-input"
          type="checkbox"
          @change="onChange"
        >
        <label
          class="form-check-label"
          for="respondCQSwitch"
        >{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>

  <!-- Enable Callsign Blacklist -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.station.enablecallsignblacklist') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.station.enablecallsignblacklist_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          id="respondEnableBlacklistSwitch"
          v-model="settings.remote.STATION.enable_callsign_blacklist"
          class="form-check-input"
          type="checkbox"
          @change="onChange"
        >
        <label
          class="form-check-label"
          for="respondEnableBlacklistSwitch"
        >{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>

  <!-- Callsign Blacklist Textarea -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.station.callsignblacklist') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.station.callsignblacklist_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>
    <div class="w-50">
      <div class="form-floating">
        <textarea
          id="callsignBlacklistfloatingTextarea"
          v-model="settings.remote.STATION.callsign_blacklist"
          class="form-control"
          :placeholder="$t('settings.station.callsignblacklist_placeholder')"
          style="height: 150px"
          @change="onChange"
        />
        <label for="callsignBlacklistfloatingTextarea">{{ $t('settings.station.callsignblacklist_help') }}</label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { settingsStore as settings, onChange, getRemote } from "../store/settingsStore.js";
import { validateCallsignWithoutSSID } from "../js/freedata";
import * as bootstrap from "bootstrap";
import i18next from "../js/i18n";

// Initialize Bootstrap tooltips
onMounted(() => {
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  [...tooltipTriggerList].forEach(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
});


function checkGridsquare(e) {
  let value = e.target.value.trim();
  const regex = /^[A-Ra-r]{2}[0-9]{2}([A-Xa-x]{2})?$/;

  if (regex.test(value)) {
    let formatted =
      value.substring(0, 2).toUpperCase() +
      value.substring(2, 4) +
      (value.length === 6 ? value.substring(4, 6).toLowerCase() : "");

    settings.remote.STATION.mygrid = formatted;
    onChange();
  } else {
    alert(i18next.t('settings.station.locator_error'));
  }
}


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
