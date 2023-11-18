import { settingsStore as settings } from "../store/settingsStore.js";

function buildURL(endpoint) {
  const url =
    "http://" + settings.local.host + ":" + settings.local.port + endpoint;
  return url;
}

async function apiGet(endpoint) {
  const response = await fetch(buildURL(endpoint));
  if (!response.ok) {
    throw new Error(`REST response not ok: ${response.statusText}`);
  }
  const data = await response.json();
  return data;
}

export async function apiPost(endpoint, payload = {}) {
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

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error posting to REST:", error);
  }
}

export function getVersion() {
  return apiGet("/version");
}

export function getConfig() {
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
  return apiPost("/modem/ping", { dxcall: dxcall });
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
