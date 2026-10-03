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

          <p class="text p-0 m-0 mb-1 me-1 text-end">
          <span class="badge text-bg-secondary">{{ this.message.origin }}</span>
          | <span class="badge text-bg-secondary">{{ this.message.msg_type }}</span>
          | <span class="badge text-bg-secondary">{{ this.message.priority }}</span>
          | <span class="mr-2">{{ getDateTime }} UTC</span>

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
        @click="showBroadcastMessageInfo"
      >
        <i class="bi bi-info-circle" />
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
import {deleteBroadcastMessageFromDB, decodeBroadcastText} from "@/js/broadcastsHandler";

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
import { useBroadcastStore } from '../store/broadcastStore.js';
setActivePinia(pinia);
const broadcast = useBroadcastStore(pinia);

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
      const date = new Date(this.message.timestamp * 1000);
      return date.toISOString().split("T")[1].split(".")[0]; // HH:MM:SS
    },

    parsedMessageBody() {
      let body = " <p class=\"card-text placeholder-glow\">\n" +
          "      <span class=\"placeholder col-7\"></span>\n" +
          "      <span class=\"placeholder col-4\"></span>\n" +
          "    </p>";
      if (this.message.payload_data?.final) {
        try {
          body = decodeBroadcastText(this.message.payload_data.final);
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
    showBroadcastMessageInfo() {
      console.log(this.message);
      broadcast.selectedMessage = this.message;
    },

    async deleteMessage() {
      try {
        await deleteBroadcastMessageFromDB(this.message.id);
      } catch (e) {
        console.error("Delete failed:", e);
      }
    },
  },
};
</script>
