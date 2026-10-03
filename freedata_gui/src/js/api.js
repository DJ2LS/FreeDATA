// Pinia setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import {
  validateCallsignWithSSID,
  validateCallsignWithoutSSID,
} from "./freedata";
import { displayToast, escapeHtml } from "./popupHandler";
import { processFreedataMessages } from "./messagesHandler";
import {
  processFreedataDomains,
  processFreedataBroadcastsPerDomain,
} from "./broadcastsHandler";

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);
import { useChatStore } from "../store/chatStore.js";
const chatStore = useChatStore(pinia);
import { useBroadcastStore } from "../store/broadcastStore.js";
const broadcastStore = useBroadcastStore(pinia);

// Build URL with adjusted port if needed
function buildURL(endpoint) {
  const { protocol, hostname, port } = window.location;
  const adjustedPort = port === "8080" ? "5000" : port;
  return `${protocol}//${hostname}:${adjustedPort}${endpoint}`;
}

// Network traffic indicator, reference-counted so concurrent requests
// keep it set until the last one has finished.
// REST calls are not gated on the WebSocket state: the server may be
// reachable even if a socket is (re)connecting. A failed fetch simply
// returns undefined.
let pendingRequests = 0;
function setNetworkTrafficBusy(isBusy) {
  pendingRequests = Math.max(0, pendingRequests + (isBusy ? 1 : -1));
  state.is_network_traffic = pendingRequests > 0;
}

// Extract a readable error message from a FastAPI error response.
// The server sends {"detail": {"error": "..."}} (api_abort),
// {"detail": "..."} or {"detail": [{"msg": "..."}]} (validation errors).
async function getErrorMessage(response) {
  let message = `${response.status} ${response.statusText}`.trim();
  try {
    const body = await response.json();
    const detail = body?.detail ?? body?.error ?? body;
    if (typeof detail === "string") {
      message = detail;
    } else if (Array.isArray(detail)) {
      message = detail
        .map((item) => item?.msg ?? JSON.stringify(item))
        .join("; ");
    } else if (detail && typeof detail.error === "string") {
      message = detail.error;
    }
  } catch {
    // body is not JSON, keep the status text
  }
  return message;
}

// Show an API error to the user. Identical messages are suppressed for a
// few seconds to avoid toast spam.
const recentErrors = new Map();
const ERROR_TOAST_SUPPRESS_MS = 5000;
function showApiError(method, endpoint, message) {
  const key = `${method} ${endpoint} ${message}`;
  const now = Date.now();
  if (now - (recentErrors.get(key) || 0) < ERROR_TOAST_SUPPRESS_MS) return;
  recentErrors.set(key, now);
  displayToast(
    "danger",
    "bi-exclamation-octagon",
    `<strong>Server error</strong>
     <div class="small text-muted">${escapeHtml(method)} ${escapeHtml(endpoint)}</div>
     <div>${escapeHtml(message)}</div>`,
    8000,
  );
}

// Common request handler. Returns the parsed JSON body, or undefined on any
// error. Errors from requests that change something (POST/PATCH/DELETE)
// are shown as toast; GET requests are mostly background loads and are
// only logged unless `notify` is true.
async function apiRequest(method, endpoint, payload, notify) {
  setNetworkTrafficBusy(true);

  try {
    const options = { method };
    if (payload !== undefined) {
      options.headers = { "Content-Type": "application/json" };
      options.body = JSON.stringify(payload);
    }
    const response = await fetch(buildURL(endpoint), options);
    if (!response.ok) {
      const message = await getErrorMessage(response);
      console.error(`REST ${method} ${endpoint} failed: ${message}`);
      if (notify) showApiError(method, endpoint, message);
      return;
    }
    return await response.json();
  } catch (error) {
    console.error(`REST ${method} ${endpoint} failed:`, error);
    if (notify) {
      showApiError(method, endpoint, error?.message || String(error));
    }
  } finally {
    setNetworkTrafficBusy(false);
  }
}

