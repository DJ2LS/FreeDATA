import { getModemConfigAsJSON } from "./settingsHandler.ts";
import { getFromServer, postToServer } from "./rest.js";

export function getModemConfig() {
  // fetch Settings
  getFromServer("localhost", 5000, "config");
  getFromServer("localhost", 5000, "devices/audio");
  getFromServer("localhost", 5000, "devices/serial");
}

export function saveModemConfig() {
  postToServer("localhost", 5000, "config", getModemConfigAsJSON());
}

export function startModem() {
  postToServer("localhost", 5000, "modem/start", null);
}

export function stopModem() {
  postToServer("localhost", 5000, "modem/stop", null);
}

export function getModemVersion() {
  getFromServer("localhost", 5000, "version", null);
}
