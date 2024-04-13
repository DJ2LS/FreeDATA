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
      year: "2-digit",
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
function pushToPing(origin)
{
   window.dispatchEvent(new CustomEvent("stationSelected", {bubbles:true, detail: origin }));
}
</script>
<template>
  <div class="card h-100">
    <!--325px-->
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
              <th scope="col" id="thFreq">Freq</th>
              <th scope="col" id="thDxcall">DXCall</th>
              <th scope="col" id="thDxgrid">Grid</th>
              <th scope="col" id="thDist">Dist</th>
              <th scope="col" id="thType">Type</th>
              <th scope="col" id="thSnr">SNR</th>
              <!--<th scope="col">Off</th>-->
              <th scope="col" id="thSnr">AFK?</th>

            </tr>
          </thead>
          <tbody id="gridHeardStations">
            <!--https://vuejs.org/guide/essentials/list.html-->
            <tr v-for="item in state.heard_stations" :key="item.origin" @click="pushToPing(item.origin)">
              <td>
                {{ getDateTime(item.timestamp) }}
              </td>
              <td>{{ item.frequency / 1000 }} kHz</td>
              <td>
                {{ item.origin }}
              </td>
              <td>
                {{ item.gridsquare }}
              </td>
              <td>{{ getMaidenheadDistance(item.gridsquare) }} km</td>
              <td>
                {{ item.activity_type }}
              </td>
              <td>
                {{ item.snr }}
              </td>
              <td>
                {{ item.away_from_key }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- END OF HEARD STATIONS TABLE -->
    </div>
  </div>
</template>
