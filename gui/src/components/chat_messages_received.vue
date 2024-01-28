<template>

  <div class="row justify-content-start mb-2">
    <div :class="messageWidthClass">
      <div class="card bg-light border-0 text-dark">
        <div class="card-header" v-if="getFileContent['filesize'] !== 0">
          <p class="card-text">
            {{ getFileContent["filename"] }} |
            {{ getFileContent["filesize"] }} Bytes |
            {{ getFileContent["filetype"] }}
          </p>
        </div>

        <div class="card-body">
          <p class="card-text">{{ message.body }}</p>
        </div>

        <div class="card-footer p-0 bg-light border-top-0">
          <p class="text-muted p-0 m-0 me-1 text-end">{{ getDateTime }}</p>
          <!-- Display formatted timestamp in card-footer -->
        </div>
      </div>
    </div>

    <!-- Delete button outside of the card -->
    <div class="col-auto">
      <button
        class="btn btn-outline-secondary border-0 me-1"
        @click="showMessageInfo"
        data-bs-target="#messageInfoModal"
        data-bs-toggle="modal"
      >
        <i class="bi bi-info-circle"></i>
      </button>

      <button
        v-if="getFileContent['filesize'] !== 0"
        class="btn btn-outline-secondary border-0 me-1"
        @click="downloadAttachment"
      >
        <i class="bi bi-download"></i>
      </button>

      <button class="btn btn-outline-secondary border-0" @click="deleteMessage">
        <i class="bi bi-trash"></i>
      </button>
    </div>
  </div>
</template>

<script>
import {
  deleteMessageFromDB,
  requestMessageInfo,
  getMessageAttachment,
} from "../js/messagesHandler";
import { atob_FD } from "../js/freedata";

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
    showMessageInfo() {
      requestMessageInfo(this.message.id);
      //let infoModal = Modal.getOrCreateInstance(document.getElementById('messageInfoModal'))
      //console.log(this.infoModal)
      //this.infoModal.show()
    },
    deleteMessage() {
      deleteMessageFromDB(this.message.id);
    },
    async downloadAttachment() {
      try {
        // reset file store
        chat.downloadFileFromDB = [];

        const attachment = await getMessageAttachment(this.message.id);
        const blob = new Blob([atob_FD(attachment[2])], {
          type: `${attachment[1]};charset=utf-8`,
        });
        window.focus();
        saveAs(blob, attachment[0]);
      } catch (error) {
        console.error("Failed to download attachment:", error);
      }
    },
  },
  computed: {
    getFileContent() {
    
      if(this.message.attachments.length <= 0){
        return { filename: '', filesize: 0, filetype: '' };
      }
      
      try {
        var filename = Object.keys(this.message._attachments)[0];
        var filesize = this.message._attachments[filename]["length"];
        var filetype = filename.split(".")[1];

        return { filename: filename, filesize: filesize, filetype: filetype };
      } catch (e) {
        console.log("file not loaded from database - empty?");
        // we are only checking against filesize for displaying attachments
        return { filesize: 0 };
      }
    },
    messageWidthClass() {
      // Calculate a Bootstrap grid class based on message length
      // Adjust the logic as needed to fit your requirements
      if (this.message.body.length <= 50) {
        return "col-4";
      } else if (this.message.body.length <= 100) {
        return "col-6";
      } else {
        return "col-9";
      }
    },

    getDateTime() {

        let date = new Date(this.message.timestamp);
        let hours = date.getHours().toString().padStart(2, '0');
        let minutes = date.getMinutes().toString().padStart(2, '0');
        let seconds = date.getSeconds().toString().padStart(2, '0');
        return `${hours}:${minutes}:${seconds}`;
    },
  },
};
</script>
