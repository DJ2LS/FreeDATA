<script setup lang="ts">
import { saveSettingsToFile } from "../js/settingsHandler";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { useChatStore } from "../store/chatStore.js";
const chat = useChatStore(pinia);

import {getNewMessagesByDXCallsign, resetIsNewMessage} from '../js/chatHandler'


import chat_conversations_entry from "./chat_conversations_entry.vue";


function chatSelected(callsign) {
  chat.selectedCallsign = callsign.toUpperCase();

  // scroll message container to bottom
  var messageBody = document.getElementById("message-container");
  if (messageBody != null ) {
    // needs sensible defaults
    messageBody.scrollTop = messageBody.scrollHeight - messageBody.clientHeight;
  }

  if (getNewMessagesByDXCallsign(callsign)[1] > 0){
        let messageArray = getNewMessagesByDXCallsign(callsign)[2]
        console.log(messageArray)

        for (const key in messageArray){
                resetIsNewMessage(messageArray[key].uuid, false)
            }
  }

  try {
    chat.beaconLabelArray = Object.values(
      chat.sorted_beacon_list[chat.selectedCallsign].timestamp,
    );
    chat.beaconDataArray = Object.values(
      chat.sorted_beacon_list[chat.selectedCallsign].snr,
    );
  } catch (e) {
    console.log("beacon data not fetched: " + e);
    chat.beaconLabelArray = [];
    chat.beaconDataArray = [];
  }
}
</script>
<template>
  <div class="list-group m-0 p-0" id="chat-list-tab" role="chat-tablist">
    <template v-for="(item, key) in chat.callsign_list" :key="item.dxcallsign">
      <a
        class="list-group-item list-group-item-action border-0 border-bottom rounded-0"
        :class="{ active: key == 0}"
        :id="`list-chat-list-${item}`"
        data-bs-toggle="list"
        :href="`#list-${item}-messages`"
        role="tab"
        aria-controls="list-{{item}}-messages"
        @click="chatSelected(item)"
      >



        <div class="row">
          <div class="col-9">{{ item }}
            <span class="badge rounded-pill bg-danger" v-if="getNewMessagesByDXCallsign(item)[1] > 0">
               {{getNewMessagesByDXCallsign(item)[1]}} new messages
            </span>

          </div>
          <div class="col-3">
            <button
              class="btn btn-sm btn-outline-secondary ms-2 border-0"
              data-bs-target="#deleteChatModal"
              data-bs-toggle="modal"
              @click="chatSelected(item)"
            >
              <i class="bi bi-three-dots-vertical"></i>
            </button>
          </div>
        </div>
      </a>
    </template>
    <!--<chat_conversations_entry/>-->
  </div>
</template>
