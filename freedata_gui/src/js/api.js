// Pinia setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
import { computed } from "vue";

import {
  validateCallsignWithSSID,
  validateCallsignWithoutSSID,
} from "./freedata";
import { processFreedataMessages } from "./messagesHandler";
import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

// Build URL with adjusted port if needed
function buildURL(endpoint) {
  const { protocol, hostname, port } = window.location;
  const adjustedPort = port === "8080" ? "5000" : port;
  return `${protocol}//${hostname}:${adjustedPort}${endpoint}`;
}

// Check network connectivity
const isNetworkConnected = computed(
  () => state.modem_connection !== "disconnected",
);
function checkNetworkConnectivity() {
  if (!isNetworkConnected.value) {
    console.warn("Network is disconnected. API call aborted.");
    return false;
  }
  return true;
}
// Set network traffic state
function setNetworkTrafficBusy(isBusy) {
  state.is_network_traffic = isBusy;
}

// Fetch GET request
async function apiGet(endpoint) {
  if (!checkNetworkConnectivity()) return;

  setNetworkTrafficBusy(true); // Set the network busy state to true

  try {
    const response = await fetch(buildURL(endpoint));
    if (!response.ok) {
      throw new Error(`REST response not ok: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error getting from REST:", error);
  } finally {
    setNetworkTrafficBusy(false); // Set the network busy state back to false
  }
}

// Fetch POST request
export async function apiPost(endpoint, payload = {}) {
  if (!checkNetworkConnectivity()) return;

  setNetworkTrafficBusy(true); // Set the network busy state to true

  try {
    const response = await fetch(buildURL(endpoint), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`REST response not ok: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error posting to REST:", error);
  } finally {
    setNetworkTrafficBusy(false); // Set the network busy state back to false
  }
}

// Fetch PATCH request
export async function apiPatch(endpoint, payload = {}) {
  if (!checkNetworkConnectivity()) return;

  setNetworkTrafficBusy(true); // Set the network busy state to true

  try {
    const response = await fetch(buildURL(endpoint), {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`REST response not ok: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error patching to REST:", error);
  } finally {
    setNetworkTrafficBusy(false); // Set the network busy state back to false
  }
}

// Fetch DELETE request
export async function apiDelete(endpoint, payload = {}) {
  if (!checkNetworkConnectivity()) return;

  setNetworkTrafficBusy(true); // Set the network busy state to true

  try {
    const response = await fetch(buildURL(endpoint), {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`REST response not ok: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error deleting from REST:", error);
  } finally {
    setNetworkTrafficBusy(false); // Set the network busy state back to false
  }
}

// functions using updated apiGet and apiPost
export async function getVersion() {
  let data = await apiGet("/version");
  if (data && data.version) {
    return data.version;
  }
  return 0;
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

export async function sendModemARQRaw(mycall, dxcall, data, uuid) {
  return await apiPost("/modem/send_arq_raw", {
    mycallsign: mycall,
    dxcall,
    data,
    uuid,
  });
}

export async function stopTransmission() {
  return await apiPost("/modem/stop_transmission");
}

export async function sendModemTestFrame() {
  return await apiPost("/modem/send_test_frame");
}

export async function sendSineTone(state) {
  return await apiPost("/radio/tune", {enable_tuning: state});
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
  let res = await apiGet("/freedata/messages");
  if (res) processFreedataMessages(res);
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
