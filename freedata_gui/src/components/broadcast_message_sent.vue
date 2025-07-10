<template>
  <div class="row justify-content-end mb-2 me-1">
    <!-- control area -->
    <div class="col-auto p-0 m-0">
      <!-- Info Button -->
      <button
        class="btn btn-outline-secondary border-0 me-1"
        data-bs-target="#broadcastMessageInfoModal"
        data-bs-toggle="modal"
        @click="showBroadcastMessageInfo"
      >
        <i class="bi bi-info-circle" />
      </button>

      <!-- Retransmit Button -->
      <button
        class="btn btn-outline-secondary border-0 me-1"
        @click="retransmitBroadcast"
      >
        <i class="bi bi-arrow-repeat" />
      </button>

      <!-- Delete Button -->
      <button
        class="btn btn-outline-secondary border-0"
        @click="deleteBroadcast"
      >
        <i class="bi bi-trash" />
      </button>

      <button
        class="btn btn-outline-secondary border-0"
        @click="sendADIF"
      >
        ADIF
      </button>
    </div>

    <!-- message area -->
    <div class="col-8 align-items-end">
      <div class="card">
        <div class="card-body">
          <p
            class="card-text text-break"
            v-html="parsedMessageBody"
          />
        </div>

        <div class="card-footer p-1 border-top-0">
          <p class="text p-0 m-0 mb-1 me-1 text-end">
            <span class="badge text-bg-secondary">{{ message.msg_type }}</span>
            | <span class="badge text-bg-light"> {{ timeUTC }} UTC </span>
            | <span class="badge text-bg-light"> {{ message.origin }} </span>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { marked } from "marked";
import DOMPurify from "dompurify";

import {repeatBroadcastTransmission, deleteBroadcastMessageFromDB, sendBroadcastADIFviaUDP} from "@/js/broadcastsHandler";

export default {
  props: {
    message: Object,
  },

  computed: {
    timeUTC() {
      const d = new Date(this.message.timestamp);
      return d.toISOString().split("T")[1].split(".")[0]; // HH:MM:SS
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
      temp.querySelectorAll("a").forEach((a) => {
        a.setAttribute("target", "_blank");
        a.setAttribute("rel", "noopener noreferrer");
      });

      return temp.innerHTML;
    },
  },

  methods: {
    showBroadcastMessageInfo() {
      broadcast.selectedMessage = this.message;
    },

    async retransmitBroadcast() {
      try {
        await repeatBroadcastTransmission(this.message.id);
      } catch (e) {
        console.error("Retransmit failed:", e);
      }
    },

    async deleteBroadcast() {
      try {
        await deleteBroadcastMessageFromDB(this.message.id);
      } catch (e) {
        console.error("Delete failed:", e);
      }
    },
    sendADIF() {
      sendBroadcastADIFviaUDP(this.message.id);
    },
  },
};
</script>