// Fetch GET request
async function apiGet(endpoint, notify = false) {
  return apiRequest("GET", endpoint, undefined, notify);
}

// Fetch POST request
export async function apiPost(endpoint, payload = {}) {
  return apiRequest("POST", endpoint, payload, true);
}

// Fetch PATCH request
export async function apiPatch(endpoint, payload = {}) {
  return apiRequest("PATCH", endpoint, payload, true);
}

// Fetch DELETE request
export async function apiDelete(endpoint, payload = {}) {
  return apiRequest("DELETE", endpoint, payload, true);
}

// functions using updated apiGet and apiPost
// /version returns api_version, modem_version, os_info and python_info
export async function getVersion() {
  let data = await apiGet("/version");
  return data?.modem_version || "N/A";
}

export async function getSysInfo() {
  let data = await apiGet("/version");
  console.log(data);
  return {
    api_version: data?.api_version || "N/A",
    modem_version: data?.modem_version || "N/A",
    os_info: {
      system: data?.os_info?.system || "N/A",
      node: data?.os_info?.node || "N/A",
      release: data?.os_info?.release || "N/A",
      version: data?.os_info?.version || "N/A",
      machine: data?.os_info?.machine || "N/A",
      processor: data?.os_info?.processor || "N/A",
    },
    python_info: {
      build: data?.python_info?.build || ["N/A", "N/A"],
      compiler: data?.python_info?.compiler || "N/A",
      branch: data?.python_info?.branch || "N/A",
      implementation: data?.python_info?.implementation || "N/A",
      revision: data?.python_info?.revision || "N/A",
      version: data?.python_info?.version || "N/A",
    },
  };
}

export async function getConfig() {
  return await apiGet("/config");
}

export async function setConfig(config) {
  return await apiPost("/config", config);
}

export async function getAudioDevices() {
  return await apiGet("/devices/audio");
}

export async function getSerialDevices() {
  return await apiGet("/devices/serial");
}

export async function setModemBeacon(enabled = false, away_from_key = false) {
  return await apiPost("/modem/beacon", { enabled, away_from_key });
}

export async function sendModemCQ() {
  return await apiPost("/modem/cqcqcq");
}

export async function sendModemPing(dxcall) {
  if (
    validateCallsignWithSSID(dxcall) === false &&
    validateCallsignWithoutSSID(dxcall) === true
  ) {
    dxcall = String(dxcall).toUpperCase().trim() + "-0";
  }
  dxcall = String(dxcall).toUpperCase().trim();
  if (validateCallsignWithSSID(dxcall)) {
    return await apiPost("/modem/ping_ping", { dxcall });
  }
}

/**
 * Send raw data via ARQ.
 * @param {string} dxcall destination callsign (with SSID)
 * @param {string} data base64 encoded payload
 * @param {string} type one of "raw", "raw_lzma", "raw_gzip"
 */
export async function sendModemARQRaw(dxcall, data, type = "raw") {
  return await apiPost("/modem/send_arq_raw", {
    dxcall,
    type,
    data,
  });
}

export async function stopTransmission() {
  return await apiPost("/modem/stop_transmission");
}

export async function sendModemTestFrame() {
  return await apiPost("/modem/send_test_frame");
}

export async function sendSineTone(state) {
  return await apiPost("/radio/tune", { enable_tuning: state });
}

export async function startModem() {
  return await apiPost("/modem/start");
}

export async function stopModem() {
  return await apiPost("/modem/stop");
}

export async function getModemState() {
  return await apiGet("/modem/state");
}

export async function setRadioParametersFrequency(frequency) {
  return await apiPost("/radio", { radio_frequency: frequency });
}

export async function setRadioParametersMode(mode) {
  return await apiPost("/radio", { radio_mode: mode });
}

export async function setRadioParametersRFLevel(rf_level) {
  return await apiPost("/radio", { radio_rf_level: rf_level });
}

export async function setRadioParametersTuner(state) {
  return await apiPost("/radio", { radio_tuner: state });
}

