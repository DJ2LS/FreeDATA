<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useChatStore } from "../store/chatStore.js";
import { getBeaconDataByCallsign } from "../js/api.js";
import { startChatWithNewStation } from "../js/chatHandler";

import { ref, computed } from "vue";


const chat = useChatStore(pinia);

function chatSelected(callsign) {
  chat.selectedCallsign = callsign.toUpperCase();
  // scroll message container to bottom
  var messageBody = document.getElementById("message-container");
  if (messageBody != null) {
    // needs sensible defaults
    messageBody.scrollTop = messageBody.scrollHeight - messageBody.clientHeight;
  }

  processBeaconData(callsign);
}

async function processBeaconData(callsign) {
  // fetch beacon data when selecting a callsign
  let beacons = await getBeaconDataByCallsign(callsign);
  chat.beaconLabelArray = beacons.map((entry) => entry.timestamp);
  chat.beaconDataArray = beacons.map((entry) => entry.snr);
}

function getDateTime(timestamp) {
  let date = new Date(timestamp);
  let hours = date.getHours().toString().padStart(2, "0");
  let minutes = date.getMinutes().toString().padStart(2, "0");
  let seconds = date.getSeconds().toString().padStart(2, "0");
  return `${hours}:${minutes}`;
}

const newChatCall = ref(null);

function newChat() {
  let callsign = this.newChatCall.value;
  callsign = callsign.toUpperCase().trim();
  if (callsign === "") return;
  //startChatWithNewStation(callsign);
  //updateAllChat(false);
  this.newChatCall.value = "";
}


</script>
<template>

<nav class="navbar sticky-top bg-body-tertiary shadow">

<button
            class="btn btn-outline-primary w-100"
            data-bs-target="#newChatModal"
            data-bs-toggle="modal"
          >
            <i class="bi bi-pencil-square"> Start a new chat</i>
          </button>


</nav>


  <div
    class="list-group bg-body-tertiary m-0 p-1"
    id="chat-list-tab"
    role="chat-tablist"
  >
    <template
      v-for="(details, callsign, key) in chat.callsign_list"
      :key="callsign"
    >
      <a
        class="list-group-item list-group-item-action list-group-item-secondary rounded-2 border-0 mb-2"
        :class="{ active: key == 0 }"
        :id="`list-chat-list-${callsign}`"
        data-bs-toggle="list"
        :href="`#list-${callsign}-messages`"
        role="tab"
        aria-controls="list-{{callsign}}-messages"
        @click="chatSelected(callsign)"
      >
        <div class="row">
          <div class="col-9 text-truncate">
            <strong>{{ callsign }}</strong>
            <br />
            <small> {{ details.body }} </small>
          </div>
          <div class="col-3">
            <small> {{ getDateTime(details.timestamp) }} </small>
            <button
              class="btn btn-sm btn-outline-secondary ms-2 border-0"
              data-bs-target="#deleteChatModal"
              data-bs-toggle="modal"
              @click="chatSelected(callsign)"
            >
              <i class="bi bi-three-dots-vertical"></i>
            </button>
          </div>
        </div>
      </a>
    </template>
  </div>
</template>
