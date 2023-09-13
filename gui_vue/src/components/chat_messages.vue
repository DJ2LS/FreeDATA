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



</script>

<template>
 <div class="tab-content" id="nav-tabContent-chat-messages">
     <template v-for="callsign in chat.callsign_list">


          <div class="tab-pane fade" :id="`list-${callsign}-messages`" role="tabpanel" :aria-labelledby="`list-chat-list-${callsign}`">


          <template v-for="item in chat.sorted_chat_list[callsign]" :key="item._id">
              <div v-if="item.type === 'transmit'">
                <!--Sending message: {{ item.msg }} -->
                <sent-message :message="item" />
              </div>
              <div v-else-if="item.type === 'received'">
                <!--Received message: {{ item.msg }}-->
                <received-message :message="item" />

              </div>



            </template>






          </div>
    </template>

  </div>
</template>
