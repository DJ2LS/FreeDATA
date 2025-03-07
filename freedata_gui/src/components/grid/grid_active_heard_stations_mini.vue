<script setup>
// Initialize Pinia and state store
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
import { useStateStore } from "../../store/stateStore.js";

// Set active Pinia store
setActivePinia(pinia);
const state = useStateStore(pinia);

// Format timestamp to human-readable datetime
function getDateTime(timestampRaw) {
  if (!timestampRaw) return "N/A"; // Handle invalid timestamps
  return new Date(timestampRaw * 1000).toLocaleString(
    navigator.language,
    {
      hourCycle: "h23",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }
  );
}

// Dispatch custom event for selected station
function pushToPing(origin) {
  window.dispatchEvent(
    new CustomEvent("stationSelected", { bubbles: true, detail: origin })
  );
}
</script>

<template>
  <div class="card h-100">
    <div class="card-header">
      <i class="bi bi-list-columns-reverse" style="font-size: 1.2rem"></i>&nbsp;
      <strong>{{ $t('grid.components.heardstations') }}</strong>
    </div>

    <div class="card-body overflow-auto p-0">
      <div class="table-responsive">
        <!-- Table for Heard Stations -->
        <table class="table table-sm table-striped">
          <thead>
            <tr>
              <th scope="col">Tim{{ $t('grid.components.time') }}e</th>
              <th scope="col">{{ $t('grid.components.dxcall') }}</th>
            </tr>
          </thead>
          <tbody>
            <!-- Iterate over heard stations -->
            <tr
              v-for="item in state.heard_stations"
              :key="item.origin"
              @click="pushToPing(item.origin)"
              role="row"
              aria-label="Heard Station"
            >
              <td>
                <span class="fs-6">{{ getDateTime(item.timestamp) }}</span>
              </td>
              <td>
                <span>{{ item.origin }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
