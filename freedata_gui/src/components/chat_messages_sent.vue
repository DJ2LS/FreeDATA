<template>
  <div class="row justify-content-end mb-2">
    <!-- control area -->
    <div class="col-auto p-0 m-0">
      <button
        class="btn btn-outline-secondary border-0 me-1"
        @click="repeatMessage"
      >
        <i class="bi bi-arrow-repeat"></i>
      </button>

      <button

        class="btn btn-outline-secondary border-0 me-1"
        @click="showMessageInfo"
        data-bs-target="#messageInfoModal"
        data-bs-toggle="modal"
      >
        <i class="bi bi-info-circle"></i>
      </button>

      <button class="btn btn-outline-secondary border-0" @click="deleteMessage">
        <i class="bi bi-trash"></i>
      </button>
    </div>
    <!-- message area -->
    <div :class="messageWidthClass">
      <div class="card bg-secondary text-white">
        <div
          v-for="attachment in message.attachments"
          :key="attachment.id"
          class="card-header"
        >
          <div class="btn-group w-100" role="group">
            <button class="btn btn-light text-truncate" disabled>
              {{ attachment.name }}
            </button>
            <button
              @click="
                downloadAttachment(attachment.hash_sha512, attachment.name)
              "
              class="btn btn-light w-25"
            >
              <i class="bi bi-download strong"></i>
            </button>
          </div>
        </div>

        <div class="card-body">
          <p class="card-text text-break">{{ message.body }}</p>
        </div>

        <div class="card-footer p-0 bg-secondary border-top-0">
          <p class="text p-0 m-0 me-1 text-end">
            <span class="badge badge-primary mr-2" :class="{
                'bg-danger': message.status == 'failed',
                'bg-primary': message.status == 'transmitting',
                'bg-secondary': message.status == 'transmitted',
              }"
            >
              {{ message.status }}
            </span>
            | attempt: {{ message.attempt + 1 }} | {{ getDateTime }}
          </p>
        </div>

        <div
          class="card-footer p-0 border-top-0"
          v-if="message.percent < 100 || message.status === 'failed'"
        >
          <div
            class="progress rounded-0 rounded-bottom"
            hidden
            :class="{
              'bg-danger': message.status == 'failed',
              'bg-primary': message.status == 'transmitting',
              'bg-secondary': message.status == 'transmitted',
            }"
          >
            <div
              class="progress-bar progress-bar-striped overflow-visible"
              role="progressbar"
              :style="{ width: message.percent + '%', height: '10px' }"
              :aria-valuenow="message.percent"
              aria-valuemin="0"
              aria-valuemax="100"
            >
              {{ message.percent }} % with {{ message.bytesperminute }} bpm (
              {{ message.status }} )
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  repeatMessageTransmission,
  deleteMessageFromDB,
  requestMessageInfo,
  getMessageAttachment,
} from "../js/messagesHandler";

// pinia store setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useChatStore } from '../store/chatStore.js';
const chatStore = useChatStore(pinia);

export default {
  props: {
    message: Object,
  },

  methods: {
    repeatMessage() {
      repeatMessageTransmission(this.message.id);
    },

    deleteMessage() {
      deleteMessageFromDB(this.message.id);
    },

    showMessageInfo() {
      chatStore.messageInfoById = requestMessageInfo(this.message.id);

    },

    async downloadAttachment(hash_sha512, fileName) {
      try {
        const jsondata = await getMessageAttachment(hash_sha512);
        const byteCharacters = atob(jsondata.data);
        const byteArrays = [];

        for (let offset = 0; offset < byteCharacters.length; offset += 512) {
          const slice = byteCharacters.slice(offset, offset + 512);
          const byteNumbers = new Array(slice.length);
          for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
          }
          const byteArray = new Uint8Array(byteNumbers);
          byteArrays.push(byteArray);
        }

        const blob = new Blob(byteArrays, { type: jsondata.type });
        const url = URL.createObjectURL(blob);

        // Creating a temporary anchor element to download the file
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = fileName;
        document.body.appendChild(anchor);
        anchor.click();

        // Cleanup
        document.body.removeChild(anchor);
        URL.revokeObjectURL(url);
      } catch (error) {
        console.error("Failed to download the attachment:", error);
      }
    },
  },

  computed: {
    messageWidthClass() {
      // Calculate a Bootstrap grid class based on message length
      if (this.message.body.length <= 50) {
        return "col-4";
      } else if (this.message.body.length <= 100) {
        return "col-6";
      } else {
        return "col-8";
      }
    },

    getDateTime() {
      let date = new Date(this.message.timestamp);
      let hours = date.getHours().toString().padStart(2, "0");
      let minutes = date.getMinutes().toString().padStart(2, "0");
      let seconds = date.getSeconds().toString().padStart(2, "0");
      return `${hours}:${minutes}:${seconds}`;
    },
  },
};
</script>
