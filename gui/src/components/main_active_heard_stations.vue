<script setup lang="ts">
// @ts-nocheck
const {
  locatorToLatLng,
  distance,
  bearingDistance,
  latLngToLocator,
} = require("qth-locator");

import { saveSettingsToFile } from "../js/settingsHandler";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

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
  <div class="card mb-1 h-100">
    <!--325px-->
    <div class="card-header p-1">
      <div class="container">
        <div class="row">
          <div class="col-auto">
            <i class="bi bi-list-columns-reverse" style="font-size: 1.2rem"></i>
          </div>
          <div class="col-10">
            <strong class="fs-5">Heard stations</strong>
          </div>
          <div class="col-1 text-end">
            <button
              type="button"
              id="openHelpModalHeardStations"
              data-bs-toggle="modal"
              data-bs-target="#heardStationsHelpModal"
              class="btn m-0 p-0 border-0"
            >
              <i class="bi bi-question-circle" style="font-size: 1rem"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="card-body p-0" style="overflow-y: overlay">
      <div class="table-responsive">
        <!-- START OF TABLE FOR HEARD STATIONS -->
        <table class="table table-sm" id="tblHeardStationList">
          <thead>
            <tr>
              <th scope="col" id="thTime">
                <i id="hslSort" class="bi bi-sort-up"></i>Time
              </th>
              <th scope="col" id="thFreq">Frequency</th>
              <th>&nbsp;</th>
              <th scope="col" id="thDxcall">DXCall</th>
              <th scope="col" id="thDxgrid">DXGrid</th>
              <th scope="col" id="thDist">Distance</th>
              <th scope="col" id="thType">Type</th>
              <th scope="col" id="thSnr">SNR (rx/dx)</th>
              <!--<th scope="col">Off</th>-->
            </tr>
          </thead>
          <tbody id="heardstations">
            <!--https://vuejs.org/guide/essentials/list.html-->
            <tr v-for="item in state.heard_stations" :key="item.timestamp">
              <td>{{ getDateTime(item.timestamp) }}</td>
              <td>{{ item.frequency }}</td>
              <td>&nbsp;</td>
              <td>
                <span class="badge bg-secondary">{{ item.dxcallsign }}</span>
              </td>
              <td>{{ item.dxgrid }}</td>
              <td>{{ getMaidenheadDistance(item.dxgrid) }} km</td>
              <td>{{ item.datatype }}</td>
              <td>{{ item.snr }}</td>
              <!--<td>{{ item.offset }}</td>-->
            </tr>
          </tbody>
        </table>
      </div>
      <!-- END OF HEARD STATIONS TABLE -->
    </div>
  </div>
</template>
