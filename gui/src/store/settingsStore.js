import { reactive, ref, watch } from "vue";
import { getConfig, setConfig } from "../js/api";
import { getAppDataPath } from "../js/freedata";
import fs from "fs";
const path = require("path");
const nconf = require("nconf");

var appDataPath = getAppDataPath();
var configFolder = path.join(appDataPath, "FreeDATA");
let configFile = "config.json";

const isGitHubActions = process.env.GITHUB_ACTIONS === "true";
if (isGitHubActions) {
  configFile = "example.json";
  configFolder = appDataPath;
}

var configPath = path.join(configFolder, configFile);

console.log("AppData Path:", appDataPath);
console.log(configFolder);
console.log(configPath);

nconf.file({ file: configPath });

// +++
//GUI DEFAULT SETTINGS........
//Set GUI defaults here, they will be used if not found in config/config.json
//They should be an exact mirror (variable wise) of settingsStore.local
//Nothing else should be needed aslong as components are using v-bind
// +++

const defaultConfig = {
  local: {
    host: "127.0.0.1",
    port: "5000",
    spectrum: "waterfall",
    wf_theme: 2,
    update_channel: "alpha",
    enable_sys_notification: false,
    grid_layout: "[]",
    grid_preset: "[]",
    grid_enabled: true,
  },
  remote: {
    AUDIO: {
      enable_auto_tune: false,
      input_device: "",
      output_device: "",
      rx_audio_level: 0,
      tx_audio_level: 0,
    },
    MESH: {
      enable_protocol: false,
    },
    MODEM: {
      enable_fft: false,
      enable_fsk: false,
      enable_low_bandwidth_mode: false,
      respond_to_cq: false,
      rx_buffer_size: 0,
      tuning_range_fmax: 0,
      tuning_range_fmin: 0,
      tx_delay: 0,
      beacon_interval: 0,
      enable_hamc: false,
      enable_morse_identifier: false,
    },
    RADIO: {
      control: "disabled",
      model_id: 0,
      serial_port: "",
      serial_speed: "",
      data_bits: 0,
      stop_bits: 0,
      serial_handshake: "",
      ptt_port: "",
      ptt_type: "",
      serial_dcd: "",
      serial_dtr: "",
    },
    RIGCTLD: {
      ip: "127.0.0.1",
      port: 0,
      path: "",
      command: "",
      arguments: "",
    },
    STATION: {
      enable_explorer: false,
      enable_stats: false,
      mycall: "DEFAULT",
      myssid: 0,
      mygrid: "",
      ssid_list: [],
    },
    TCI: {
      tci_ip: "127.0.0.1",
      tci_port: 0,
    },
  },
};

nconf.defaults(defaultConfig);
nconf.required(["local:host", "local:port"]);

export const settingsStore = reactive(defaultConfig);

//Save settings for GUI to config file
settingsStore.local = nconf.get("local");
saveLocalSettingsToConfig();

export function onChange() {
  setConfig(settingsStore.remote).then((conf) => {
    settingsStore.remote = conf;
  });
}

export function getRemote() {
  return getConfig().then((conf) => {
    if (typeof conf !== "undefined") {
      settingsStore.remote = conf;
      onChange();
    } else {
      console.warn("Received undefined configuration, using default!");
      settingsStore.remote = defaultConfig.remote;
    }
  });
}

watch(settingsStore.local, (oldValue, newValue) => {
  //This function watches for changes, and triggers a save of local settings
  saveLocalSettingsToConfig();
});

export function saveLocalSettingsToConfig() {
  nconf.set("local", settingsStore.local);
  nconf.save();
  //console.log("Settings saved!");
}
