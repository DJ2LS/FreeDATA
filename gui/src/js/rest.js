// ----------------- init pinia stores -------------
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
import {
  processModemConfig,
  processModemAudioDevices,
  processModemSerialDevices,
  getModemConfigAsJSON,
} from "../js/settingsHandler.ts";

export async function getFromServer(host, port, endpoint) {
  // our central function for fetching the modems REST API by a specific endpoint
  // TODO make this function using the host and port, specified in settings

  const url = `http://${host}:${port}/${endpoint}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`REST response not ok: ${response.statusText}`);
  }
  const data = await response.json();

  // move received data to our data dispatcher
  restDataDispatcher(endpoint, data);
}

export async function postToServer(host, port, endpoint, data) {
  // our central function for posting to the modems REST API by a specific endpoint
  // TODO make this function using the host and port, specified in settings

  const url = `http://${host}:${port}/${endpoint}`;
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`REST response not ok: ${response.statusText}`);
    }
  } catch (error) {
    console.error("Error posting to REST:", error);
  }
}

function restDataDispatcher(endpoint, data) {
  // dispatch received data by endpoint

  switch (endpoint) {
    case "config":
      processModemConfig(data);
      break;
    case "devices/audio":
      processModemAudioDevices(data);
      break;
    case "devices/serial":
      processModemSerialDevices(data);
      break;

    default:
      console.log("Wrong endpoint:" + endpoint);
  }
}
