import path from "node:path";
import fs from "fs";
import { setColormap } from "./waterfallHandler";
// pinia store setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

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
  console.log(data);
  // basic test if we received settings
  // we should iterate through JSON, by using equal variables here like in modem config
  // STATION SETTINGS
  settings.mycall = data["STATION"].mycall;
  settings.mygrid = data["STATION"].mygrid;
}
