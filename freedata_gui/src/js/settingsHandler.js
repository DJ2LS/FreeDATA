import path from "node:path";
import fs from "fs";
import { setColormap } from "./waterfallHandler";
// pinia store setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { settingsStore as settings, onChange } from "../store/settingsStore.js";

import { useStateStore } from "../store/stateStore";
const stateStore = useStateStore(pinia);



// create config file if not exists with defaults
const configDefaultSettings = `{
    "screen_height": 670,
    "screen_width": 1200,
    "spectrum": "waterfall",
    "screen_height": 430,
    "screen_width": 1050,
    "wftheme": 2,
    "enable_sys_notification": 1
}`;
var parsedConfig = JSON.parse(configDefaultSettings);


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
        setColormap();
      }
      if (key == "mycall") {
        settings.remote.STATION.mycall = config[key].split("-")[0];
        settings.remote.STATION.myssid = config[key].split("-")[1];
      } else {
        settings[key] = config[key];
      }
    } catch (e) {
      console.log(e);
    }
  }
}

//No longer used...
//export function saveSettingsToFile() {
//  console.log("save settings to file...");
//  let config = settings.getJSON();
//  console.log(config);
//  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
//}

export function processModemConfig(data) {
  // update our settings from get request
  // TODO Can we make this more dynamic? Maybe using a settings object?
  // For now its a hardcoded structure until we found a better way

  console.log(data);
  for (const category in data) {
    if (data.hasOwnProperty(category)) {
      for (const setting in data[category]) {
        if (data[category].hasOwnProperty(setting)) {
          // Create a variable name combining the category and setting name
          const variableName = setting;
          // Assign the value to the variable
          if (variableName == "mycall") {
            let mycall = data[category][setting];
            if (mycall.includes("-")) {
              const splittedCallsign = mycall.split("-");
              settings.remote.STATION.mycall = splittedCallsign[0]; // The part before the hyphen
              settings.remote.STATION.myssid = parseInt(
                splittedCallsign[1],
                10,
              ); // The part after the hyphen, converted to a number
            } else {
              settings.remote.STATION.mycall = mycall; // Use the original mycall if no SSID is present
              settings.remote.STATION.myssid = 0; // Default SSID if not provided
            }
          } else {
            settings[variableName] = data[category][setting];
          }
          console.log(variableName + ": " + settings[variableName]);
        }
      }
    }
  }
}
