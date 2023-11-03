import { defineStore } from "pinia";
import { ref } from "vue";
import * as bootstrap from "bootstrap";

export const useStateStore = defineStore("stateStore", () => {
  var busy_state = ref("-");
  var arq_state = ref("-");
  var frequency = ref("-");
  var new_frequency = ref(0);
  var mode = ref("-");
  var rf_level = ref("10");
  var bandwidth = ref("-");
  var dbfs_level_percent = ref(0);
  var dbfs_level = ref(0);

  var ptt_state = ref("False");

  var speed_level = ref(0);
  var fft = ref();
  var channel_busy = ref("");
  var channel_busy_slot = ref();
  var scatter = ref();
  var s_meter_strength_percent = ref(0);
  var s_meter_strength_raw = ref(0);

  var modem_connection = ref("disconnected");
  var modemStartCount = ref(0);
  var modem_running_state = ref("--------");

  var arq_total_bytes = ref(0);
  var arq_transmission_percent = ref(0);

  var heard_stations = ref("");
  var dxcallsign = ref("");

  var arq_session_state = ref("");
  var arq_state = ref("");
  var beacon_state = ref("False");

  var audio_recording = ref("");

  var hamlib_status = ref("");
  var tx_audio_level = ref("");
  var alc = ref("");

  var is_codec2_traffic = ref("");

  var arq_speed_list_timestamp = ref([]);
  var arq_speed_list_bpm = ref([]);
  var arq_speed_list_snr = ref([]);

  var arq_seconds_until_finish = ref();
  var arq_seconds_until_timeout = ref();
  var arq_seconds_until_timeout_percent = ref();

  var rigctld_started = ref();
  var rigctld_process = ref();

  var python_version = ref();
  var modem_version = ref();

  var rx_buffer_length = ref();

  function getChannelBusySlotState(slot) {
    const slot_state = channel_busy_slot.value;

    if (typeof slot_state !== "undefined") {
      // Replace 'False' with 'false' to match JavaScript's boolean representation
      const string = slot_state
        .replace(/False/g, "false")
        .replace(/True/g, "true");

      // Parse the string to get an array
      const arr = JSON.parse(string);

      return arr[slot];
    } else {
      // Handle the undefined case
      return false;
    }
  }

  function updateTncState(state) {
    modem_connection.value = state;

    if (modem_connection.value == "open") {
      //Set tuning for fancy graphics mode (high/low CPU)
      //set_CPU_mode();

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
    dbfs_level,
    dbfs_level_percent,
    speed_level,
    fft,
    channel_busy,
    channel_busy_slot,
    getChannelBusySlotState,
    scatter,
    ptt_state,
    s_meter_strength_percent,
    s_meter_strength_raw,
    arq_total_bytes,
    audio_recording,
    hamlib_status,
    tx_audio_level,
    alc,
    updateTncState,
    arq_transmission_percent,
    arq_speed_list_bpm,
    arq_speed_list_timestamp,
    arq_speed_list_snr,
    arq_seconds_until_finish,
    arq_seconds_until_timeout,
    arq_seconds_until_timeout_percent,
    modem_connection,
    modem_running_state,
    arq_session_state,
    is_codec2_traffic,
    rf_level,
    heard_stations,
    beacon_state,
    rigctld_started,
    rigctld_process,
    python_version,
    modem_version,
    rx_buffer_length,
  };
});
