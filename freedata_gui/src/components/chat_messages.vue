<template>
  <div class="tab-content p-3" id="nav-tabContent-chat-messages">
    <template v-for="(details, callsign) in chat.callsign_list" :key="callsign">
      <div
        class="tab-pane fade"

        :class="{ 'active show': chat.selectedCallsign === callsign }"
        :id="`list-${callsign}-messages`"
        role="tabpanel"
        :aria-labelledby="`list-chat-list-${callsign}`"
      >
        <template v-for="(item, index) in chat.sorted_chat_list[callsign]" :key="item.timestamp">
          <!-- Date Separator -->
          <div v-if="showDateSeparator(index, item.timestamp, chat.sorted_chat_list[callsign])">
            <div class="d-flex align-items-center my-3">
              <hr class="flex-grow-1" />
              <span class="mx-2 text-muted">{{ getDate(item.timestamp) }}</span>
              <hr class="flex-grow-1" />
            </div>
          </div>

          <!-- Message Components -->
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

function getDate(timestampRaw) {
  // Parsing the timestamp and returning the date part as YYYY-MM-DD
  const date = new Date(timestampRaw);
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function showDateSeparator(index, currentTimestamp, messages) {
  if (index === 0) return true; // Always show the date for the first message

  const previousTimestamp = messages[index - 1].timestamp;
  return getDate(currentTimestamp) !== getDate(previousTimestamp);
}

export default {
  components: {
    SentMessage,
    ReceivedMessage
  },
  setup() {
    return { chat, getDate, showDateSeparator };
  }
};
</script>
