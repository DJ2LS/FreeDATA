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
          :key="item.id || `${item.timestamp}-${index}`"
        >
          <!-- Date Separator -->
          <div v-if="showDateSeparator(index, item.timestamp * 1000, messages)">
            <div class="d-flex align-items-center my-3">
              <hr class="flex-grow-1" />
              <span class="mx-2 text-muted">{{ getDate(item.timestamp * 1000) }}</span>
              <hr class="flex-grow-1" />
            </div>
          </div>

          <!-- Message Components -->
          <div v-if="item.direction === 'transmit'">
            <component
              :is="item.msg_type === 'METAR' ? 'MetarSentBroadcast' : 'SentBroadcast'"
              :message="item"
            />
          </div>

          <!-- Empfangen: METAR spezialisiert, sonst Standard -->
          <div v-else-if="item.direction === 'receive'">
            <component
              :is="item.msg_type === 'METAR' ? 'MetarReceivedBroadcast' : 'ReceivedBroadcast'"
              :message="item"
            />
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
import MetarReceivedBroadcast from './broadcast_message_metar_received.vue';
import MetarSentBroadcast from './broadcast_message_metar_sent.vue';

setActivePinia(pinia);
const broadcast = useBroadcastStore(pinia);

function getDate(timestampRaw) {
  const date = new Date(timestampRaw);
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

function showDateSeparator(index, currentTimestamp, messages) {
  if (index === 0) return true;
  const previousTimestamp = messages[index - 1].timestamp * 1000;
  return getDate(currentTimestamp) !== getDate(previousTimestamp);
}

export default {
  name: 'BroadcastMessages',
  components: {
    SentBroadcast,
    ReceivedBroadcast,
    MetarReceivedBroadcast,
    MetarSentBroadcast,
  },
  setup() {
    return { broadcast, getDate, showDateSeparator };
  },
};
</script>
