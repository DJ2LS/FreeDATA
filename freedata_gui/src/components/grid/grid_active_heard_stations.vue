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

const activityIcons = {
  ARQ_SESSION_INFO: 'bi bi-file-earmark-binary',
  ARQ_SESSION_OPEN: 'bi bi-file-earmark-binary',
  ARQ_SESSION_OPEN_ACK: 'bi bi-file-earmark-binary',
  ARQ_BURST: 'bi bi-file-earmark-binary',
  ARQ_BURST_ACK: 'bi bi-file-earmark-binary',
  P2P_CONNECTION_CONNECT: 'bi bi-arrow-left-right',
  P2P_CONNECTION_CONNECT_ACK: 'bi bi-arrow-left-right',
  P2P_CONNECTION_PAYLOAD: 'bi bi-arrow-left-right',
  P2P_CONNECTION_PAYLOAD_ACK: 'bi bi-arrow-left-right',
  P2P_CONNECTION_DISCONNECT: 'bi bi-arrow-left-right',
  P2P_CONNECTION_DISCONNECT_ACK: 'bi bi-arrow-left-right',
  QRV: 'bi bi-person-raised-hand',
  CQ: 'bi bi-megaphone',
  BEACON: 'bi bi-globe',
  PING_ACK: 'bi bi-check-square'
};

function getActivityInfo(activityType) {
  if (!activityType) {
    return { iconClass: 'bi bi-question-circle', description: 'Unknown activity' };
  }

  return {
    iconClass: activityIcons[activityType] || 'bi bi-question-circle',
    description: activityType
  };
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
      <i
        class="bi bi-list-columns-reverse"
        style="font-size: 1.2rem"
      />&nbsp;
      <strong>{{ $t('grid.components.heardstations') }}</strong>
    </div>

    <div class="card-body overflow-auto p-0">
      <div class="table-responsive">
        <!-- START OF TABLE FOR HEARD STATIONS -->
        <table
          id="tblHeardStationList"
          class="table table-sm table-striped"
        >
          <thead>
            <tr>
              <th
                id="thTime"
                scope="col"
              >
                {{ $t('grid.components.time') }}
              </th>
              <th
                id="thFreq"
                scope="col"
              >
                {{ $t('grid.components.freq') }}
              </th>
              <th
                id="thDxcall"
                scope="col"
              >
                {{ $t('grid.components.dxcall') }}
              </th>
              <th
                id="thDxgrid"
                scope="col"
              >
                {{ $t('grid.components.grid') }}
              </th>
              <th
                id="thDist"
                scope="col"
              >
                {{ $t('grid.components.dist') }}
              </th>
              <th
                id="thType"
                scope="col"
              >
                {{ $t('grid.components.type') }}
              </th>
              <th
                id="thSnr"
                scope="col"
              >
                {{ $t('grid.components.snr') }}
              </th>
              <th
                id="thSnr"
                scope="col"
              >
                {{ $t('grid.components.afk') }}
              </th>
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
                  disabled
                  @click="getStationInfoByCallsign(item.origin)"
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
                  <i class="bi bi-pencil-square" />
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
                  <i class="bi bi-arrow-left-right" />
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
                />
              </td>
              <td>
                <small>{{ item.snr }}</small>
              </td>
              <td>
                <i
                  v-if="item.away_from_key"
                  class="bi bi-house-x"
                />
                <i
                  v-else
                  class="bi bi-house-check-fill"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- END OF HEARD STATIONS TABLE -->
    </div>
  </div>
</template>
