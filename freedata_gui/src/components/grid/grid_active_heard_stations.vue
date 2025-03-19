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
    case 'ARQ_SESSION_OPEN':
    case 'ARQ_SESSION_OPEN_ACK':
    case 'ARQ_BURST':
    case 'ARQ_BURST_ACK':
      return { iconClass: 'bi bi-file-earmark-binary', description: activityType };
    case 'P2P_CONNECTION_CONNECT':
    case 'P2P_CONNECTION_CONNECT_ACK':
    case 'P2P_CONNECTION_PAYLOAD':
    case 'P2P_CONNECTION_PAYLOAD_ACK':
    case 'P2P_CONNECTION_DISCONNECT':
    case 'P2P_CONNECTION_DISCONNECT_ACK':

      return { iconClass: 'bi bi-arrow-left-right', description: activityType };
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
    <div class="card-header">
      <i class="bi bi-list-columns-reverse" style="font-size: 1.2rem"></i>&nbsp;
      <strong>{{ $t('grid.components.heardstations') }}</strong>
    </div>

    <div class="card-body overflow-auto p-0">
      <div class="table-responsive">
        <!-- START OF TABLE FOR HEARD STATIONS -->
        <table class="table table-sm table-striped" id="tblHeardStationList">
          <thead>
            <tr>
              <th scope="col" id="thTime">{{ $t('grid.components.time') }}</th>
              <th scope="col" id="thFreq">{{ $t('grid.components.freq') }}</th>
              <th scope="col" id="thDxcall">{{ $t('grid.components.dxcall') }}</th>
              <th scope="col" id="thDxgrid">{{ $t('grid.components.grid') }}</th>
              <th scope="col" id="thDist">{{ $t('grid.components.dist') }}</th>
              <th scope="col" id="thType">{{ $t('grid.components.type') }}</th>
              <th scope="col" id="thSnr">{{ $t('grid.components.snr') }}</th>
              <th scope="col" id="thSnr">{{ $t('grid.components.afk') }}</th>
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
                                  <span class="badge text-bg-secondary">{{ getDateTime(item.timestamp) }}</span>

              </td>
              <td><small>{{ item.frequency / 1000 }} kHz</small></td>
              <td>
                <button
                  class="btn btn-sm btn-outline-secondary ms-2 border-0"
                  data-bs-target="#dxStationInfoModal"
                  data-bs-toggle="modal"
                  @click="getStationInfoByCallsign(item.origin)"
                  disabled
                >
                  <span class="badge text-bg-primary">{{ item.origin }}</span>
                </button>

                <button
                  class="btn btn-sm border-0 btn-outline-primary"
                  data-bs-target="#newChatModal"
                  data-bs-toggle="modal"
                  type="button"
                  data-bs-trigger="hover"
                  :title="$t('grid.components.newmessage_help')"
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
                  :data-bs-title="$t('grid.components.ping_help')"
                  @click="transmitPing(item.origin)"
                >
                  <i class="bi bi-arrow-left-right"></i>
                </button>
              </td>
              <td>
                <small>{{ item.gridsquare }}</small>
              </td>
              <td><small>{{ getMaidenheadDistance(item.gridsquare) }} km</small></td>
              <td>
                <i
                  :class="getActivityInfo(item.activity_type).iconClass"
                  data-bs-toggle="tooltip"
                  :title="getActivityInfo(item.activity_type).description"
                ></i>
              </td>
              <td>
                <small>{{ item.snr }}</small>
              </td>
              <td>
                <i v-if="item.away_from_key" class="bi bi-house-x"></i>
                <i v-else class="bi bi-house-check-fill"></i>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- END OF HEARD STATIONS TABLE -->
    </div>
  </div>
</template>
