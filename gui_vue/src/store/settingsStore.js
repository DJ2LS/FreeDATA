import { defineStore } from 'pinia'
import { ref, computed } from 'vue';

export const useSettingsStore = defineStore('settingsStore', () => {

    // network
    var tnc_host = ref("127.0.0.1");
    var tnc_port = ref(3000);
    var daemon_host = ref("127.0.0.1");
    var daemon_port = ref(3001);
    var tnclocation = ref("localhost");

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
    var mycall = ref("AA0AA-0");
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
    var hamlib_rigctld_port = ref(4532);
    var hamlib_rigctld_ip = ref("127.0.0.1");
    var hamlib_rigctld_path = ref("");
    var hamlib_rigctld_server_port = ref(4532);
    var hamlib_rigctld_custom_args = ref("");

    // tci
    var tci_ip = ref('127.0.0.1');
    var tci_port = ref(50001);

    //tnc
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


  return {
    tnc_host,
    tnc_port,
    daemon_host,
    daemon_port,
    tnclocation,
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
    hamlib_rigctld_port,
    hamlib_rigctld_ip,
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
    enable_mesh_features
   };

});
