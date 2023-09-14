<script setup lang="ts">


import {saveSettingsToFile} from '../js/settingsHandler';

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);

import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);

import SentMessage from './chat_messages_sent.vue'; // Import the chat_messages_sent component
import ReceivedMessage from './chat_messages_received.vue'; // Import the chat_messages_sent component

//helper function for saving the last messages day for disaplying the day based divider
var prevChatMessageDay = ''

function getDateTime(timestampRaw){
    var datetime = new Date(timestampRaw * 1000).toLocaleString(
          navigator.language,
          {
            hourCycle: "h23",
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
          },
        );
return datetime
}



</script>

<template>
 <div class="tab-content" id="nav-tabContent-chat-messages">
     <template v-for="(callsign, key) in chat.callsign_list">
          <div class="tab-pane fade show" :class="{ active: key==0 }" :id="`list-${callsign}-messages`" role="tabpanel" :aria-labelledby="`list-chat-list-${callsign}`">
          <template v-for="item in chat.sorted_chat_list[callsign]" :key="item._id">

          <div v-if="prevChatMessageDay !== getDateTime(item.timestamp)">
                <div class="separator my-2">{{prevChatMessageDay = getDateTime(item.timestamp)}}</div>
            </div>

              <div v-if="item.type === 'transmit'">
                <sent-message :message="item" />
              </div>
              <div v-else-if="item.type === 'received'">
                <received-message :message="item" />

              </div>

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
}

.separator::before,
.separator::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid #000;
}

.separator:not(:empty)::before {
  margin-right: .25em;
}

.separator:not(:empty)::after {
  margin-left: .25em;
}
</style>