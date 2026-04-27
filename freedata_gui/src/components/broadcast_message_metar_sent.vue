<template>
  <div class="row justify-content-end mb-2 me-1">
    <div class="col-auto p-0 m-0">
      <button
        class="btn btn-outline-secondary border-0 me-1"
        data-bs-target="#broadcastMessageInfoModal"
        data-bs-toggle="modal"
        @click="showBroadcastMessageInfo"
      >
        <i class="bi bi-info-circle" />
      </button>

      <button class="btn btn-outline-secondary border-0 me-1" @click="retransmit">
        <i class="bi bi-arrow-repeat" />
      </button>

      <button class="btn btn-outline-secondary border-0 me-1" @click="deleteMsg">
        <i class="bi bi-trash" />
      </button>

      <button class="btn btn-outline-secondary border-0" @click="sendADIF">
        ADIF
      </button>
    </div>

    <div class="col-8 align-items-end">
      <div class="card">
        <div class="card-body">
          <div class="d-flex gap-3 align-items-start flex-wrap">
            <div v-html="compassSVG"></div>

            <div class="flex-grow-1">
              <div class="d-flex align-items-center gap-2 mb-1">
                <strong class="me-2">{{ stationLabel }}</strong>
                <span class="badge rounded-pill" :class="categoryCss">{{ category }}</span>
                <span class="text-muted small">{{ timeStr }}</span>
              </div>

              <div class="row g-2">
                <div class="col-6 col-md-4">
                  <div class="border rounded p-2">
                    <div class="text-uppercase small text-muted">Wind</div>
                    <div class="fw-semibold text-nowrap">{{ windStr }}</div>
                  </div>
                </div>

                <div class="col-6 col-md-4">
                  <div class="border rounded p-2">
                    <div class="text-uppercase small text-muted">Visibility</div>
                    <div class="fw-semibold text-nowrap">{{ visStr }}</div>
                  </div>
                </div>

                <div class="col-6 col-md-4">
                  <div class="border rounded p-2">
                    <div class="text-uppercase small text-muted">Clouds</div>
                    <div class="fw-semibold text-nowrap">{{ cloudsStr }}</div>
                  </div>
                </div>

                <div class="col-6 col-md-4">
                  <div class="border rounded p-2">
                    <div class="text-uppercase small text-muted">Temp/Dew</div>
                    <div class="fw-semibold text-nowrap">{{ tempDewStr }}</div>
                  </div>
                </div>

                <div class="col-6 col-md-4">
                  <div class="border rounded p-2">
                    <div class="text-uppercase small text-muted">QNH</div>
                    <div class="fw-semibold text-nowrap">{{ qnhStr }}</div>
                  </div>
                </div>
              </div>

              <div class="text-muted small mt-2"><code>{{ parsed.raw }}</code></div>
            </div>
          </div>
        </div>

        <div class="card-footer p-1 border-top-0">
          <p class="text p-0 m-0 mb-1 me-1 text-end">
            <span class="badge text-bg-secondary">{{ message.msg_type }}</span>
            | <span class="badge text-bg-light">{{ timeUTC }} UTC</span>
            | <span class="badge text-bg-light">{{ message.origin }}</span>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  parseMetar,
  determineFlightCategory,
  categoryClass,
  windToString,
  visibilityToString,
  cloudsToString,
  tempDewToString,
  qnhToString,
  timeToString,
  buildCompassSVG,
} from '@/js/metar.js';

import airports from '@/assets/airports.json';

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
import { useBroadcastStore } from '../store/broadcastStore.js';
setActivePinia(pinia);
const broadcast = useBroadcastStore(pinia);

import {
  repeatBroadcastTransmission,
  deleteBroadcastMessageFromDB,
  sendBroadcastADIFviaUDP,
} from '@/js/broadcastsHandler';

// Build iata lookup once
const AIRPORT_BY_IATA = {};
for (const a of airports) {
  if (a?.iata) AIRPORT_BY_IATA[a.iata] = a;
}

export default {
  name: 'BroadcastMessageMetarSent',
  props: { message: Object },

  computed: {
    timeUTC() {
      const d = new Date(this.message.timestamp * 1000);
      return d.toISOString().split('T')[1].split('.')[0];
    },

    parsed() {
      let raw = '';
      const b64 = this.message?.payload_data?.final;
      if (b64) {
        try { raw = atob(b64); } catch { raw = '<decode error>'; }
      }
      console.log(atob(b64))
      return parseMetar((raw || '').trim());
    },

    airportInfo() {
      const iata = this.parsed.iata || null;
      console.log(iata)
      console.log(AIRPORT_BY_IATA[iata])
      if (iata && AIRPORT_BY_IATA[iata]) return AIRPORT_BY_IATA[iata];
      return null;
    },

    stationLabel() {
      if (this.airportInfo) {
        const code = this.parsed.iata || this.airportInfo.iata || '';
        const name = this.airportInfo.name || '';
        return code ? `${code} – ${name}` : name || 'METAR';
      }
      return this.parsed.iata || 'METAR';
    },

    category() { return determineFlightCategory(this.parsed); },
    categoryCss() { return categoryClass(this.category); },

    windStr() { return windToString(this.parsed.wind); },
    visStr() { return visibilityToString(this.parsed.visibility); },
    cloudsStr() { return cloudsToString(this.parsed.clouds); },
    tempDewStr() { return tempDewToString(this.parsed.temp_c, this.parsed.dew_c); },
    qnhStr() { return qnhToString(this.parsed.qnh_hpa); },
    timeStr() { return timeToString(this.parsed.day, this.parsed.hh, this.parsed.mm); },

    compassSVG() {
      return buildCompassSVG(this.parsed.wind, { size: 160 });
    },
  },

  methods: {
    showBroadcastMessageInfo() { broadcast.selectedMessage = this.message; },

    async retransmit() {
      try { await repeatBroadcastTransmission(this.message.id); }
      catch (e) { console.error('Retransmit failed:', e); }
    },

    async deleteMsg() {
      try { await deleteBroadcastMessageFromDB(this.message.id); }
      catch (e) { console.error('Delete failed:', e); }
    },

    sendADIF() { sendBroadcastADIFviaUDP(this.message.id); },
  },
};
</script>

<style scoped>
.text-bg-magenta { color: #fff; background-color: #d63384 !important; } /* LIFR */
</style>
