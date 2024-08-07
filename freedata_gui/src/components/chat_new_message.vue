<script setup>
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);

import { newMessage } from '../js/messagesHandler.js';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { ref } from 'vue';

import { VuemojiPicker } from 'vuemoji-picker';

const handleEmojiClick = (detail) => {
  chat.inputText += detail.unicode;
};

const chatModuleMessage = ref(null);

// Function to trigger the hidden file input
function triggerFileInput() {
  fileInput.value.click();
}

// Use a ref for storing multiple files
const selectedFiles = ref([]);
const fileInput = ref(null);

function handleFileSelection(event) {
  // Reset previously selected files
  selectedFiles.value = [];

  // Process each file
  for (let file of event.target.files) {
    const reader = new FileReader();
    reader.onload = () => {
      // Convert file content to base64
      const base64Content = btoa(reader.result);
      selectedFiles.value.push({
        name: file.name,
        size: file.size,
        type: file.type,
        content: base64Content, // Store base64 encoded content
      });
    };
    reader.readAsBinaryString(file); // Read the file content as binary string
  }
}

function removeFile(index) {
  selectedFiles.value.splice(index, 1);
  // Check if the selectedFiles array is empty
  if (selectedFiles.value.length === 0) {
    // Reset the file input if there are no files left
    resetFile();
  }
}

function transmitNewMessage() {
  // Check if a callsign is selected, default to the first one if not
  if (typeof(chat.selectedCallsign) === 'undefined') {
    chat.selectedCallsign = Object.keys(chat.callsign_list)[0];
  }

  chat.inputText = chat.inputText.trim();

  // Proceed only if there is text or files selected
  if (chat.inputText.length === 0 && selectedFiles.value.length === 0) return;

  const attachments = selectedFiles.value.map(file => ({
    name: file.name,
    type: file.type,
    data: file.content
  }));

  if (chat.selectedCallsign.startsWith("BC-")) {
    // Handle broadcast message differently if needed
    return "new broadcast";
  } else {
    // If there are attachments, send them along with the message
    if (attachments.length > 0) {
      newMessage(chat.selectedCallsign, chat.inputText, attachments);
    } else {
      // Send text only if no attachments are selected
      newMessage(chat.selectedCallsign, chat.inputText);
    }
  }

  // Cleanup after sending message
  chat.inputText = '';
  chatModuleMessage.value = "";
  resetFile();
}

function resetFile() {
  if (fileInput.value) {
    fileInput.value.value = ''; // Reset the file input
  }
  // Clear the selected files array to reset the state of attachments
  selectedFiles.value = [];
}

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);



</script>

<template>
  <nav class="navbar sticky-bottom bg-body-tertiary border-top">
    <div class="container-fluid p-0">
      <!-- Hidden file input -->
      <input type="file" multiple ref="fileInput" @change="handleFileSelection" style="display: none;" />

      <div class="container-fluid">
        <div class="d-flex flex-row overflow-auto bg-light">
          <div v-for="(file, index) in selectedFiles" :key="index" class="p-2">
            <div class="card" style="min-width: 10rem; max-width: 10rem;">
              <!-- Card Header with Remove Button -->
              <div class="card-header d-flex justify-content-between align-items-center">
                <span class="text-truncate">{{ file.name }}</span>
                <button class="btn btn-close" @click="removeFile(index)"></button>
              </div>
              <div class="card-footer text-muted">
                {{ file.type }}
              </div>
              <div class="card-footer text-muted">
                {{ file.size }} bytes
              </div>
            </div>
          </div>
        </div>
      </div>

      <!--
      <Line :data="speedChartData" />
      -->

      <div class="input-group bottom-0 ms-2">
        <button
          type="button"
          class="btn btn-outline-secondary border-0 rounded-pill me-1"
          data-bs-toggle="modal"
          data-bs-target="#emojiPickerModal"
          data-bs-backdrop="false"
          @click="$refs.chatModuleMessage.focus()"
        >
          <i id="emojipickerbutton" class="bi bi-emoji-smile p-0" style="font-size: 1rem"></i>
        </button>

        <!-- Trigger file selection modal -->
        <button
          type="button"
          class="btn btn-outline-secondary border-0 rounded-pill me-1"
          @click="triggerFileInput(), $event.target.blur(), $refs.chatModuleMessage.focus()"
        >
          <i class="bi bi-paperclip" style="font-size: 1.2rem"></i>
        </button>

        <textarea
          class="form-control border rounded-pill"
          rows="1"
          ref="chatModuleMessage"
          placeholder="Message - Send with [Enter]"
          v-model="chat.inputText"
          @keyup.enter="transmitNewMessage()"
        ></textarea>

        <button
          class="btn btn-sm btn-secondary ms-1 me-2 rounded-pill"
          @click="transmitNewMessage()"
          type="button"
        >
          <i class="bi bi-send ms-4 me-4" style="font-size: 1.2rem"></i>
        </button>
      </div>
    </div>
  </nav>

  <!-- Emoji Picker Modal -->
  <div class="modal fade" id="emojiPickerModal" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-sm">
      <div class="modal-content">
        <div class="modal-body p-0">
          <VuemojiPicker @emojiClick="handleEmojiClick" />
        </div>
      </div>
    </div>
  </div>
</template>
