<template>
  <div class="row justify-content-start mb-2">
    <div :class="messageWidthClass">
      <div class="card border rounded-top">
        <div class="card-body">
          <p
            class="card-text text-break"
            v-html="parsedMessageBody"
          />
        </div>

        <div class="card-footer p-0 border-top-0">
          <p class="p-0 m-0 me-1 text-end">
            <span class="mr-2">{{ getDateTime }} UTC</span>
          </p>
        </div>
      </div>
    </div>

    <!-- Info-Button -->
    <div class="col-auto">
      <button
        class="btn btn-outline-secondary border-0 me-1"
        data-bs-target="#broadcastMessageInfoModal"
        data-bs-toggle="modal"
        @click="showMessageInfo"
      >
        <i class="bi bi-info-circle" />
      </button>

      <button
        class="btn btn-outline-secondary border-0"
        @click="sendADIF"
      >
        {{ $t('chat.adif') }}
      </button>

      <button
        class="btn btn-outline-secondary border-0"
        @click="deleteMessage"
      >
        <i class="bi bi-trash" />
      </button>


    </div>
  </div>
</template>

<script>
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import {deleteBroadcastMessageFromDB, sendBroadcastADIFviaUDP} from "@/js/broadcastsHandler";

export default {
  props: {
    message: Object,
  },

  computed: {
    messageWidthClass() {
      const len = this.message?.payload_data?.final?.length || 0;
      if (len <= 50) return "col-6";
      else if (len <= 100) return "col-7";
      else return "col-9";
    },

    getDateTime() {
      const date = new Date(this.message.timestamp);
      return date.toISOString().split("T")[1].split(".")[0]; // HH:MM:SS
    },

    sendADIF() {
      sendBroadcastADIFviaUDP(this.message.id);
    },

    deleteMessage() {
      deleteBroadcastMessageFromDB(this.message.id);
    },

    parsedMessageBody() {
      let body = "";
      if (this.message.payload_data?.final) {
        try {
          body = atob(this.message.payload_data.final);
        } catch (e) {
          body = "<decode error>";
        }
      }

      const html = DOMPurify.sanitize(marked.parse(body));
      const temp = document.createElement("div");
      temp.innerHTML = html;
      temp.querySelectorAll("a").forEach(link => {
        link.setAttribute("target", "_blank");
        link.setAttribute("rel", "noopener noreferrer");
      });

      return temp.innerHTML;
    },
  },

  methods: {
    showMessageInfo() {
      this.$emit("show-info", this.message);
    },
  },
};
</script>
