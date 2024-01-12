import { settingsStore as settings } from "../store/settingsStore.js";
import {
  validateCallsignWithSSID,
  validateCallsignWithoutSSID,
} from "./freedata";

function buildURL(params, endpoint) {
  const url = "http://" + params.host + ":" + params.port + endpoint;
  return url;
}

async function apiGet(endpoint) {
  try {
    const response = await fetch(buildURL(settings.local, endpoint));
    if (!response.ok) {
      throw new Error(`REST response not ok: ${response.statusText}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error getting from REST:", error);
  }
}

export async function apiPost(endpoint, payload = {}) {
  try {
    const response = await fetch(buildURL(settings.local, endpoint), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`REST response not ok: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error posting to REST:", error);
  }
}

export async function getVersion() {
  let data = await apiGet("/version").then((res) => {
    return res;
  });
  return data.version;
  //return data["version"];
}

export async function getConfig() {
  return apiGet("/config");
}

export function setConfig(config) {
  return apiPost("/config", config);
}

export function getAudioDevices() {
  return apiGet("/devices/audio");
}

export function getSerialDevices() {
  return apiGet("/devices/serial");
}

export function setModemBeacon(enabled = false) {
  return apiPost("/modem/beacon", { enabled: enabled });
}

export function sendModemCQ() {
  return apiPost("/modem/cqcqcq");
}

export function sendModemPing(dxcall) {
  if (
    validateCallsignWithSSID(dxcall) === false &&
    validateCallsignWithoutSSID(dxcall) === true
  ) {
    dxcall = String(dxcall).toUpperCase().trim();
    dxcall = dxcall + "-0";
  }
  dxcall = String(dxcall).toUpperCase().trim();
  if (validateCallsignWithSSID(dxcall))
    return apiPost("/modem/ping_ping", { dxcall: dxcall });
}

export function sendModemARQRaw(mycall, dxcall, data, uuid) {
  return apiPost("/modem/send_arq_raw", {
    mycallsign: mycall,
    dxcall: dxcall,
    data: data,
    uuid: uuid,
  });
}

export function stopTransmission() {
  return apiPost("/modem/stop_transmission");
}

export function sendModemTestFrame() {
  return apiPost("/modem/send_test_frame");
}

export function startModem() {
  return apiPost("/modem/start");
}

export function stopModem() {
  return apiPost("/modem/stop");
}

export function getModemState() {
  return apiGet("/modem/state");
}

export function setRadioParameters(frequency, mode, rf_level){
  return apiPost("/radio", {
    radio_frequency: frequency,
    radio_mode: mode,
  });
}
export function getRadioStatus() {
  return apiGet("/radio");
}