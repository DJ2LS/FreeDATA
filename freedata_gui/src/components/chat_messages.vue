<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useChatStore } from "../store/chatStore.js";
const chat = useChatStore(pinia);

import SentMessage from "./chat_messages_sent.vue"; // Import the chat_messages_sent component
import ReceivedMessage from "./chat_messages_received.vue"; // Import the chat_messages_sent component
import ReceivedBroadcastMessage from "./chat_messages_broadcast_received.vue"; // Import the chat_messages_sent component for broadcasts
import SentBroadcastMessage from "./chat_messages_broadcast_sent.vue"; // Import the chat_messages_sent component for broadcasts

//helper function for saving the last messages day for disaplying the day based divider
var prevChatMessageDay = "";

function getDateTime(timestampRaw) {
  let date = new Date(timestampRaw);
  let year = date.getFullYear();
  let month = (date.getMonth() + 1).toString().padStart(2, "0"); // Months are zero-indexed
  let day = date.getDate().toString().padStart(2, "0");
  return `${year}-${month}-${day}`;
}
</script>

<template>
  <div class="tab-content p-3" id="nav-tabContent-chat-messages">
    <template
      v-for="(details, callsign, key) in chat.callsign_list"
      :key="callsign"
    >
      <div
        class="tab-pane fade show"
        :class="{ active: key == 0 }"
        :id="`list-${callsign}-messages`"
        role="tabpanel"
        :aria-labelledby="`list-chat-list-${callsign}`"
      >
        <template v-for="item in chat.sorted_chat_list[callsign]">
          <div v-if="prevChatMessageDay !== getDateTime(item.timestamp)">
            <div class="separator my-2">
              {{ (prevChatMessageDay = getDateTime(item.timestamp)) }}
            </div>
          </div>

          <div v-if="item.direction === 'transmit'">
            <sent-message :message="item" />
          </div>

          <div v-else-if="item.direction === 'receive'">
            <received-message :message="item" />
          </div>
          <!--
          <div v-if="item.type === 'broadcast_transmit'">
            <sent-broadcast-message :message="item" />
          </div>
          <div v-else-if="item.type === 'broadcast_received'">
            <received-broadcast-message :message="item" />
          </div>
          -->
        </template>
      </div>
    </template>
  </div>
</template>

<style>
/* https://stackoverflow.com/a/26634224 */
.separator {
  display: flex;
  align-items: center;
  text-align: center;
  color: #6c757d;
}

.separator::before,
.separator::after {
  content: "";
  flex: 1;
  border-bottom: 1px solid #adb5bd;
}

.separator:not(:empty)::before {
  margin-right: 0.25em;
}

.separator:not(:empty)::after {
  margin-left: 0.25em;
}
</style>
