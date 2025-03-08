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
</script>

<template>
  <div class="container-fluid d-flex p-0" style="height: calc(100vh - 48px);">
    <!-- Chat Conversations Sidebar -->
<div class="bg-body-tertiary p-0 d-flex flex-column" style="min-width: 250px; max-width: 250px;">
   <div class="container-fluid overflow-auto p-0 flex-grow-1">
      <chat_conversations />
   </div>
   <div class="list-group overflow-auto" id="list-tab-chat" role="tablist"></div>
</div>

    <!-- Chat Messages Area -->
    <div class="flex-grow-1 border-start p-0 d-flex flex-column">
      <!-- Top Navbar -->
      <nav class="navbar sticky-top z-0 bg-body-tertiary border-bottom p-1">
        <div class="row align-items-center">
  <!-- Column for the callsign button -->
  <div class="col-auto">
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
      <div class="overflow-auto flex-grow-1" ref="messagesContainer">
        <chat_messages />
      </div>

      <!-- New Message Input Area -->
      <div class="p-0">
        <chat_new_message />
      </div>
    </div>
  </div>
</template>


