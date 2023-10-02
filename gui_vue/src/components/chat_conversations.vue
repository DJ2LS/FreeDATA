<script setup lang="ts">


import {saveSettingsToFile} from '../js/settingsHandler';

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);
import {deleteChatByCallsign} from '../js/chatHandler'

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);

import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);

function deleteChat(callsign){
 deleteChatByCallsign(callsign)
}


import chat_conversations_entry from './chat_conversations_entry.vue'

function chatSelected(callsign){

    chat.selectedCallsign = callsign.toUpperCase()

  // scroll message container to bottom
  var messageBody = document.getElementById("message-container");
  messageBody.scrollTop = messageBody.scrollHeight - messageBody.clientHeight;

    console.log(chat.sorted_beacon_list[chat.selectedCallsign])
    console.log(chat.selectedCallsign)
    try{
        chat.beaconLabelArray = Object.values(chat.sorted_beacon_list[chat.selectedCallsign].timestamp)
        chat.beaconDataArray = Object.values(chat.sorted_beacon_list[chat.selectedCallsign].snr)
    } catch(e){
        console.log("beacon data not fetched: " + e)
        chat.beaconLabelArray = []
        chat.beaconDataArray = []
    }

    console.log(chat.beaconDataArray)



}




</script>
<template>

<div class="list-group m-0 p-0" id="chat-list-tab" role="chat-tablist">
       <template  v-for="(item, key) in chat.callsign_list" :key="item.dxcallsign">
           <a class="list-group-item list-group-item-action border-0 border-bottom rounded-0" :class="{ active: key==0 }" :id="`list-chat-list-${item}`" data-bs-toggle="list" :href="`#list-${item}-messages`" role="tab" aria-controls="list-{{item}}-messages" @click="chatSelected(item)">
                <div class="row">
                    <div class="col-9">{{item}}</div>
                    <div class="col-3">

                    <button class="btn btn-sm btn-outline-danger ms-2" @click="deleteChat(item)"><i class="bi bi-trash"></i></button>




                    </div>
                </div>
            </a>
        </template>
    <!--<chat_conversations_entry/>-->
</div>



</template>
