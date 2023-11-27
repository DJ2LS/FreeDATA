<script setup lang="ts">
// @ts-nocheck
const { distance } = require("qth-locator");

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings } from "../store/settingsStore.js";

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

function getDateTime(timestampRaw) {
  var datetime = new Date(timestampRaw * 1000).toLocaleString(
    navigator.language,
    {
      hourCycle: "h23",
      year: "numeric",
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
    return parseInt(distance(settings.mygrid, dxGrid));
  } catch (e) {
    //
  }
}
</script>
<template>
  <div class="card h-100">
    <!--325px-->
    <div class="card-header">
      <i class="bi bi-list-columns-reverse" style="font-size: 1rem"></i>&nbsp;
      <strong>Heard stations</strong>
    </div>

    <div class="card-body">
      <div class="table-responsive">
        <!-- START OF TABLE FOR HEARD STATIONS -->
        <table class="table table-sm" id="tblHeardStationList">
          <thead>
            <tr>
              <th scope="col" id="thTime">Time</th>
              <th scope="col" id="thFreq">Freq</th>
              <th scope="col" id="thDxcall">DXCall</th>
              <th scope="col" id="thDxgrid">Grid</th>
              <th scope="col" id="thDist">Dist</th>
              <th scope="col" id="thType">Type</th>
              <th scope="col" id="thSnr">SNR</th>
              <!--<th scope="col">Off</th>-->
            </tr>
          </thead>
          <tbody id="gridHeardStations">
            <!--https://vuejs.org/guide/essentials/list.html-->
            <tr v-for="item in state.heard_stations" :key="item.timestamp">
              <td>
                <span class="badge bg-secondary">{{
                  getDateTime(item.timestamp)
                }}</span>
              </td>
              <td>
                <span class="badge bg-secondary"
                  >{{ item.frequency / 1000 }} kHz</span
                >
              </td>
              <td>
                <span class="badge bg-secondary">{{ item.dxcallsign }}</span>
              </td>
              <td>
                <span class="badge bg-secondary">{{ item.dxgrid }}</span>
              </td>
              <td>
                <span class="badge bg-secondary"
                  >{{ getMaidenheadDistance(item.dxgrid) }} km</span
                >
              </td>
              <td>
                <span class="badge bg-secondary">{{ item.datatype }}</span>
              </td>
              <td>
                <span class="badge bg-secondary">{{ item.snr }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- END OF HEARD STATIONS TABLE -->
    </div>
  </div>
</template>
