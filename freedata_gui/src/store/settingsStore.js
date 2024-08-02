import { reactive, watch } from "vue";
import { getConfig, setConfig } from "../js/api";


// Default configuration
const defaultConfig = {
  local: {
    host: "127.0.0.1",
    port: "5000",
    spectrum: "waterfall",
    wf_theme: 2,
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
      respond_to_cq: false,
      tx_delay: 0,
      enable_hamc: false,
      enable_morse_identifier: false,
      maximum_bandwidth: 3000,
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
      serial_rts: "",
    },
    RIGCTLD: {
      ip: "127.0.0.1",
      port: 0,
      path: "",
      command: "",
      arguments: "",
      enable_vfo: false,
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
    MESSAGES: {
      enable_auto_repeat: false,
    },
    GUI: {
      auto_run_browser: true,
    }
  },
};

// Initialize local settings from browser storage
const localConfig = JSON.parse(localStorage.getItem("localConfig")) || defaultConfig.local;
console.log("--------- LOCAL CONFIG -----------")
console.log(localConfig)

export const settingsStore = reactive({ ...defaultConfig, local: localConfig });
// Function to handle remote configuration changes

export function onChange() {
  setConfig(settingsStore.remote).then((conf) => {
    settingsStore.remote = conf;
  });
}

// Function to fetch remote configuration
export function getRemote() {
  return getConfig().then((conf) => {
    if (conf !== undefined) {
      settingsStore.remote = conf;
      onChange();
    } else {
      console.warn("Received undefined configuration, using default!");
      settingsStore.remote = defaultConfig.remote;
    }
  });
}

// Watcher to save local settings on change
watch(() => settingsStore.local, () => {
  saveLocalSettingsToConfig();
}, { deep: true });

// Function to save local settings to browser storage
export function saveLocalSettingsToConfig() {
  localStorage.setItem("localConfig", JSON.stringify(settingsStore.local));
  console.log("Settings saved!");
}
