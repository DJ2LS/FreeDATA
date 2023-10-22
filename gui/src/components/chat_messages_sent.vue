<template>
  <div class="row justify-content-end mb-2">
    <!-- control area -->
    <div class="col-auto p-0 m-0">
      <button
        v-if="getFileContent['filesize'] !== 0"
        class="btn btn-outline-secondary border-0 me-1"
        @click="downloadAttachment"
      >
        <i class="bi bi-download"></i>
      </button>

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
      <div class="card bg-primary text-white">
        <div class="card-header" v-if="getFileContent['filesize'] !== 0">
          <p class="card-text">
            {{ getFileContent["filename"] }} |
            {{ getFileContent["filesize"] }} Bytes |
            {{ getFileContent["filetype"] }}
          </p>
        </div>

        <div class="card-body">
          <p class="card-text">{{ message.msg }}</p>
        </div>

        <div class="card-footer p-0 bg-primary border-top-0">
          <p class="text p-0 m-0 me-1 text-end">{{ getDateTime }}</p>
          <!-- Display formatted timestamp in card-footer -->
        </div>

        <div class="card-footer p-0 border-top-0" v-if="message.percent < 100">
          <div
            class="progress bg-secondary rounded-0 rounded-bottom"
            :style="{ height: '10px' }"
          >
            <div
              class="progress-bar progress-bar-striped overflow-visible"
              role="progressbar"
              :style="{ width: message.percent + '%', height: '10px' }"
              :aria-valuenow="message.percent"
              aria-valuemin="0"
              aria-valuemax="100"
            >
              {{ message.percent }} % with {{ message.bytesperminute }} bpm
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from "bootstrap";
import { onMounted, ref } from "vue";
import { atob_FD } from "../js/freedata";

import {
  repeatMessageTransmission,
  deleteMessageFromDB,
  requestMessageInfo,
  getMessageAttachment,
} from "../js/chatHandler";

// pinia store setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
import { saveAs } from "file-saver";

import { useChatStore } from "../store/chatStore.js";
const chat = useChatStore(pinia);

export default {
  props: {
    message: Object,
  },

  methods: {
    async downloadAttachment() {
      try {
        // reset file store
        chat.downloadFileFromDB = [];

        const attachment = await getMessageAttachment(this.message._id);
        const blob = new Blob([atob_FD(attachment[2])], {
          type: `${attachment[1]};charset=utf-8`,
        });
        saveAs(blob, attachment[0]);
      } catch (error) {
        console.error("Failed to download attachment:", error);
      }
    },
  },
  computed: {
    getFileContent() {
      var filename = Object.keys(this.message._attachments)[0];
      var filesize = this.message._attachments[filename]["length"];
      var filetype = filename.split(".")[1];

      // ensure filesize is 0 for hiding message header if no data is available
      if (
        typeof filename === "undefined" ||
        filename === "" ||
        filename === "-"
      ) {
        filesize = 0;
      }

      return { filename: filename, filesize: filesize, filetype: filetype };
    },
    messageWidthClass() {
      // Calculate a Bootstrap grid class based on message length
      // Adjust the logic as needed to fit your requirements
      if (this.message.msg.length <= 50) {
        return "col-4";
      } else if (this.message.msg.length <= 100) {
        return "col-6";
      } else {
        return "col-9";
      }
    },
    repeatMessage() {
      repeatMessageTransmission(this.message._id);
    },

    deleteMessage() {
      deleteMessageFromDB(this.message._id);
    },
    showMessageInfo() {
      requestMessageInfo(this.message._id);
      //let infoModal = Modal.getOrCreateInstance(document.getElementById('messageInfoModal'))
      //console.log(this.infoModal)
      //this.infoModal.show()
    },

    getDateTime() {
      var datetime = new Date(this.message.timestamp * 1000).toLocaleString(
        navigator.language,
        {
          hour: "2-digit",
          minute: "2-digit",
        },
      );
      return datetime;
    },
  },
};
</script>