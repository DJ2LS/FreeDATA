<script setup lang="ts">
import { ref } from "vue";
import main_modem_healthcheck from "./main_modem_healthcheck.vue";

import { getOverallHealth } from "../js/eventHandler.js";
import { getFreedataMessages } from "../js/api";
import { getRemote } from "../store/settingsStore.js";
import { loadAllData } from "../js/eventHandler";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useChatStore } from "../store/chatStore.js";
const chat = useChatStore(pinia);


const isTextVisible = ref(false); // Initially, the text is invisible
function toggleTextVisibility() {
  isTextVisible.value = !isTextVisible.value; // Toggle the visibility
}
</script>
<template>
  <!-- Button -->

  <div class="btn-group" role="group" aria-label="Basic example">
    <button
      class="btn btn-outline-secondary border-0 ms-2 mb-3"
      type="button"
      @click="toggleTextVisibility()"
    >
      <span class="fw-semibold"><i class="bi bi-text-paragraph"></i></span>
    </button>
  </div>

  <a
    class="btn border btn-outline-secondary list-group-item rounded-3"
    data-bs-html="false"
    data-bs-toggle="modal"
    data-bs-target="#modemCheck"
    title="Check FreeDATA status"
    :class="
      getOverallHealth() > 4
        ? 'bg-danger'
        : getOverallHealth() < 2
          ? ''
          : 'bg-warning'
    "
    ><i class="h3 bi bi-activity"></i>
    <span class="ms-2" v-if="isTextVisible">Healtcheck</span>
  </a>

  <div
    class="list-group bg-body-secondary"
    id="main-list-tab"
    role="tablist"
    style="margin-top: 100px"
    @click="loadAllData"
  >
    <a
      class="list-group-item list-group-item-dark list-group-item-action border-0 rounded-3 mb-2 active"
      id="list-grid-list"
      data-bs-toggle="list"
      href="#list-grid"
      role="tab"
      aria-controls="list-grid"
      title="Grid"
    >
      <i class="bi bi-grid h3"></i>
      <span class="ms-2" v-if="isTextVisible">Home</span>
    </a>

    <a
      class="list-group-item list-group-item-dark list-group-item-action border-0 rounded-3 mb-2"
      id="list-chat-list"
      data-bs-toggle="list"
      href="#list-chat"
      role="tab"
      aria-controls="list-chat"
      title="Chat"
      @click="getFreedataMessages"
    >
      <i class="bi bi-chat-text h3"></i>
      <span class="ms-2" v-if="isTextVisible">RF Chat</span>
      <span
    v-if="chat.totalUnreadMessages > 0"
    class="badge bg-danger position-absolute top-0 end-0 mt-1 me-1"
>
    {{ chat.totalUnreadMessages }}
  </span>
    </a>




    <a
      class="list-group-item list-group-item-dark list-group-item-action d-none border-0 rounded-3 mb-2"
      id="list-mesh-list"
      data-bs-toggle="list"
      href="#list-mesh"
      role="tab"
      aria-controls="list-mesh"
    >
      <i class="bi bi-rocket h3"></i>
      <span class="ms-2" v-if="isTextVisible">Mesh</span>
    </a>

    <a
      class="list-group-item list-group-item-dark list-group-item-action border-0 rounded-3 mb-2"
      id="list-settings-list"
      data-bs-toggle="list"
      href="#list-settings"
      role="tab"
      aria-controls="list-settings"
      title="Settings"
      @click="loadAllData"
    >
      <i class="bi bi-gear-wide-connected h3"></i>
      <span class="ms-2" v-if="isTextVisible">Settings</span>
    </a>
  </div>

  <button
    class="btn btn-outline-secondary border-0 left-bottom-btn position-fixed bottom-0 mb-3 rounded-3 ms-1"
    data-bs-html="false"
    data-bs-toggle="modal"
    data-bs-target="#stationInfoModal"
    title="Set station info"
    disabled
  >
    <i class="bi bi-person-circle h3"></i>
    <span class="ms-2" v-if="isTextVisible">Station</span>
  </button>
</template>
