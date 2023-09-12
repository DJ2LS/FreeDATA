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



    var callsign_list = ref()
    var sorted_chat_list = ref()
    var unsorted_chat_list = ref([])


  return {chat_filter, callsign_list, sorted_chat_list, unsorted_chat_list  };
});
