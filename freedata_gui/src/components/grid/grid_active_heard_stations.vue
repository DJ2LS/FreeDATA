<script setup>
// @ts-nocheck
const { distance } = require("qth-locator");

import { setActivePinia } from 'pinia';
import pinia from '../../store/index';
setActivePinia(pinia);

import { settingsStore as settings } from '../../store/settingsStore.js';
import { useStateStore } from '../../store/stateStore.js';
import { useChatStore } from '../../store/chatStore.js';
import { getStationInfoByCallsign } from './../../js/stationHandler';
import { sendModemPing } from '../../js/api.js';

const state = useStateStore(pinia);
const chat = useChatStore(pinia);

function getDateTime(timestampRaw) {
  var datetime = new Date(timestampRaw * 1000).toLocaleString(
    navigator.language,
    {
      hourCycle: 'h23',
      year: '2-digit',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }
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
    new CustomEvent('stationSelected', { bubbles: true, detail: origin })
  );
}

function getActivityInfo(activityType) {
  switch (activityType) {
    case 'ARQ_SESSION_INFO':
      return { iconClass: 'bi bi-info-circle', description: activityType };
    case 'ARQ_SESSION_OPEN':
    case 'ARQ_SESSION_OPEN_ACK':
      return { iconClass: 'bi bi-link', description: activityType };
    case 'QRV':
      return { iconClass: 'bi bi-person-raised-hand', description: activityType };
    case 'CQ':
      return { iconClass: 'bi bi-megaphone', description: activityType };
    case 'BEACON':
      return { iconClass: 'bi bi-globe', description: activityType };
    case 'PING_ACK':
      return { iconClass: 'bi bi-check-square', description: activityType };
    default:
      return { iconClass: '', description: activityType };
  }
}

function startNewChat(callsign) {
  chat.newChatCallsign = callsign;
  chat.newChatMessage = 'Hi there! Nice to meet you!';
}

function transmitPing(callsign) {
  sendModemPing(callsign.toUpperCase());
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
              <th scope="col" id="thSnr">AFK?</th>
            </tr>
          </thead>
          <tbody id="gridHeardStations">
            <!--https://vuejs.org/guide/essentials/list.html-->
            <tr
              v-for="item in state.heard_stations"
              :key="item.origin"
              @click="pushToPing(item.origin)"
            >
              <td>
                {{ getDateTime(item.timestamp) }}
              </td>
              <td>{{ item.frequency / 1000 }} kHz</td>
              <td>
                <button
                  class="btn btn-sm btn-outline-secondary ms-2 border-0"
                  data-bs-target="#dxStationInfoModal"
                  data-bs-toggle="modal"
                  @click="getStationInfoByCallsign(item.origin)"
                  disabled
                >
                  <h6 class="p-0 m-0">{{ item.origin }}</h6>
                </button>

                <button
                  class="btn btn-sm border-0 btn-outline-primary"
                  data-bs-target="#newChatModal"
                  data-bs-toggle="modal"
                  type="button"
                  data-bs-trigger="hover"
                  data-bs-title="Start new chat"
                  @click="startNewChat(item.origin)"
                >
                  <i class="bi bi-pencil-square"></i>
                </button>

                <button
                  class="btn btn-sm border-0 btn-outline-primary"
                  data-bs-placement="top"
                  type="button"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-title="Transmit ping"
                  @click="transmitPing(item.origin)"
                >
                  <i class="bi bi-arrow-left-right"></i>
                </button>
              </td>
              <td>
                {{ item.gridsquare }}
              </td>
              <td>{{ getMaidenheadDistance(item.gridsquare) }} km</td>
              <td>
                <i
                  :class="getActivityInfo(item.activity_type).iconClass"
                  data-bs-toggle="tooltip"
                  :title="getActivityInfo(item.activity_type).description"
                ></i>
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
