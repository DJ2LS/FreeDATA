<script setup lang="ts">
// @ts-nocheck
const { distance } = require("qth-locator");

import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);

import { settingsStore as settings } from "../../store/settingsStore.js";

import { useStateStore } from "../../store/stateStore.js";
const state = useStateStore(pinia);

function getDateTime(timestampRaw) {
  var datetime = new Date(timestampRaw * 1000).toLocaleString(
    navigator.language,
    {
      hourCycle: "h23",

      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    },
  );
  return datetime;
}

function getMaidenheadDistance(dxGrid) {
  try {
    return parseInt(distance(settings.remote.STATION.mygrid, dxGrid));
  } catch (e) {
    //
  }
}
function pushToPing(origin) {
  window.dispatchEvent(
    new CustomEvent("stationSelected", { bubbles: true, detail: origin }),
  );
}
</script>
<template>
  <div class="card h-100">
    <div class="card-header p-0">
      <i class="bi bi-list-columns-reverse" style="font-size: 1.2rem"></i>&nbsp;
      <strong>Heard stations</strong>
    </div>

    <div class="card-body overflow-auto p-0">
      <div class="table-responsive">
        <!-- START OF TABLE FOR HEARD STATIONS -->
        <table class="table table-sm table-striped" id="tblHeardStationList">
          <thead>
            <tr>
              <th scope="col" id="thTime">Time</th>
              <th scope="col" id="thDxcall">DXCall</th>
            </tr>
          </thead>
          <tbody id="miniHeardStations">
            <!--https://vuejs.org/guide/essentials/list.html-->
            <tr
              v-for="item in state.heard_stations"
              :key="item.origin"
              @click="pushToPing(item.origin)"
            >
              <td>
                <span class="fs-6">{{ getDateTime(item.timestamp) }}</span>
              </td>

              <td>
                <span>{{ item.origin }}</span>
              </td>
              <!--<td>{{ item.offset }}</td>-->
            </tr>
          </tbody>
        </table>
      </div>

      <!-- END OF HEARD STATIONS TABLE -->
    </div>
  </div>
</template>
