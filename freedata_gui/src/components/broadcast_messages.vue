<template>
  <div
    id="nav-tabContent-broadcast-messages"
    class="tab-content p-3"
  >
    <template
      v-for="(messages, domain) in broadcast.domainBroadcasts"
      :key="domain"
    >
      <div
        :id="`list-${domain}-messages`"
        class="tab-pane fade"
        :class="{ 'active show': broadcast.selectedDomain === domain }"
        role="tabpanel"
        :aria-labelledby="`list-domain-list-${domain}`"
      >
        <template
          v-for="(item, index) in messages"
          :key="item.timestamp"
        >
          <!-- Date Separator -->
          <div v-if="showDateSeparator(index, item.timestamp, messages)">
            <div class="d-flex align-items-center my-3">
              <hr class="flex-grow-1">
              <span class="mx-2 text-muted">{{ getDate(item.timestamp) }}</span>
              <hr class="flex-grow-1">
            </div>
          </div>

          <!-- Message Components -->
          <div v-if="item.direction === 'transmit'">
            <SentBroadcast :message="item" />
          </div>

          <div v-else-if="item.direction === 'receive'">
            <ReceivedBroadcast :message="item" />
          </div>

        </template>
      </div>
    </template>
  </div>
</template>




<script>
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
import { useBroadcastStore } from '../store/broadcastStore.js';
import SentBroadcast from './broadcast_message_sent.vue';
import ReceivedBroadcast from './broadcast_message_received.vue';


setActivePinia(pinia);

const broadcast = useBroadcastStore(pinia);

function getDate(timestampRaw) {
  const date = new Date(timestampRaw);
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
}

function showDateSeparator(index, currentTimestamp, messages) {
  if (index === 0) return true;
  const previousTimestamp = messages[index - 1].timestamp;
  return getDate(currentTimestamp) !== getDate(previousTimestamp);
}

export default {
  components: {
    SentBroadcast,
    ReceivedBroadcast
  },
  setup() {
    return { broadcast, getDate, showDateSeparator };
  }
};




</script>
