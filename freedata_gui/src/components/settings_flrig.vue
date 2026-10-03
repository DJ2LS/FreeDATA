<template>

     <!-- Flrig host -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.radio.flrighost') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.radio.flrighost_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>

    <input
      id="flrighost"
      v-model="settings.remote.FLRIG.ip"
      type="text"
      class="form-control"
      placeholder="127.0.0.1"
      aria-label="flrig host"
      @change="onChange"
    >
  </div>
     <!-- Flrig port -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.radio.flrigport') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.radio.flrigport_help')"
      >
        <i class="bi bi-question-circle" />
      </button>
    </label>

    <input
      id="flrigport"
      v-model.number="settings.remote.FLRIG.port"
      type="number"
      class="form-control"
      placeholder="12345"
      aria-label="flrig port"
      min="1"
      max="65535"
      @focus="rememberNumber('FLRIG', 'port')"
      @change="onNumberChange($event, 'FLRIG', 'port')"
    >
  </div>


</template>


<script setup>
import { settingsStore as settings, onChange, getRemote } from "../store/settingsStore.js";
import { useSerialStore } from "../store/serialStore";
import { setActivePinia } from "pinia";
import pinia from "../store/index";

setActivePinia(pinia);
const serialStore = useSerialStore(pinia);

// Number inputs: v-model.number yields "" when a field is cleared, which the
// server rejects (it expects an int). Restore the previous value instead of
// saving, round to an integer and clamp to the input's min/max before saving.
const previousNumbers = {};
function rememberNumber(section, key) {
  previousNumbers[`${section}.${key}`] = settings.remote[section][key];
}
function onNumberChange(event, section, key) {
  const el = event.target;
  let value = settings.remote[section][key];
  if (typeof value !== "number" || !Number.isFinite(value)) {
    const previous = previousNumbers[`${section}.${key}`];
    if (previous !== "" && previous !== null && previous !== undefined && Number.isFinite(Number(previous))) {
      settings.remote[section][key] = Number(previous);
    } else {
      getRemote(); // reload the last saved config from the server
    }
    return;
  }
  value = Math.round(value);
  if (el.min !== "" && value < Number(el.min)) value = Number(el.min);
  if (el.max !== "" && value > Number(el.max)) value = Number(el.max);
  settings.remote[section][key] = value;
  previousNumbers[`${section}.${key}`] = value;
  onChange();
}
</script>