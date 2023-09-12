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

</script>

<template>
 <div class="tab-content" id="nav-tabContent-chat-messages">
     <template v-for="callsign in chat.callsign_list">


          <div class="tab-pane fade" :id="`list-${callsign}-messages`" role="tabpanel" :aria-labelledby="`list-chat-list-${callsign}`">{{callsign}}...

          <template v-for="item in chat.sorted_chat_list[callsign]" :key="item._id">
            {{item}}<br>

    </template>








          </div>
    </template>

  </div>
</template>
