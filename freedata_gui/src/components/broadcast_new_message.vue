<script setup>
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useBroadcastStore } from '../store/broadcastStore.js';
import {settingsStore as settings} from '../store/settingsStore.js';
const broadcast = useBroadcastStore(pinia);


import { ref } from 'vue';
import { VuemojiPicker } from 'vuemoji-picker';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { useIsMobile } from '../js/mobile_devices.js';
import {newBroadcastMessage} from "@/js/broadcastsHandler";

const { isMobile } = useIsMobile(992);

// Refs
const inputField = ref(null);

// Emoji Handling
const handleEmojiClick = (detail) => {
  broadcast.inputText += detail.unicode;
};

// Transmit Broadcast Message
function transmitNewBroadcast() {
  if (!broadcast.selectedDomain) {
    broadcast.selectedDomain = Object.keys(broadcast.domains)[0];
  }

  broadcast.inputText = broadcast.inputText.trim();
  if (broadcast.inputText.length === 0) return;

  const sanitizedInput = DOMPurify.sanitize(marked.parse(broadcast.inputText));

  const base64data = btoa(sanitizedInput);
  const params = {
    origin: settings.remote.STATION.mycall + '-' + settings.remote.STATION.myssid,
    domain: broadcast.selectedDomain,
    gridsquare: settings.remote.STATION.mygrid,
    type: "MESSAGE",
    priority: "1",
    data: base64data
  }

  newBroadcastMessage(params)
  broadcast.inputText = ''
}

// Markdown helper
function applyMarkdown(formatType) {
  const textarea = inputField.value;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selectedText = broadcast.inputText.substring(start, end);

  if (formatType === 'bold') {
    broadcast.inputText = broadcast.inputText.substring(0, start) + `**${selectedText}**` + broadcast.inputText.substring(end);
  } else if (formatType === 'italic') {
    broadcast.inputText = broadcast.inputText.substring(0, start) + `_${selectedText}_` + broadcast.inputText.substring(end);
  } else if (formatType === 'underline') {
    broadcast.inputText = broadcast.inputText.substring(0, start) + `<u>${selectedText}</u>` + broadcast.inputText.substring(end);
  }
}
</script>

<template>
  <nav class="navbar sticky-bottom bg-body-tertiary border-top">
    <div class="container-fluid p-0">
      <div class="input-group bottom-0 ms-2">

        <!-- Emoji Button -->
        <button
          v-if="!isMobile"
          type="button"
          class="btn btn-outline-secondary border-0 rounded-pill me-1"
          data-bs-toggle="modal"
          data-bs-target="#emojiPickerModal"
          data-bs-backdrop="false"
          @click="$refs.inputField.focus()"
        >
          <i class="bi bi-emoji-smile p-0" style="font-size: 1rem" />
        </button>

        <div v-if="!isMobile" class="vr mx-2" />

        <!-- Markdown Buttons -->
        <button
          v-if="!isMobile"
          class="btn btn-outline-secondary border-0 d-md-block rounded-pill"
          @click="applyMarkdown('bold')"
        >
          <b>B</b>
        </button>
        <button
          v-if="!isMobile"
          class="btn btn-outline-secondary border-0 rounded-pill"
          @click="applyMarkdown('italic')"
        >
          <i>I</i>
        </button>
        <button
          v-if="!isMobile"
          class="btn btn-outline-secondary border-0 rounded-pill"
          @click="applyMarkdown('underline')"
        >
          <u>U</u>
        </button>

        <!-- Input Textarea -->
        <textarea
          ref="inputField"
          v-model="broadcast.inputText"
          class="form-control border rounded-pill"
          rows="1"
          :placeholder="$t('chat.entermessage_placeholder')"
          style="resize: none;"
          @keyup.enter="transmitNewBroadcast()"
        />

        <!-- Send Button -->
        <button
          class="btn btn-sm btn-secondary ms-1 me-2 rounded-pill"
          type="button"
          @click="transmitNewBroadcast()"
        >
          <i class="bi bi-send ms-2 me-2" style="font-size: 1.2rem" />
        </button>
      </div>
    </div>
  </nav>

  <!-- Emoji Modal -->
  <div id="emojiPickerModal" class="modal fade" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ $t('chat.insertemoji') }}</h5>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            data-bs-target="#emojiPickerModal"
            aria-label="Close"
          />
        </div>
        <div class="modal-body">
          <VuemojiPicker @emoji-click="handleEmojiClick" />
        </div>
      </div>
    </div>
  </div>
</template>
