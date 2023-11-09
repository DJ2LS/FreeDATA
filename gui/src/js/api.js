import { getModemConfigAsJSON } from "./settingsHandler.ts";

export function getModemConfig() {
  // fetch Settings
  getFromServer("localhost", 5000, "config");
  getFromServer("localhost", 5000, "devices/audio");
  getFromServer("localhost", 5000, "devices/serial");
}

export function saveModemConfig() {
  postToServer("localhost", 5000, "config", getModemConfigAsJSON());
}

export function fetchSettings() {}

export function saveSettings() {
  // save settings via post
  console.log("post settings");
}
