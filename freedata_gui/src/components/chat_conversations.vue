<template>
  <nav class="navbar sticky-top bg-body-tertiary border-bottom p-1">
    <button
      class="btn btn-outline-primary w-100"
      data-bs-target="#newChatModal"
      data-bs-toggle="modal"
      @click="startNewChat"
    >
      <i class="bi bi-pencil-square"> Start a new chat</i>
    </button>
  </nav>

  <div
    class="list-group bg-body-tertiary m-0 p-1"
    id="chat-list-tab"
    role="chat-tablist"
  >
    <template v-for="(details, callsign, key) in chat.callsign_list" :key="callsign">
      <a
        class="list-group-item list-group-item-action list-group-item-secondary rounded-2 border-0 mb-2"
        :class="{ active: key === 0 }"
        :id="`list-chat-list-${callsign}`"
        data-bs-toggle="list"
        :href="`#list-${callsign}-messages`"
        role="tab"
        :aria-controls="`list-${callsign}-messages`"
        @click="chatSelected(callsign)"
      >
        <div class="row">
          <div class="col-9 text-truncate">
            <strong>{{ callsign }}</strong>
            <span v-if="details.unread_messages > 0" class="ms-1 badge bg-danger">
              {{ details.unread_messages }} new
            </span>
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

<script>
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
import { useChatStore } from '../store/chatStore.js';
import { getBeaconDataByCallsign, setFreedataMessageAsRead, getFreedataMessages } from '../js/api.js';
import { ref } from 'vue';

setActivePinia(pinia);

const chat = useChatStore(pinia);
const newChatCall = ref(null);

function chatSelected(callsign) {
  chat.selectedCallsign = callsign.toUpperCase();
  chat.triggerScrollToBottom();
  processBeaconData(callsign);
  setMessagesAsRead(callsign);
}

async function setMessagesAsRead(callsign) {
  const messages = chat.sorted_chat_list[callsign];
  if (messages) {
    messages.forEach((message) => {
      if (message.is_read === false) {
        setFreedataMessageAsRead(message.id);
        message.is_read = true;
      }
    });

    // Delay the execution of getFreedataMessages by 500 milliseconds
    setTimeout(() => {
      getFreedataMessages();
    }, 500);
  }
}

async function processBeaconData(callsign) {
  const beacons = await getBeaconDataByCallsign(callsign);
  chat.beaconLabelArray = beacons.map((entry) => entry.timestamp);
  chat.beaconDataArray = beacons.map((entry) => entry.snr);
}

function getDateTime(input) {
  let date;
  if (typeof input === 'number') {
    // Assuming input is a Unix timestamp in seconds
    date = new Date(input * 1000);
  } else {
    // Assuming input is an ISO 8601 formatted string
    date = new Date(input);
  }

  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  return `${hours}:${minutes}`;
}


function newChat() {
  let callsign = newChatCall.value;
  callsign = callsign.toUpperCase().trim();
  if (callsign === "") return;
  newChatCall.value = "";
}

function startNewChat() {
  chat.newChatCallsign = "";
  chat.newChatMessage = "Hi there! Nice to meet you!";
}

export default {
  setup() {
    return { chat, newChatCall, chatSelected, setMessagesAsRead, processBeaconData, getDateTime, newChat, startNewChat };
  }
};
</script>
