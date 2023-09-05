import { defineStore } from 'pinia'
import { ref, computed } from 'vue';

export const useSettingsStore = defineStore('settingsStore', () => {

    // station
    var mycall = ref("AA0AA-0")
    var mygrid = ref("JN40aa")

    // rigctld
    var hamlib_rigctld_port = ref(4532)
    var hamlib_rigctld_ip = ref("127.0.0.1")
    /*
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
                  "hamlbib_serialspeed_ptt": "9600",\
                  "hamlib_rigctld_port" : "4532",\
                  "hamlib_rigctld_ip" : "127.0.0.1",\
                  "hamlib_rigctld_path" : "",\
                  "hamlib_rigctld_server_port" : "4532",\
                  "hamlib_rigctld_custom_args": "",\
                  */

    // tci
    var tci_ip = ref('127.0.0.1')
    var tci_port = ref(50001)


/*
                  "tnc_host": "127.0.0.1",\
                  "tnc_port": "3000",\
                  "daemon_host": "127.0.0.1",\
                  "daemon_port": "3001",\

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
                  "hamlbib_serialspeed_ptt": "9600",\
                  "hamlib_rigctld_port" : "4532",\
                  "hamlib_rigctld_ip" : "127.0.0.1",\
                  "hamlib_rigctld_path" : "",\
                  "hamlib_rigctld_server_port" : "4532",\
                  "hamlib_rigctld_custom_args": "",\

                  "spectrum": "waterfall",\
                  "tnclocation": "localhost",\
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
                  "rx_buffer_size" : "16", \
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
*/
  return {
    mycall,
    mygrid,
    tci_ip,
    tci_port,
    hamlib_rigctld_ip,
    hamlib_rigctld_port
   };

});
