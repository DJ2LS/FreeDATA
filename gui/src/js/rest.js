// ----------------- init pinia stores -------------
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import { processModemConfig } from "../js/settingsHandler.ts";

export function fetchSettings() {
  // fetch Settings
  getFromServer("localhost", 5000, "config");
}

async function getFromServer(host, port, endpoint) {
  // our central function for fetching the modems REST API by a specific endpoint
  // TODO make this function using the host and port, specified in settings
  // include better error handling

  const url = "http://" + host + ":" + port + "/" + endpoint;
  const response = await fetch(url);
  const data = await response.json();

  // move received data to our data dispatcher
  restDataDispatcher(endpoint, data.data);
}

function restDataDispatcher(endpoint, data) {
  // dispatch received data by endpoint

  switch (endpoint) {
    case "config":
      processModemConfig(data);
      break;

    default:
      console.log("Wrong endpoint:" + endpoint);
  }
}
