<template>
  <!-- Navbar for starting a new chat -->
  <nav class="navbar sticky-top bg-body-tertiary border-bottom p-1">

    <button
      class="btn btn-outline-primary w-100"
      data-bs-target="#newBroadcastModal"
      data-bs-toggle="modal"
      @click="startNewBroadcast"
    >
      <i class="bi bi-pencil-square" /> {{ $t('broadcast.startnewbroadcast') }}
    </button>
  </nav>

  <!-- List of broadcasts -->

  <div
    id="chat-list-tab"
    class="list-group m-0 p-1"
    role="tablist"
  >
    <!-- Show loading message if we're waiting -->
    <div
      v-if="broadcast.loading"
      class="text-center p-2"
    >
      <div
        class="spinner-border"
        role="status"
      >
        <span class="visually-hidden">{{ $t('chat.loadingMessages') }}</span>
      </div>
    </div>

    <!-- Show 'no conversations' message if not loading and no conversations exist -->
    <div
      v-else-if="!broadcast.domains || Object.keys(broadcast.domains).length === 0"
      class="text-center p-2"
    >
      {{ $t('broadcast.noDomains') }}
    </div>

<template
  v-for="(details, domain) in broadcast.domains"
  :key="domain"
>
  <a
    :id="`list-domain-list-${domain}`"
    class="list-group-item list-group-item-action list-group-item-secondary rounded-2 border-0 mb-2"
    data-bs-toggle="list"
    :href="`#list-${domain}-messages`"
    role="tab"
    :aria-controls="`list-${domain}-messages`"
    @click="domainSelected(domain)"
  >
    <div class="row">
      <div class="col-7 text-truncate">
        <strong>{{ domain }}</strong>
        <span class="badge bg-secondary ms-1 rounded-pill">
            {{ details.message_count }}
          </span>
        <br>
        <small class="text-muted d-inline-flex align-items-center gap-2">

          <span
            class="badge rounded-pill"
            :class="details.unread_count > 0 ? 'bg-danger' : 'bg-success'"
            :aria-label="details.unread_count > 0 ? (details.unread_count + $t('broadcast.unread_description')) : $t('broadcast.unread_description')"
            :title="details.unread_count > 0 ? (details.unread_count + $t('broadcast.unread_description')) : $t('broadcast.unread_description')"
          >
            {{ details.unread_count }}&nbsp;{{ $t('broadcast.unread') }}
          </span>
        </small>
      </div>
      <div class="col-5 text-end">
        <small>
          {{ getDateTime(details.last_message_timestamp) }}
        </small>
      </div>
    </div>
  </a>
</template>

  </div>
</template>

<script setup>

import { getFreedataBroadcastsPerDomain } from '../js/api.js';
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useBroadcastStore } from '../store/broadcastStore.js';
const broadcast = useBroadcastStore(pinia);

function getDateTime(input) {
  let date;
  if (typeof input === 'number') {
    // Assuming input is a Unix timestamp in seconds
    date = new Date(input * 1000);
  } else {
    // Assuming input is an ISO 8601 formatted string
    date = new Date(input);
  }

  const now = new Date();
  const isSameDay = date.getDate() === now.getDate() &&
                    date.getMonth() === now.getMonth() &&
                    date.getFullYear() === now.getFullYear();

  if (isSameDay) {
    // Use the browser's locale to format time only
    return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  } else {
    // Use the browser's locale to format both date and time
    const datePart = date.toLocaleDateString(undefined, { day: '2-digit', month: '2-digit', year: 'numeric' });
    //const timePart = date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
    //return `${datePart} ${timePart}`;
    return `${datePart}`;
  }
}

function domainSelected(domain) {
  broadcast.selectedDomain = domain.toUpperCase();
  broadcast.triggerScrollToBottom();
  //setMessagesAsRead(domain);
  getFreedataBroadcastsPerDomain(domain);
}



</script>
