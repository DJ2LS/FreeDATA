<script setup>
/**
 * Broadcast modal – MESSAGE and METAR composer
 * - MESSAGE: simple Markdown text input (sanitized -> HTML -> base64)
 * - METAR: guided form that assembles a valid raw METAR string -> base64
 * Emits nothing; writes via existing broadcast API (newBroadcastMessage),
 * refreshes domains and selects target domain (as your previous flow).
 */

import { reactive, ref, watch, computed } from "vue";
import { setActivePinia } from "pinia";
import pinia from "../store/index";
import { useBroadcastStore } from "../store/broadcastStore.js";
import { settingsStore as settings } from "../store/settingsStore.js";
import { getFreedataBroadcastsPerDomain, getFreedataDomains } from "../js/api";
import { newBroadcastMessage } from "../js/broadcastsHandler";
import airports from "@/assets/airports.json";
import DOMPurify from "dompurify";
import { marked } from "marked";

// Pinia stores
setActivePinia(pinia);
const broadcast = useBroadcastStore(pinia);

// -------- Helpers --------
function pad2(n) { return String(n).padStart(2, "0"); }
function utcNowParts() {
  const d = new Date();
  return { dd: pad2(d.getUTCDate()), HH: pad2(d.getUTCHours()), mm: pad2(d.getUTCMinutes()) };
}

// Build iata datalist from airports.json
const IATA_LIST = computed(() => {
  const set = new Set();
  for (const a of airports) if (a?.iata) set.add(a.iata);
  return Array.from(set).sort();
});

// Default type
if (!broadcast.newMessageType) broadcast.newMessageType = "MESSAGE";

// -------- METAR form state --------
const now = utcNowParts();
const metar = reactive({
  iata: "",
  auto: false,
  corr: false,
  dd: now.dd,
  HH: now.HH,
  mm: now.mm,

  wind_vrb: false,
  wind_dir: "",      // 000..360
  wind_spd: "",      // kt
  wind_gust: "",     // kt optional
  wind_var_from: "", // 3-digit optional
  wind_var_to: "",   // 3-digit optional

  cavok: false,
  visibility: "9999",

  clouds: [
    { cover: "FEW", base_hundreds: "030", type: "" },
  ],

  temp: "15",
  dew: "10",
  qnh: "1015",       // hPa
  remarks: ""        // optional
});

watch(() => metar.wind_vrb, (v) => { if (v) metar.wind_dir = ""; });

function normHundreds(v) {
  if (typeof v !== "string") v = String(v ?? "");
  v = v.replace(/\D/g, "").slice(0, 3);
  return v.padStart(3, "0");
}

function fmtTemp(t) {
  const n = parseInt(t, 10);
  if (isNaN(n)) return "MM";
  return n < 0 ? `M${String(Math.abs(n)).padStart(2, "0")}` : String(n).padStart(2, "0");
}

const metarString = computed(() => {
  const parts = ["METAR"];

  const iata = (metar.iata || "").toUpperCase().trim();
  if (iata) parts.push(iata);

  const dd = pad2(parseInt(metar.dd || "01", 10));
  const HH = pad2(parseInt(metar.HH || "00", 10));
  const mm = pad2(parseInt(metar.mm || "00", 10));
  parts.push(`${dd}${HH}${mm}Z`);

  if (metar.auto) parts.push("AUTO");
  if (metar.corr) parts.push("COR");

  const spd = metar.wind_spd ? String(parseInt(metar.wind_spd, 10)).padStart(2, "0") : "00";
  const dir = metar.wind_vrb ? "VRB" : (metar.wind_dir ? String(parseInt(metar.wind_dir, 10)).padStart(3, "0") : "000");
  let wind = `${dir}${spd}`;
  if (metar.wind_gust) {
    const g = String(parseInt(metar.wind_gust, 10)).padStart(2, "0");
    wind += `G${g}`;
  }
  wind += "KT";
  parts.push(wind);

  if (!metar.wind_vrb && metar.wind_var_from && metar.wind_var_to) {
    const vf = String(parseInt(metar.wind_var_from, 10)).padStart(3, "0");
    const vt = String(parseInt(metar.wind_var_to, 10)).padStart(3, "0");
    parts.push(`${vf}V${vt}`);
  }

  if (metar.cavok) {
    parts.push("CAVOK");
  } else {
    const vis = metar.visibility ? String(parseInt(metar.visibility, 10)).padStart(4, "0") : "9999";
    parts.push(vis);
  }

  if (!metar.cavok) {
    const cloudTokens = metar.clouds
      .filter(c => c.cover && c.base_hundreds)
      .map(c => `${c.cover.toUpperCase()}${normHundreds(c.base_hundreds)}${(c.type || "").toUpperCase()}`);
    if (cloudTokens.length) parts.push(...cloudTokens);
  }

  const T = fmtTemp(metar.temp);
  const D = fmtTemp(metar.dew);
  parts.push(`${T}/${D}`);

  const q = parseInt(metar.qnh, 10);
  if (!isNaN(q)) parts.push(`Q${String(q).padStart(4, "0")}`);

  if (metar.remarks && metar.remarks.trim().length) {
    parts.push(metar.remarks.trim());
  }

  return (parts.join(" ") + "=").replace(/\s+/g, " ").trim();
});

