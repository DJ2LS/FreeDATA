import { reactive, watch } from "vue";

import { getConfig, setConfig } from "../js/api";

export const settingsStore = reactive({
  local: {
    host: "127.0.0.1",
    port: "5000",
    enable_fft: false,
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
      mycall: "",
      myssid: 0,
      mygrid: "",
      ssid_list: [],
    },
    TCI: {
      tci_ip: "127.0.0.1",
      tci_port: 0,
    },
  },
});

export function onChange() {
  setConfig(settingsStore.remote).then((conf) => {
    settingsStore.remote = conf;
  });
}

export function getRemote() {
  return getConfig().then((conf) => {
    settingsStore.remote = conf;
  });
}

watch(settingsStore.local, (oldValue, newValue) => {
  // TODO handle local file saving
  const cenas = newValue;
});
