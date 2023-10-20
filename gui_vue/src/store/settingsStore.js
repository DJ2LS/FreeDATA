import { defineStore } from "pinia";
import { ref } from "vue";

export const useSettingsStore = defineStore("settingsStore", () => {
  // audio
  var tx_audio = ref()
  var rx_audio = ref()

  // network
  var modem_host = ref("127.0.0.1");
  var modem_port = ref(3000);
  var daemon_host = ref(modem_host.value);
  var daemon_port = ref(modem_port.value + 1);

  // app
  var screen_height = ref(430);
  var screen_width = ref(1050);
  var theme = ref("default");
  var wftheme = ref(2);
  var high_graphics = ref("False");
  var auto_start = ref(0);
  var enable_sys_notification = ref(1);

  // chat
  var shared_folder_path = ref(".");
  var enable_request_profile = ref("True");
  var enable_request_shared_folder = ref("False");
  var max_retry_attempts = ref(5);
  var enable_auto_retry = ref("False");

  // station
  var mycall = ref("AA0AA-5");
  var myssid = ref(0);
  var mygrid = ref("JN20aa");

  // rigctld
  var hamlib_rigctld_port = ref(4532);
  var hamlib_rigctld_ip = ref("127.0.0.1");
  var radiocontrol = ref("disabled");
  var hamlib_deviceid = ref("RIG_MODEL_DUMMY_NOVFO");
  var hamlib_deviceport = ref("ignore");
  var hamlib_stop_bits = ref("ignore");
  var hamlib_data_bits = ref("ignore");
  var hamlib_handshake = ref("ignore");
  var hamlib_serialspeed = ref("ignore");
  var hamlib_dtrstate = ref("ignore");
  var hamlib_pttprotocol = ref("ignore");
  var hamlib_ptt_port = ref("ignore");
  var hamlib_dcd = ref("ignore");
  var hamlbib_serialspeed_ptt = ref(9600);
  var hamlib_rigctld_path = ref("");
  var hamlib_rigctld_server_port = ref(4532);
  var hamlib_rigctld_custom_args = ref("");

  // tci
  var tci_ip = ref("127.0.0.1");
  var tci_port = ref(50001);

  //modem
  var spectrum = ref("waterfall");
  var enable_scatter = ref("False");
  var enable_fft = ref("False");
  var enable_fsk = ref("False");
  var low_bandwidth_mode = ref("False");
  var update_channel = ref("latest");
  var beacon_interval = ref(300);
  var received_files_folder = ref("None");
  var tuning_range_fmin = ref(-50.0);
  var tuning_range_fmax = ref(50.0);
  var respond_to_cq = ref("True");
  var rx_buffer_size = ref(16);
  var enable_explorer = ref("False");
  var explorer_stats = ref("False");
  var auto_tune = ref("False");
  var enable_is_writing = ref("True");
  var tx_delay = ref(0);
  var enable_mesh_features = ref("False");
  var serial_devices = ref();


  function getSerialDevices() {
    var html = "";
    for (var key in serial_devices.value) {
      html += `<option value="${serial_devices.value[key]["port"]}">${serial_devices.value[key]["port"]} - ${serial_devices.value[key]["description"]}</option>`;
    }
    return html;
  }

  function getJSON() {
    var config_export = {
      modem_host: modem_host.value,
      modem_port: modem_port.value,
      daemon_host: modem_host.value,
      daemon_port: (parseInt(modem_port.value) + 1).toString(),
      mycall: mycall.value,
      myssid: myssid.value,
      mygrid: mygrid.value,
      radiocontrol: radiocontrol.value,
      hamlib_deviceid: hamlib_deviceid.value,
      hamlib_deviceport: hamlib_deviceport.value,
      hamlib_stop_bits: hamlib_stop_bits.value,
      hamlib_data_bits: hamlib_data_bits.value,
      hamlib_handshake: hamlib_handshake.value,
      hamlib_serialspeed: hamlib_serialspeed.value,
      hamlib_dtrstate: hamlib_dtrstate.value,
      hamlib_pttprotocol: hamlib_pttprotocol.value,
      hamlib_ptt_port: hamlib_ptt_port.value,
      hamlib_dcd: hamlib_dcd.value,
      hamlbib_serialspeed_ptt: hamlib_serialspeed.value,
      hamlib_rigctld_port: hamlib_rigctld_port.value,
      hamlib_rigctld_ip: hamlib_rigctld_ip.value,
      hamlib_rigctld_path: hamlib_rigctld_path.value,
      hamlib_rigctld_server_port: hamlib_rigctld_server_port.value,
      hamlib_rigctld_custom_args: hamlib_rigctld_custom_args.value,
      tci_port: tci_port.value,
      tci_ip: tci_ip.value,
      spectrum: spectrum.value,
      enable_scatter: enable_scatter.value,
      enable_fft: enable_fft.value,
      enable_fsk: enable_fsk.value,
      low_bandwidth_mode: low_bandwidth_mode.value,
      theme: theme.value,
      screen_height: screen_height.value,
      screen_width: screen_width.value,
      update_channel: update_channel.value,
      beacon_interval: beacon_interval.value,
      received_files_folder: received_files_folder.value,
      tuning_range_fmin: tuning_range_fmin.value,
      tuning_range_fmax: tuning_range_fmax.value,
      respond_to_cq: respond_to_cq.value,
      rx_buffer_size: rx_buffer_size.value,
      enable_explorer: enable_explorer.value,
      wftheme: wftheme.value,
      high_graphics: high_graphics.value,
      explorer_stats: explorer_stats.value,
      auto_tune: auto_tune.value,
      enable_is_writing: enable_is_writing.value,
      shared_folder_path: shared_folder_path.value,
      enable_request_profile: enable_request_profile.value,
      enable_request_shared_folder: enable_request_shared_folder.value,
      max_retry_attempts: max_retry_attempts.value,
      enable_auto_retry: enable_auto_retry.value,
      tx_delay: tx_delay.value,
      auto_start: auto_start.value,
      enable_sys_notification: enable_sys_notification.value,
      enable_mesh_features: enable_mesh_features.value,
      tx_audio: tx_audio.value,
      rx_audio: rx_audio.value,
    };

    return config_export;
  }

  return {
    modem_host,
    modem_port,
    daemon_host,
    daemon_port,
    screen_height,
    screen_width,
    theme,
    wftheme,
    high_graphics,
    auto_start,
    enable_sys_notification,
    shared_folder_path,
    enable_request_profile,
    enable_request_shared_folder,
    max_retry_attempts,
    enable_auto_retry,
    mycall,
    myssid,
    mygrid,
    hamlib_rigctld_port,
    hamlib_rigctld_ip,
    radiocontrol,
    hamlib_deviceid,
    hamlib_deviceport,
    hamlib_stop_bits,
    hamlib_data_bits,
    hamlib_handshake,
    hamlib_serialspeed,
    hamlib_dtrstate,
    hamlib_pttprotocol,
    hamlib_ptt_port,
    hamlib_dcd,
    hamlbib_serialspeed_ptt,
    hamlib_rigctld_path,
    hamlib_rigctld_server_port,
    hamlib_rigctld_custom_args,
    tci_ip,
    tci_port,
    spectrum,
    enable_scatter,
    enable_fft,
    enable_fsk,
    low_bandwidth_mode,
    update_channel,
    beacon_interval,
    received_files_folder,
    tuning_range_fmin,
    tuning_range_fmax,
    respond_to_cq,
    rx_buffer_size,
    enable_explorer,
    explorer_stats,
    auto_tune,
    enable_is_writing,
    tx_delay,
    enable_mesh_features,
    getJSON,
    tx_audio,
    rx_audio,
    getSerialDevices,
    serial_devices
  };
});
