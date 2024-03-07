import { defineStore } from "pinia";
import { ref } from "vue";

export const useChatStore = defineStore("chatStore", () => {


  var callsign_list = ref();
  var sorted_chat_list = ref();
  var newChatCallsign = ref();
  var newChatMessage = ref();


  /* ------------------------------------------------ */
    // Scroll to bottom functions
  const scrollTrigger = ref(0);

  function triggerScrollToBottom() {
    scrollTrigger.value++;
  }


  /* ------------------------------------------------ */

  var chat_filter = ref([
    { type: "newchat" },
    { type: "received" },
    { type: "transmit" },
    { type: "ping-ack" },
    { type: "broadcast_received" },
    { type: "broadcast_transmit" },
    //{ type: "request" },
    //{ type: "response" },
  ]);

  var selectedCallsign = ref();
  // we need a default value in our ref because of our message info modal
  var selectedMessageObject = ref({
    command: "msg",
    hmac_signed: false,
    percent: 0,
    is_new: false,
    _id: "2ead6698",
    timestamp: 1697289795,
    dxcallsign: "DJ2LS-0",
    dxgrid: "null",
    msg: "test",
    checksum: "",
    type: "transmit",
    status: "transmitting",
    attempt: 1,
    uuid: "2ead6698",
    duration: 0,
    nacks: 0,
    speed_list: "null",
    _attachments: {
      "": {
        content_type: "text",
        data: "",
      },
    },
  });
  var inputText = ref("");
  var inputFile = ref();
  var inputFileName = ref("-");
  var inputFileType = ref("-");
  var inputFileSize = ref("-");

  var sorted_beacon_list = ref({});
  var unsorted_beacon_list = ref({});

  var chartSpeedPER0 = ref();
  var chartSpeedPER25 = ref();
  var chartSpeedPER75 = ref();

  //    var beaconDataArray = ref([-3, 10, 8, 5, 3, 0, -5, 10, 8, 5, 3, 0, -5, 10, 8, 5, 3, 0, -5, 10, 8, 5, 3, 0, -5])
  //    var beaconLabelArray = ref(['18:10', '19:00', '23:00', '01:13', '04:25', '08:15', '09:12', '18:10', '19:00', '23:00', '01:13', '04:25', '08:15', '09:12', '18:10', '19:00', '23:00', '01:13', '04:25', '08:15', '09:12', '01:13', '04:25', '08:15', '09:12'])
  var beaconDataArray = ref([]);
  var beaconLabelArray = ref([]);

  var arq_speed_list_bpm = ref([]);
  var arq_speed_list_timestamp = ref([]);
  var arq_speed_list_snr = ref([]);

  return {
    selectedCallsign,
    newChatCallsign,
    newChatMessage,
    selectedMessageObject,
    inputText,
    chat_filter,
    callsign_list,
    sorted_chat_list,
    inputFileName,
    inputFileSize,
    inputFileType,
    inputFile,
    chartSpeedPER0,
    chartSpeedPER25,
    chartSpeedPER75,
    beaconDataArray,
    beaconLabelArray,
    unsorted_beacon_list,
    sorted_beacon_list,
    arq_speed_list_bpm,
    arq_speed_list_snr,
    arq_speed_list_timestamp,
    scrollTrigger,
    triggerScrollToBottom,
  };
});