function addCloudLayer() {
  metar.clouds.push({ cover: "SCT", base_hundreds: "040", type: "" });
}
function removeCloudLayer(idx) {
  if (metar.clouds.length > 1) metar.clouds.splice(idx, 1);
}
function nowUTCToForm() {
  const p = utcNowParts();
  metar.dd = p.dd; metar.HH = p.HH; metar.mm = p.mm;
}

// -------- SEND --------
function newBroadcast() {
  const domain = broadcast.newDomain && broadcast.newDomain.trim()
    ? broadcast.newDomain.trim()
    : "GLOBAL-1";
  const type = broadcast.newMessageType && broadcast.newMessageType.trim()
    ? broadcast.newMessageType.trim().toUpperCase()
    : "MESSAGE";

  let base64data = "";

  if (type === "METAR") {
    const raw = metarString.value;        // raw METAR
    base64data = btoa(raw);
  } else {
    broadcast.inputText = (broadcast.inputText || "").trim();
    if (!broadcast.inputText.length) return;
    const sanitizedInput = DOMPurify.sanitize(marked.parse(broadcast.inputText));
    base64data = btoa(sanitizedInput);
  }

  const params = {
    origin: settings.remote.STATION.mycall + '-' + settings.remote.STATION.myssid,
    domain,
    gridsquare: settings.remote.STATION.mygrid,
    type,
    priority: 1,
    data: base64data
  };

  newBroadcastMessage(params);

  setTimeout(() => {
    getFreedataDomains();
    getFreedataBroadcastsPerDomain(domain);
    broadcast.selectedDomain = domain;
    broadcast.newDomain = "";
  }, 1000);

  if (type === "MESSAGE") {
    broadcast.inputText = "";
  }
}
</script>

