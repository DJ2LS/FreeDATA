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




import chat_conversations_entry from './chat_conversations_entry.vue'

</script>

<template>

<div class="list-group" id="chat-list-tab" role="chat-tablist">

       <template v-for="(item) in chat.callsign_list" :key="item.timestamp">
          <a class="list-group-item list-group-item-action" :id="`list-chat-list-${item}`" data-bs-toggle="list" :href="`#list-${item}-messages`" role="tab" aria-controls="list-{{item}}-messages">{{item}}</a>

        </template>


    <!--<chat_conversations_entry/>-->
</div>



</template>
