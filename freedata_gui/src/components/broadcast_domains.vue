<template>
  <!-- Navbar for starting a new chat -->
  <nav class="navbar sticky-top bg-body-tertiary border-bottom p-1">

    <button
      class="btn btn-outline-primary w-100"
      data-bs-target="#newBroadcastModal"
      data-bs-toggle="modal"
      @click="startNewBroadcast"
    >
      <i class="bi bi-pencil-square" /> {{ $t('chat.startnewchat') }}
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
      v-else-if="!broadcast.domain_list || Object.keys(broadcast.domain_list).length === 0"
      class="text-center p-2"
    >
      {{ $t('chat.noConversations') }}
    </div>


    <template
      v-for="(details, domain) in broadcast.callsign_list"
      :key="callsign"
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
            <strong>Typ, Global, EU, US, Asia, ... EMCOM</strong>
            <br>
            <small>{{ sanitizeBody(details.body.substring(0, 35) + '...') || "\u003Cfile\u003E" }}</small>

          </div>
          <div class="col-5 text-end">
            <small>{{ getDateTime(details.timestamp) }}</small>

          </div>
        </div>
      </a>
    </template>
  </div>
</template>

<script setup>

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useBroadcastStore } from '../store/broadcastStore.js';
const broadcast = useBroadcastStore(pinia);

</script>
