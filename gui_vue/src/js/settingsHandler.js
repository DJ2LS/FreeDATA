//const path = require("path");
//const fs = require("fs");
//const os = require("os");

import path from "node:path";
import fs from "fs";
import os from "os";

// pinia store setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);
// ---------------------------------

console.log(process.env)
if(typeof process.env["APPDATA"]  !== "undefined"){
    var appDataFolder = process.env["APPDATA"]
    console.log(appDataFolder)

} else {
        switch (process.platform) {
        case "darwin":
            var appDataFolder = process.env["HOME"] + "/Library/Application Support";
            console.log(appDataFolder)

            break;
        case "linux":
            var appDataFolder = process.env["HOME"] + "/.config";
            console.log(appDataFolder)

            break;
        case "linux2":
            var appDataFolder = "undefined";
            break;
        case "windows":
            var appDataFolder = "undefined";
            break;
        default:
            var appDataFolder = "undefined";
            break;
    }
}


var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, "config.json");

console.log(appDataFolder)
console.log(configFolder)
console.log(configPath)


// create config folder if not exists
if (!fs.existsSync(configFolder)) {
  fs.mkdirSync(configFolder);
}

// create config file if not exists with defaults
const configDefaultSettings =
  '{\
                  "modem_host": "127.0.0.1",\
                  "modem_port": 3000,\
                  "daemon_host": "127.0.0.1",\
                  "daemon_port": 3001,\
                  "mycall": "AA0AA",\
                  "myssid": "0",\
                  "mygrid": "JN40aa",\
                  "radiocontrol" : "disabled",\
                  "hamlib_deviceid": "RIG_MODEL_DUMMY_NOVFO",\
                  "hamlib_deviceport": "ignore",\
                  "hamlib_stop_bits": "ignore",\
                  "hamlib_data_bits": "ignore",\
                  "hamlib_handshake": "ignore",\
                  "hamlib_serialspeed": "ignore",\
                  "hamlib_dtrstate": "ignore",\
                  "hamlib_pttprotocol": "ignore",\
                  "hamlib_ptt_port": "ignore",\
                  "hamlib_dcd": "ignore",\
                  "hamlbib_serialspeed_ptt": 9600,\
                  "hamlib_rigctld_port" : 4532,\
                  "hamlib_rigctld_ip" : "127.0.0.1",\
                  "hamlib_rigctld_path" : "",\
                  "hamlib_rigctld_server_port" : 4532,\
                  "hamlib_rigctld_custom_args": "",\
                  "tci_port" : 50001,\
                  "tci_ip" : "127.0.0.1",\
                  "spectrum": "waterfall",\
                  "enable_scatter" : "False",\
                  "enable_fft" : "False",\
                  "enable_fsk" : "False",\
                  "low_bandwidth_mode" : "False",\
                  "theme" : "default",\
                  "screen_height" : 430,\
                  "screen_width" : 1050,\
                  "update_channel" : "latest",\
                  "beacon_interval" : 300,\
                  "received_files_folder" : "None",\
                  "tuning_range_fmin" : "-50.0",\
                  "tuning_range_fmax" : "50.0",\
                  "respond_to_cq" : "True",\
                  "rx_buffer_size" : 16, \
                  "enable_explorer" : "False", \
                  "wftheme": 2, \
                  "high_graphics" : "True",\
                  "explorer_stats" : "False", \
                  "auto_tune" : "False", \
                  "enable_is_writing" : "True", \
                  "shared_folder_path" : ".", \
                  "enable_request_profile" : "True", \
                  "enable_request_shared_folder" : "False", \
                  "max_retry_attempts" : 5, \
                  "enable_auto_retry" : "False", \
                  "tx_delay" : 0, \
                  "auto_start": 0, \
                  "enable_sys_notification": 1, \
                  "enable_mesh_features": "False" \
                  }';

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

  var parsedConfig = JSON.parse(configDefaultSettings);
  for (var key in parsedConfig) {
    if (config.hasOwnProperty(key)) {
      console.log("FOUND SETTTING [" + key + "]: " + config[key]);
    } else {
      console.log("MISSING SETTTING [" + key + "] : " + parsedConfig[key]);
      config[key] = parsedConfig[key];
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    }
    try {
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
