<template>
  <!-- Navbar for starting a new chat -->
  <nav class="navbar sticky-top bg-body-tertiary border-bottom p-1">
    <button
      class="btn btn-outline-primary w-100"
      data-bs-target="#newChatModal"
      data-bs-toggle="modal"
      @click="startNewChat"
    >
      <i class="bi bi-pencil-square" /> {{ $t('chat.startnewchat') }}
    </button>
  </nav>

  <!-- List of chats -->
  <div
    id="chat-list-tab"
    class="list-group m-0 p-1"
    role="tablist"
  >
    <!-- Show loading message if we're waiting -->
    <div
      v-if="chat.loading"
      class="text-center p-2"
    >
      <div
        class="spinner-border"
        role="status"
      >
        <span class="visually-hidden">{{ $t('chat.loadingMessages') }}</span>
      </div>
    </div>

    <!-- Show 'no conversations' message if not loading and no conversations exist -->
    <div
      v-else-if="!chat.callsign_list || Object.keys(chat.callsign_list).length === 0"
      class="text-center p-2"
    >
      {{ $t('chat.noConversations') }}
    </div>


    <template
      v-for="(details, callsign) in chat.callsign_list"
      :key="callsign"
    >
      <a
        :id="`list-chat-list-${callsign}`"
        class="list-group-item list-group-item-action list-group-item-secondary rounded-2 border-0 mb-2"
        data-bs-toggle="list"
        :href="`#list-${callsign}-messages`"
        role="tab"
        :aria-controls="`list-${callsign}-messages`"
        @click="chatSelected(callsign)"
      >
        <div class="row">
          <div class="col-7 text-truncate">
            <strong>{{ callsign }}</strong>
            <span
              v-if="details.unread_messages > 0"
              class="ms-1 badge bg-danger"
            >
              {{ details.unread_messages }} {{ $t('chat.new') }}
            </span>
            <br>
            <small>{{ sanitizeBody(details.body.substring(0, 35) + '...') || "\u003Cfile\u003E" }}</small>

          </div>
          <div class="col-5 text-end">
            <small>{{ getDateTime(details.timestamp) }}</small>

          </div>
        </div>
      </a>
    </template>
  </div>
</template>

<script>
import DOMPurify from 'dompurify';
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
import { useChatStore } from '../store/chatStore.js';
import { getBeaconDataByCallsign, setFreedataMessageAsRead, getFreedataMessages } from '../js/api.js';
import { ref } from 'vue';
import { useIsMobile } from '../js/mobile_devices.js';
const { isMobile } = useIsMobile(720);


setActivePinia(pinia);

const chat = useChatStore(pinia);
const newChatCall = ref(null);

function chatSelected(callsign) {
  chat.selectedCallsign = callsign.toUpperCase();
  chat.triggerScrollToBottom();
  processBeaconData(callsign);
  setMessagesAsRead(callsign);
}


import { watch } from 'vue';

watch(isMobile, (newVal) => {
  console.log("isMobile changed to:", newVal);
});



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

  const now = new Date();
  const isSameDay = date.getDate() === now.getDate() &&
                    date.getMonth() === now.getMonth() &&
                    date.getFullYear() === now.getFullYear();

  if (isSameDay) {
    // Use the browser's locale to format time only
    return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  } else {
    // Use the browser's locale to format both date and time
    const datePart = date.toLocaleDateString(undefined, { day: '2-digit', month: '2-digit', year: 'numeric' });
    //const timePart = date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
    //return `${datePart} ${timePart}`;
    return `${datePart}`;
  }
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

function sanitizeBody(body) {
  return body ? DOMPurify.sanitize(body, { ALLOWED_TAGS: [] }) : null;
}

export default {
  setup() {
    return { chat, newChatCall, chatSelected, setMessagesAsRead, processBeaconData, getDateTime, newChat, startNewChat, sanitizeBody };
  }
};
</script>