<template>
  <!-- Broadcast Modal ONLY -->
  <div
    id="newBroadcastModal"
    ref="newBroadcastModalElement"
    class="modal fade"
    tabindex="-1"
    aria-hidden="true"
  >
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">
            {{ $t('modals.startnewbroadcast') }}
          </h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"/>
        </div>

        <div class="modal-body">
          <!-- Domain & Type -->
          <div class="row g-3">
            <div class="col-md-6">
              <label for="domainInput" class="form-label">Domain</label>
              <input
                id="domainInput"
                list="domainOptions"
                class="form-control"
                v-model="broadcast.newDomain"
                placeholder="Enter or select a domain"
              />
              <datalist id="domainOptions">
                <option value="EUROPE-1">EUROPE-1</option>
                <option value="ASIA-1">ASIA-1</option>
                <option value="NA-1">NA-1</option>
                <option value="SA-1">SA-1</option>
                <option value="AFRICA-1">AFRICA-1</option>
              </datalist>
            </div>

            <div class="col-md-6">
              <label for="typeSelect" class="form-label">Type</label>
              <select
                id="typeSelect"
                class="form-select"
                v-model="broadcast.newMessageType"
              >
                <option value="MESSAGE">MESSAGE</option>
                <option value="METAR">METAR</option>
              </select>
            </div>
          </div>

          <!-- MESSAGE composer -->
          <div v-if="(broadcast.newMessageType || 'MESSAGE') === 'MESSAGE'" class="mt-3">
            <label for="messageTextarea" class="form-label">Message</label>
            <textarea
              id="messageTextarea"
              class="form-control"
              rows="6"
              v-model="broadcast.inputText"
              placeholder="Enter your message..."
            />
            <div class="form-text">
              Markdown supported. Will be sanitized before sending.
            </div>
          </div>

          <!-- METAR composer -->
          <div v-else class="mt-3">
            <div class="row g-3">
              <div class="col-md-4">
                <label class="form-label">iata</label>
                <input
                  class="form-control text-uppercase"
                  list="iataOptions"
                  v-model="metar.iata"
                  maxlength="4"
                  placeholder="EFHK"
                  style="text-transform: uppercase"
                />
                <datalist id="iataOptions">
                  <option v-for="code in IATA_LIST" :key="code" :value="code">{{ code }}</option>
                </datalist>
              </div>

              <div class="col-md-5">
                <label class="form-label">Time (UTC)</label>
                <div class="input-group">
                  <input class="form-control" v-model="metar.dd" maxlength="2" placeholder="DD">
                  <span class="input-group-text">/</span>
                  <input class="form-control" v-model="metar.HH" maxlength="2" placeholder="HH">
                  <span class="input-group-text">:</span>
                  <input class="form-control" v-model="metar.mm" maxlength="2" placeholder="mm">
                  <span class="input-group-text">Z</span>
                  <button class="btn btn-outline-secondary" type="button" @click="nowUTCToForm">now</button>
                </div>
                <div class="form-text">Day / Hour : Minute (UTC)</div>
              </div>

              <div class="col-md-3 d-flex align-items-end gap-2">
                <div class="form-check form-switch">
                  <input class="form-check-input" type="checkbox" id="autoSwitch" v-model="metar.auto">
                  <label class="form-check-label" for="autoSwitch">AUTO</label>
                </div>
                <div class="form-check form-switch ms-3">
                  <input class="form-check-input" type="checkbox" id="corrSwitch" v-model="metar.corr">
                  <label class="form-check-label" for="corrSwitch">COR</label>
                </div>
              </div>
            </div>

            <!-- Wind -->
            <div class="row g-3 mt-2">
              <div class="col-md-2 d-flex align-items-end">
                <div class="form-check form-switch">
                  <input class="form-check-input" type="checkbox" id="vrbSwitch" v-model="metar.wind_vrb">
                  <label class="form-check-label" for="vrbSwitch">VRB</label>
                </div>
              </div>

              <div class="col-md-3">
                <label class="form-label">Direction (°)</label>
                <input class="form-control" :disabled="metar.wind_vrb" v-model="metar.wind_dir" placeholder="150">
              </div>

              <div class="col-md-3">
                <label class="form-label">Speed (kt)</label>
                <input class="form-control" v-model="metar.wind_spd" placeholder="06">
              </div>

              <div class="col-md-2">
                <label class="form-label">Gust (kt)</label>
                <input class="form-control" v-model="metar.wind_gust" placeholder="12">
              </div>

              <div class="col-md-1">
                <label class="form-label">Var From</label>
                <input class="form-control" :disabled="metar.wind_vrb" v-model="metar.wind_var_from" placeholder="140">
              </div>

              <div class="col-md-1">
                <label class="form-label">Var To</label>
                <input class="form-control" :disabled="metar.wind_vrb" v-model="metar.wind_var_to" placeholder="200">
              </div>
            </div>

            <!-- Visibility / CAVOK -->
            <div class="row g-3 mt-2">
              <div class="col-md-3">
                <label class="form-label">Visibility (m)</label>
                <input class="form-control" :disabled="metar.cavok" v-model="metar.visibility" placeholder="9999">
              </div>
              <div class="col-md-2 d-flex align-items-end">
                <div class="form-check form-switch">
                  <input class="form-check-input" type="checkbox" id="cavokSwitch" v-model="metar.cavok">
                  <label class="form-check-label" for="cavokSwitch">CAVOK</label>
                </div>
              </div>
            </div>

            <!-- Clouds -->
            <div class="mt-2">
              <div class="d-flex justify-content-between align-items-center">
                <label class="form-label m-0">Clouds</label>
                <div>
                  <button class="btn btn-sm btn-outline-primary me-1" type="button" @click="addCloudLayer" :disabled="metar.cavok">+ Layer</button>
                </div>
              </div>

              <div class="row g-2" v-for="(c, idx) in metar.clouds" :key="idx">
                <div class="col-md-3">
                  <select class="form-select" v-model="c.cover" :disabled="metar.cavok">
                    <option value="FEW">FEW</option>
                    <option value="SCT">SCT</option>
                    <option value="BKN">BKN</option>
                    <option value="OVC">OVC</option>
                  </select>
                </div>
                <div class="col-md-3">
                  <input class="form-control" v-model="c.base_hundreds" :disabled="metar.cavok" placeholder="030 (→ 3000 ft)">
                </div>
                <div class="col-md-3">
                  <select class="form-select" v-model="c.type" :disabled="metar.cavok">
                    <option value="">—</option>
                    <option value="CB">CB</option>
                    <option value="TCU">TCU</option>
                  </select>
                </div>
                <div class="col-md-3">
                  <button class="btn btn-outline-danger" type="button" :disabled="metar.cavok || metar.clouds.length===1" @click="removeCloudLayer(idx)">Remove</button>
                </div>
              </div>
            </div>

            <!-- Temp/Dew/QNH -->
            <div class="row g-3 mt-2">
              <div class="col-md-3">
                <label class="form-label">Temp (°C)</label>
                <input class="form-control" v-model="metar.temp" placeholder="16">
              </div>
              <div class="col-md-3">
                <label class="form-label">Dew (°C)</label>
                <input class="form-control" v-model="metar.dew" placeholder="14">
              </div>
              <div class="col-md-3">
                <label class="form-label">QNH (hPa)</label>
                <input class="form-control" v-model="metar.qnh" placeholder="1015">
              </div>
              <div class="col-md-3">
                <label class="form-label">Remarks (optional)</label>
                <input class="form-control" v-model="metar.remarks" placeholder="RMK ...">
              </div>
            </div>

            <!-- Preview -->
            <div class="mt-3">
              <label class="form-label">Preview</label>
              <pre class="form-control" style="height:auto; min-height: 60px; white-space: pre-wrap;">{{ metarString }}</pre>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            {{ $t('modals.close') }}
          </button>
          <button
            type="button"
            class="btn btn-primary"
            data-bs-dismiss="modal"
            data-bs-trigger="hover"
            @click="newBroadcast"
          >
            Send Broadcast
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
