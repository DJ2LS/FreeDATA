import { defineStore } from "pinia";
import { ref } from "vue";
import * as bootstrap from "bootstrap";

export const useStateStore = defineStore("stateStore", () => {
  var busy_state = ref();
  var arq_state = ref("-");
  var frequency = ref(0);
  var new_frequency = ref(14093000);
  var mode = ref("-");
  var rf_level = ref("10");
  var bandwidth = ref("-");

  var swr = ref(0);
  var tuner = ref();

  var dbfs_level_percent = ref(0);
  var dbfs_level = ref(0);
  var radio_status = ref(false);

  var ptt_state = ref(false);

  var speed_level = ref(0);
  var fft = ref();
  var channel_busy = ref(false);
  var channel_busy_slot = ref([false, false, false, false, false]);
  var scatter = ref([]);
  var s_meter_strength_percent = ref(0);
  var s_meter_strength_raw = ref(0);

  var modem_connection = ref("disconnected");
  var modemStartCount = ref(0);
  var is_modem_running = ref();

  var arq_total_bytes = ref(0);
  var arq_transmission_percent = ref(0);

  var activities = ref([]);
  var heard_stations = ref([]);
  var dxcallsign = ref("");

  var arq_session_state = ref("");
  var arq_state = ref("");
  var beacon_state = ref(false);
  var away_from_key = ref(false);

  var audio_recording = ref(false);

  var hamlib_status = ref("");
  var tx_audio_level = ref("");
  var rx_audio_level = ref("");

  var alc = ref("");

  var is_codec2_traffic = ref("");

  var arq_speed_list_timestamp = ref([]);
  var arq_speed_list_bpm = ref([]);
  var arq_speed_list_snr = ref([]);

  var arq_is_receiving = ref(false)

  /* TODO Those 3 can be removed I guess , DJ2LS*/
  var arq_seconds_until_finish = ref();
  var arq_seconds_until_timeout = ref();
  var arq_seconds_until_timeout_percent = ref();

  var rigctld_started = ref();
  var rigctld_process = ref();

  var python_version = ref();
  var modem_version = ref();

  var rx_buffer_length = ref();

  function updateTncState(state) {
    modem_connection.value = state;

    if (modem_connection.value == "open") {
      //GUI will auto connect to TNC if already running, if that is the case increment start count if 0
      if (modemStartCount.value == 0) modemStartCount.value++;
    }
  }

  return {
    dxcallsign,
    busy_state,
    arq_state,
    new_frequency,
    frequency,
    mode,
    bandwidth,
    tuner,
    swr,
    tuner,
    dbfs_level,
    dbfs_level_percent,
    speed_level,
    fft,
    channel_busy,
    channel_busy_slot,
    scatter,
    ptt_state,
    s_meter_strength_percent,
    s_meter_strength_raw,
    arq_total_bytes,
    audio_recording,
    hamlib_status,
    tx_audio_level,
    rx_audio_level,
    alc,
    updateTncState,
    arq_transmission_percent,
    arq_speed_list_bpm,
    arq_speed_list_timestamp,
    arq_speed_list_snr,
    arq_seconds_until_finish,
    arq_seconds_until_timeout,
    arq_seconds_until_timeout_percent,
    arq_is_receiving,
    modem_connection,
    is_modem_running,
    arq_session_state,
    is_codec2_traffic,
    rf_level,
    activities,
    heard_stations,
    beacon_state,
    away_from_key,
    rigctld_started,
    rigctld_process,
    python_version,
    modem_version,
    rx_buffer_length,
    radio_status,
  };
});
