import { getModemConfigAsJSON } from "./settingsHandler.ts";
import { getFromServer, postToServer } from "./rest.js";
import { useSettingsStore } from "../store/settingsStore.js";
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
const settings = useSettingsStore(pinia);

export function getModemConfig() {
  // fetch Settings
  getFromServer(settings.modem_host, settings.modem_port, "config");
  getFromServer(settings.modem_host, settings.modem_port, "devices/audio");
  getFromServer(settings.modem_host, settings.modem_port, "devices/serial");
}

export function saveModemConfig() {
  postToServer(
    settings.modem_host,
    settings.modem_port,
    "config",
    getModemConfigAsJSON(),
  );
}

export function startModem() {
  postToServer(settings.modem_host, settings.modem_port, "modem/start", null);
}

export function stopModem() {
  postToServer(settings.modem_host, settings.modem_port, "modem/stop", null);
}

export function getModemVersion() {
  getFromServer(settings.modem_host, settings.modem_port, "version", null);
}
export function getModemCurrentState() {
  getFromServer(settings.modem_host, settings.modem_port, "modem/state", null);
}