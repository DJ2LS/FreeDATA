<script setup>
// @ts-nocheck
// disable typescript check because of error with beacon histogram options

import chat_conversations from "./chat_conversations.vue";
import chat_messages from "./chat_messages.vue";
import chat_new_message from "./chat_new_message.vue";

import { getStationInfoByCallsign } from "./../js/stationHandler";

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);

import { useIsMobile } from '../js/mobile_devices.js';
const { isMobile } = useIsMobile(992);


import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

import { watch, nextTick, ref } from 'vue';
import annotationPlugin from 'chartjs-plugin-annotation';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
  annotationPlugin
);



const messagesContainer = ref(null);
watch(
  () => chat.scrollTrigger,
  (newVal, oldVal) => {
    nextTick(() => {
    console.log(newVal)
    console.log(oldVal)
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
      }
    });
  }
);


function resetChat() {
  chat.selectedCallsign = null;
}




</script>

<template>
  <div class="container-fluid d-flex p-0" style="height: calc(100vh - 48px);">
  <div class="row h-100 m-0 w-100">
    <!-- Chat Conversations Sidebar -->
    <div  v-if="!isMobile || !chat.selectedCallsign" class="col-12 col-lg-3 bg-body-tertiary p-0 d-flex flex-column h-100">
      <div class="container-fluid overflow-auto p-0 flex-grow-1">
        <chat_conversations />
      </div>


    <!--  <div class="list-group overflow-auto" id="list-tab-chat" role="tablist"></div>-->


    </div>

    <!-- Chat Messages Area -->
     <!-- On mobile: Show if a chat is selected; On desktop: Always show -->
      <div
        v-if="!isMobile || chat.selectedCallsign"
        :class="isMobile ? 'col-11' : 'col-lg-9'"
        class="border-start p-0 d-flex flex-column h-100"
      >
      <!-- Top Navbar -->
      <nav class="navbar sticky-top z-0 bg-body-tertiary border-bottom p-1">
        <div class="row align-items-center">
  <!-- Column for the callsign button -->
  <div class="col-auto">

            <!-- Back Button on Mobile -->
          <button
            v-if="isMobile"
            class="btn btn-primary"
            @click="resetChat"
          >
            <i class="ms-2 me-2 bi bi-chevron-left strong"></i>
          </button>



    <button
      class="btn btn-sm btn-outline-secondary border-0"
      data-bs-target="#dxStationInfoModal"
      data-bs-toggle="modal"
      @click="getStationInfoByCallsign(chat.selectedCallsign)"
      disabled
    >
      <h4 class="p-0 m-0">{{ chat.selectedCallsign }}</h4>
    </button>
  </div>


  <!-- Column for the delete button -->
  <div class="col-auto">
    <div class="input-group mb-0 p-0">
      <button
        style="width: 100px;"
        class="btn btn-outline-secondary ms-2"
        data-bs-target="#deleteChatModal"
        data-bs-toggle="modal"
        @click="chatSelected(callsign)"
      >
        <i class="bi bi-graph-up h5"></i>
      </button>
    </div>
  </div>
</div>

      </nav>

      <!-- Chat Messages Area -->
      <div class="overflow-auto flex-grow-1" ref="messagesContainer" style="min-height: 0;">
        <div v-if="chat.selectedCallsign">
          <chat_messages />
        </div>
        <div v-else class="d-flex align-items-center justify-content-center h-100">
          <p class="text-muted">{{ $t('chat.selectChat') }}</p>
        </div>
      </div>


      <!-- New Message Input Area -->
      <div class="p-0">
        <chat_new_message />
      </div>
    </div>
  </div>
      </div>
</template>


