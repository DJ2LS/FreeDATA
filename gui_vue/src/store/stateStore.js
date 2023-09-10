import { defineStore } from 'pinia'
import { ref, computed } from 'vue';
import * as bootstrap from 'bootstrap'

export const useStateStore = defineStore('stateStore', () => {
    var busy_state = ref("-")
    var arq_state = ref("-")
    var frequency = ref("-")
    var mode = ref("-")
    var bandwidth = ref("-")
    var dbfs_level = ref(0)
    var ptt_state = ref("False")

    var speed_level = ref(0)
    var fft = ref()
    var channel_busy = ref("False")
    var channel_busy_slot = ref()
    var scatter = ref()
    var s_meter_strength_percent = ref(0)
    var s_meter_strength_raw = ref(0)

    var tnc_connection = ref("disconnected")
    var tncStartCount = ref(0)
    var tnc_running_state = ref("--------")

    var arq_total_bytes = ref(0)
    
    var heard_stations = ref("")
    var dxcallsign = ref("")

    var arq_session_state = ref("")
    var arq_state = ref("")
    var beacon_state = ref("False")





    function updateTncState(state){

    tnc_connection.value = state;


    if (tnc_connection.value == "open") {

    // collapse settings screen
    var collapseFirstRow = new bootstrap.Collapse(
      document.getElementById("collapseFirstRow"),
      { toggle: false },
    );
    collapseFirstRow.hide();
    var collapseSecondRow = new bootstrap.Collapse(
      document.getElementById("collapseSecondRow"),
      { toggle: false },
    );
    collapseSecondRow.hide();
    var collapseThirdRow = new bootstrap.Collapse(
      document.getElementById("collapseThirdRow"),
      { toggle: false },
    );
    collapseThirdRow.show();
    var collapseFourthRow = new bootstrap.Collapse(
      document.getElementById("collapseFourthRow"),
      { toggle: false },
    );
    collapseFourthRow.show();

    //Set tuning for fancy graphics mode (high/low CPU)
    //set_CPU_mode();

    //GUI will auto connect to TNC if already running, if that is the case increment start count if 0
    if (tncStartCount.value == 0) tncStartCount++;
  } else {

    // collapse settings screen
    var collapseFirstRow = new bootstrap.Collapse(
      document.getElementById("collapseFirstRow"),
      { toggle: false },
    );
    collapseFirstRow.show();
    var collapseSecondRow = new bootstrap.Collapse(
      document.getElementById("collapseSecondRow"),
      { toggle: false },
    );
    collapseSecondRow.show();
    var collapseThirdRow = new bootstrap.Collapse(
      document.getElementById("collapseThirdRow"),
      { toggle: false },
    );
    collapseThirdRow.hide();
    var collapseFourthRow = new bootstrap.Collapse(
      document.getElementById("collapseFourthRow"),
      { toggle: false },
    );
    collapseFourthRow.hide();
  }
};







  return { dxcallsign, busy_state, arq_state, frequency, mode, bandwidth, dbfs_level, speed_level, fft, channel_busy, channel_busy_slot, scatter, ptt_state, s_meter_strength_percent, s_meter_strength_raw, arq_total_bytes, updateTncState };
});
