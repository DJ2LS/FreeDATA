<template>
  <div class="tab-content p-3" id="nav-tabContent-chat-messages">
    <template v-for="(details, callsign, key) in chat.callsign_list" :key="callsign">
      <div
        class="tab-pane fade show"
        :class="{ active: key === 0 }"
        :id="`list-${callsign}-messages`"
        role="tabpanel"
        :aria-labelledby="`list-chat-list-${callsign}`"
      >
        <template v-for="item in chat.sorted_chat_list[callsign]" :key="item.timestamp">
          <div v-if="prevChatMessageDay !== getDateTime(item.timestamp)">
            <div class="separator my-2">
              {{ (prevChatMessageDay = getDateTime(item.timestamp)) }}
            </div>
          </div>

          <div v-if="item.direction === 'transmit'">
            <SentMessage :message="item" />
          </div>

          <div v-else-if="item.direction === 'receive'">
            <ReceivedMessage :message="item" />
          </div>
        </template>
      </div>
    </template>
  </div>
</template>

<script>
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
import { useChatStore } from '../store/chatStore.js';
import SentMessage from './chat_messages_sent.vue';
import ReceivedMessage from './chat_messages_received.vue';

setActivePinia(pinia);

const chat = useChatStore(pinia);

let prevChatMessageDay = '';

function getDateTime(timestampRaw) {
  const date = new Date(timestampRaw * 1000); // Assuming timestamp is in seconds
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export default {
  components: {
    SentMessage,
    ReceivedMessage
  },
  setup() {
    return { chat, prevChatMessageDay, getDateTime };
  }
};
</script>

<style>
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
