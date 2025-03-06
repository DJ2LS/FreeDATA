<script setup>
import { ref, computed } from 'vue';

import { getOverallHealth } from '../js/eventHandler.js';
import { getFreedataMessages } from '../js/api';
import { loadAllData } from '../js/eventHandler';

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);

const isTextVisible = ref(false); // Initially, the text is invisible
function toggleTextVisibility() {
  isTextVisible.value = !isTextVisible.value; // Toggle the visibility
}

// Network state computation
import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);
const isNetworkDisconnected = computed(() => state.modem_connection !== "connected");

// Accessing the network traffic state
const isNetworkTraffic = computed(() => state.is_network_traffic);

</script>

<template>
  <!-- Button -->
  <div class="btn-group" role="group" aria-label="Basic example">
    <button
        class="btn btn-outline-secondary border-0 ms-2 mb-3"
        type="button"
        @click="toggleTextVisibility"
    >
      <span class="fw-semibold"><i class="bi bi-text-paragraph"></i></span>
    </button>
  </div>

  <!-- Health Status/Spinner -->
  <div class="btn-group list-group-item" role="group" aria-label="">
    <button
        class="btn border btn-outline-secondary rounded-3"
        data-bs-html="false"
        data-bs-toggle="modal"
        data-bs-target="#modemCheck"
        :title=" $t('navbar.modemcheck_help')"
        :class="
        getOverallHealth() > 4
          ? 'bg-danger'
          : getOverallHealth() < 2
            ? ''
            : 'bg-warning'
      "
    >
      <!-- Show spinner if network traffic is ongoing -->
      <template v-if="isNetworkTraffic">
        <div class="h3 spinner-grow text-secondary p-0 m-0 me-1" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </template>
      <template v-else>
        <i class="h3 bi bi-activity p-1"></i>
      </template>
      <span class="ms-2" v-if="isTextVisible">{{ $t('navbar.modemcheck') }}</span>
    </button>
  </div>


  <div
      class="list-group bg-body-secondary"
      id="main-list-tab"
      role="tablist"
      style="margin-top: 100px"
      @click="isNetworkDisconnected ? null : loadAllData()"
  >
    <a
        class="list-group-item list-group-item-dark list-group-item-action border-0 rounded-3 mb-2 active"
        id="list-grid-list"
        data-bs-toggle="list"
        href="#list-grid"
        role="tab"
        aria-controls="list-grid"
        :title="$t('navbar.home_help')"
        :class="{ disabled: isNetworkDisconnected }"
    >
      <i class="bi bi-columns-gap h3"></i>
      <span class="ms-2" v-if="isTextVisible">{{ $t('navbar.home') }}</span>
    </a>

    <a
        class="list-group-item list-group-item-dark list-group-item-action border-0 rounded-3 mb-2"
        id="list-chat-list"
        data-bs-toggle="list"
        href="#list-chat"
        role="tab"
        aria-controls="list-chat"
        :title="$t('navbar.chat_help')"
        :class="{ disabled: isNetworkDisconnected }"
        @click="isNetworkDisconnected ? null : getFreedataMessages"
    >
      <i class="bi bi-chat-text h3"></i>
      <span class="ms-2" v-if="isTextVisible">{{ $t('navbar.chat') }}</span>
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
        :title="$t('navbar.settings_help')"
        :class="{ disabled: isNetworkDisconnected }"
        @click="isNetworkDisconnected ? null : loadAllData()"
    >
      <i class="bi bi-gear-wide-connected h3"></i>
      <span class="ms-2" v-if="isTextVisible">{{ $t('navbar.settings') }}</span>
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
