import path from "node:path";
import fs from "fs";
import { setColormap } from "./waterfallHandler";
// pinia store setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import { postToServer, getFromServer } from "./rest.js";

// ---------------------------------

console.log(process.env);
var appDataFolder = "undefined";
if (typeof process.env["APPDATA"] !== "undefined") {
  appDataFolder = process.env["APPDATA"];
  console.log(appDataFolder);
} else {
  switch (process.platform) {
    case "darwin":
      appDataFolder = process.env["HOME"] + "/Library/Application Support";
      console.log(appDataFolder);
      break;
    case "linux":
      appDataFolder = process.env["HOME"] + "/.config";
      console.log(appDataFolder);
      break;
    case "win32":
      appDataFolder = "undefined";
      break;
    default:
      appDataFolder = "undefined";
      break;
  }
}

var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, "config.json");

console.log(appDataFolder);
console.log(configFolder);
console.log(configPath);

// create config folder if not exists
if (!fs.existsSync(configFolder)) {
  fs.mkdirSync(configFolder);
}

// create config file if not exists with defaults
const configDefaultSettings = `{
    "modem_host": "127.0.0.1",
    "modem_port": 3000,
    "spectrum": "waterfall",
    "theme": "default",
    "screen_height": 430,
    "screen_width": 1050,
    "update_channel": "latest",
    "wftheme": 2,
    "enable_sys_notification": 1
}`;
var parsedConfig = JSON.parse(configDefaultSettings);

if (!fs.existsSync(configPath)) {
  fs.writeFileSync(configPath, configDefaultSettings);
}

export function loadSettings() {
  // load settings
  var config = require(configPath);

  //config validation
  // check running config against default config.
  // if parameter not exists, add it to running config to prevent errors
  console.log("CONFIG VALIDATION  -----------------------------  ");

  for (var key in parsedConfig) {
    if (config.hasOwnProperty(key)) {
      console.log("FOUND SETTTING [" + key + "]: " + config[key]);
    } else {
      console.log("MISSING SETTTING [" + key + "] : " + parsedConfig[key]);
      config[key] = parsedConfig[key];
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    }
    try {
      if (key == "wftheme") {
        setColormap(config[key]);
      }
      if (key == "mycall") {
        settings.mycall = config[key].split("-")[0];
        settings.myssid = config[key].split("-")[1];
      } else {
        settings[key] = config[key];
      }
    } catch (e) {
      console.log(e);
    }
  }
}

export function saveSettingsToFile() {
  console.log("save settings to file...");
  let config = settings.getJSON();
  console.log(config);
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
}

export function processModemConfig(data) {
  // update our settings from get request
  // TODO Can we make this more dynamic? Maybe using a settings object?
  // For now its a hardcoded structure until we found a better way

  console.log(data);

  // STATION SETTINGS
  // Extract the callsign and SSID
  if (data.STATION.mycall.includes("-")) {
    const splittedCallsign = data.STATION.mycall.split("-");
    settings.mycall = splittedCallsign[0]; // The part before the hyphen
    settings.myssid = parseInt(splittedCallsign[1], 10); // The part after the hyphen, converted to a number
  } else {
    settings.mycall = data.STATION.mycall; // Use the original mycall if no SSID is present
    settings.myssid = 0; // Default SSID if not provided
  }
  settings.mygrid = data.STATION.mygrid;

  // ssid list not yet implemented
  //data.STATION.ssid_list[0];

  // AUDIO SETTINGS
  settings.auto_tune = data.AUDIO.auto_tune;
  settings.rx_audio_level = data.AUDIO.rxaudiolevel;
  settings.tx_audio_level = data.AUDIO.txaudiolevel;

  // MODEM SETTINGS
  settings.enable_fft = data.Modem.fft;
  settings.enable_fsk = data.Modem.fsk;
  settings.tuning_range_fmin = data.Modem.fmin;
  settings.tuning_range_fmax = data.Modem.fmax;
  settings.rx_buffer_size = data.Modem.rx_buffer_size;
  settings.enable_explorer = data.Modem.explorer;
  settings.explorer_stats = data.Modem.stats;
  settings.tx_delay = data.Modem.tx_delay;
  settings.respond_to_cq = data.Modem.qrv;
  settings.low_bandwidth_mode = data.Modem.narrowband;

  // HAMLIB SETTINGS
  settings.hamlib_rigctld_port = data.RADIO.rigctld_port;
  settings.hamlib_rigctld_ip = data.RADIO.rigctld_ip;
  settings.radiocontrol = data.RADIO.radiocontrol;

  // TCI SETTINGS
  settings.tci_ip = data.TCI.ip;
  settings.tci_port = data.TCI.port;

  // MESH SETTINGS
  settings.enable_mesh_features = data.MESH.enable_protocol;
}

export function getModemConfigAsJSON() {
  // create json output from settings
  // TODO Can we make this more dynamic? Maybe using a settings object?
  // For now its a hardcoded structure until we found a better way

  const configData = {
    AUDIO: {
      auto_tune: settings.auto_tune,
      rx: "560f",
      rxaudiolevel: settings.rx_audio_level,
      tx: "560f",
      txaudiolevel: settings.tx_audio_level,
    },
    MESH: {
      enable_protocol: settings.enable_mesh_features,
    },
    Modem: {
      explorer: settings.enable_explorer,
      fft: settings.enable_fft,
      fmax: settings.tuning_range_fmax,
      fmin: settings.tuning_range_fmin,
      fsk: settings.enable_fsk,
      narrowband: settings.low_bandwidth_mode,
      qrv: settings.respond_to_cq,
      rx_buffer_size: settings.rx_buffer_size,
      scatter: "False",
      stats: settings.explorer_stats,
      tx_delay: settings.tx_delay,
    },
    NETWORK: {
      modemport: "3000",
    },
    RADIO: {
      radiocontrol: settings.radiocontrol,
      rigctld_ip: settings.hamlib_rigctld_ip,
      rigctld_port: settings.hamlib_rigctld_port,
    },
    STATION: {
      mycall: settings.mycall + "-" + settings.myssid,
      mygrid: settings.mygrid,
      ssid_list: [],
    },
    TCI: {
      ip: settings.tci_ip,
      port: settings.tci_port,
    },
  };

  return configData;
}

export function fetchSettings() {
  // fetch Settings
  getFromServer("localhost", 5000, "config");
  getFromServer("localhost", 5000, "devices/audio");
  getFromServer("localhost", 5000, "devices/serial");
}

export function saveSettings() {
  // save settings via post
  console.log("post settings");
  postToServer("localhost", 5000, "config", getModemConfigAsJSON());
}
