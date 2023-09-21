import { defineStore } from 'pinia'
import { ref, computed } from 'vue';

export const useChatStore = defineStore('chatStore', () => {
    var chat_filter = ref([
      { type: "newchat" },
      { type: "received" },
      { type: "transmit" },
      { type: "ping-ack" },
      { type: "broadcast_received" },
      { type: "broadcast_transmit" },
      //{ type: "request" },
      //{ type: "response" },
    ])


    var selectedCallsign = ref()
    var inputText = ref()
    var inputFile = ref()
    var inputFileName = ref()
    var inputFileType = ref()
    var inputFileSize = ref()

    var callsign_list = ref()
    var sorted_chat_list = ref()
    var unsorted_chat_list = ref([])

    var chartSpeedPER0 = ref()
    var chartSpeedPER25 = ref()
    var chartSpeedPER75 = ref()


  return {selectedCallsign, inputText, chat_filter, callsign_list, sorted_chat_list, unsorted_chat_list, inputFileName, inputFileSize, inputFileType, inputFile, chartSpeedPER0, chartSpeedPER25, chartSpeedPER75  };
});
