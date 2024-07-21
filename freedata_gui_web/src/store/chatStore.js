import { defineStore } from "pinia";
import { ref } from "vue";

export const useChatStore = defineStore("chatStore", () => {
  var callsign_list = ref();
  var sorted_chat_list = ref();
  var newChatCallsign = ref();
  var newChatMessage = ref();
  var totalUnreadMessages = ref(0);

  /* ------------------------------------------------ */
  // Scroll to bottom functions
  const scrollTrigger = ref(0);

  function triggerScrollToBottom() {
    scrollTrigger.value++;
  }

  var selectedCallsign = ref();

  // we need a default value in our ref because of our message info modal

  var inputText = ref("");

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
    totalUnreadMessages,
    inputText,
    callsign_list,
    sorted_chat_list,
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