export async function getRadioStatus() {
  return await apiGet("/radio");
}

export async function getFreedataMessages() {
  chatStore.loading = true;
  try {
    const res = await apiGet("/freedata/messages");
    if (res) {
      processFreedataMessages(res);
    }
  } catch (error) {
    console.error("Error fetching messages:", error);
  } finally {
    chatStore.loading = false;
  }
}

export async function getFreedataMessageById(id) {
  let res = await apiGet(`/freedata/messages/${id}`);
  return res;
}

export async function getFreedataAttachmentBySha512(data_sha512) {
  let res = await apiGet(`/freedata/messages/attachment/${data_sha512}`);
  return res;
}

export async function sendFreedataMessage(destination, body, attachments) {
  return await apiPost("/freedata/messages", {
    destination,
    body,
    attachments,
  });
}

export async function postFreedataMessageADIF(id) {
  return await apiPost(`/freedata/messages/${id}/adif`, {
    action: "retransmit",
  });
}

export async function retransmitFreedataMessage(id) {
  return await apiPatch(`/freedata/messages/${id}`, { action: "retransmit" });
}

export async function setFreedataMessageAsRead(id) {
  return await apiPatch(`/freedata/messages/${id}`, { is_read: true });
}

export async function deleteFreedataMessage(id) {
  return await apiDelete(`/freedata/messages/${id}`);
}

export async function getBeaconDataByCallsign(callsign) {
  return await apiGet(`/freedata/beacons/${callsign}`);
}

export async function getStationInfo(callsign) {
  return await apiGet(`/freedata/station/${callsign}`);
}

export async function setStationInfo(callsign, info) {
  return await apiPost(`/freedata/station/${callsign}`, info);
}

export async function getFreedataBroadcasts() {
  broadcastStore.loading = true;
  try {
    const res = await apiGet("/freedata/broadcasts");
    if (Array.isArray(res)) {
      // /freedata/broadcasts returns a flat list; group it by domain like
      // /freedata/broadcasts/{domain}/ does
      const perDomain = {};
      for (const msg of res) {
        const domain = msg.domain || "unknown";
        (perDomain[domain] = perDomain[domain] || []).push(msg);
      }
      processFreedataBroadcastsPerDomain(perDomain);
    }
  } catch (error) {
    console.error("Error fetching broadcasts:", error);
  } finally {
    broadcastStore.loading = false;
  }
}

export async function getFreedataBroadcastsPerDomain(domain) {
  broadcastStore.loading = true;
  try {
    const res = await apiGet(`/freedata/broadcasts/${domain}/`);
    if (res) {
      processFreedataBroadcastsPerDomain(res);
    }
  } catch (error) {
    console.error("Error fetching broadcasts:", error);
  } finally {
    broadcastStore.loading = false;
  }
}

// Marks all broadcasts of a domain as read. GET /freedata/broadcasts/{domain}/
// is side-effect free, so this is called when the user opens a domain.
export async function setFreedataBroadcastDomainAsRead(domain) {
  return await apiPatch(`/freedata/broadcasts/${domain}/read`);
}

export async function getFreedataDomains() {
  broadcastStore.loading = true;
  try {
    const res = await apiGet("/freedata/broadcasts/domains");
    if (res) {
      processFreedataDomains(res);
    }
  } catch (error) {
    console.error("Error fetching broadcasts:", error);
  } finally {
    broadcastStore.loading = false;
  }
}

export async function sendFreedataBroadcastMessage(params) {
  return await apiPost("/freedata/broadcasts", params);
}

export async function retransmitFreedataBroadcast(id) {
  return await apiPatch(`/freedata/broadcasts/${id}`, {
    action: "retransmit",
  });
}

export async function deleteFreedataBroadcastMessage(id) {
  return await apiDelete(`/freedata/broadcasts/${id}`);
}

export async function deleteFreedataBroadcastDomain(id) {
  return await apiDelete(`/freedata/broadcasts/${id}`);
}

