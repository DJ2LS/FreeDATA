import { settingsStore as settings } from "../store/settingsStore.js";
import {
  validateCallsignWithSSID,
  validateCallsignWithoutSSID,
} from "./freedata";

import { processFreedataMessages } from "./messagesHandler";

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
    return await response.json();
  } catch (error) {
    //console.error("Error getting from REST:", error);
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

export async function apiDelete(endpoint, payload = {}) {
  try {
    const response = await fetch(buildURL(settings.local, endpoint), {
      method: "DELETE",
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
    console.error("Error deleting from REST:", error);
  }
}

export async function getVersion() {
  let data = await apiGet("/version").then((res) => {
    return res;
  });

  if (typeof data !== "undefined" && typeof data.version !== "undefined") {
    return data.version;
  }
  return 0;
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
  return await apiPost("/modem/beacon", {
    enabled: enabled,
    away_from_key: away_from_key,
  });
}

export async function sendModemCQ() {
  return await apiPost("/modem/cqcqcq");
}

export async function sendModemPing(dxcall) {
  if (
    validateCallsignWithSSID(dxcall) === false &&
    validateCallsignWithoutSSID(dxcall) === true
  ) {
    dxcall = String(dxcall).toUpperCase().trim();
    dxcall = dxcall + "-0";
  }
  dxcall = String(dxcall).toUpperCase().trim();
  if (validateCallsignWithSSID(dxcall))
    return await apiPost("/modem/ping_ping", { dxcall: dxcall });
}

export async function sendModemARQRaw(mycall, dxcall, data, uuid) {
  return await apiPost("/modem/send_arq_raw", {
    mycallsign: mycall,
    dxcall: dxcall,
    data: data,
    uuid: uuid,
  });
}

export async function stopTransmission() {
  return await apiPost("/modem/stop_transmission");
}

export async function sendModemTestFrame() {
  return await apiPost("/modem/send_test_frame");
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
  return await apiPost("/radio", {
    radio_frequency: frequency,
  });
}
export async function setRadioParametersMode(mode) {
  return await apiPost("/radio", {
    radio_mode: mode,
  });
}
export async function setRadioParametersRFLevel(rf_level) {
  return await apiPost("/radio", {
    radio_rf_level: rf_level,
  });
}

export async function setRadioParametersTuner(state) {
  return await apiPost("/radio", {
    radio_tuner: state,
  });
}

export async function getRadioStatus() {
  return await apiGet("/radio");
}

export async function getFreedataMessages() {
  let res = await apiGet("/freedata/messages");
  processFreedataMessages(res);
}

export async function getFreedataAttachmentBySha512(data_sha512) {
  let res = await apiGet(`/freedata/messages/attachment/${data_sha512}`);
  return res;
}

export async function sendFreedataMessage(destination, body, attachments) {
  return await apiPost("/freedata/messages", {
    destination: destination,
    body: body,
    attachments: attachments,
  });
}

export async function retransmitFreedataMessage(id) {
  return await apiPost(`/freedata/messages/${id}`);
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
