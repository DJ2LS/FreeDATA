<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useChatStore } from "../store/chatStore.js";
const chat = useChatStore(pinia);


function chatSelected(callsign) {
  chat.selectedCallsign = callsign.toUpperCase();
  // scroll message container to bottom
  var messageBody = document.getElementById("message-container");
  if (messageBody != null) {
    // needs sensible defaults
    messageBody.scrollTop = messageBody.scrollHeight - messageBody.clientHeight;
  }

}

function getDateTime(timestamp) {

        let date = new Date(timestamp);
        let hours = date.getHours().toString().padStart(2, '0');
        let minutes = date.getMinutes().toString().padStart(2, '0');
        let seconds = date.getSeconds().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
}


</script>
<template>
  <div
    class="list-group bg-body-tertiary m-0 p-1"
    id="chat-list-tab"
    role="chat-tablist"
  >

    <template v-for="(details, callsign, key) in chat.callsign_list" :key="callsign">
      <a
        class="list-group-item list-group-item-action list-group-item-secondary rounded-2 border-0 mb-2"
        :class="{ active: key == 0 }"
        :id="`list-chat-list-${callsign}`"
        data-bs-toggle="list"
        :href="`#list-${callsign}-messages`"
        role="tab"
        aria-controls="list-{{callsign}}-messages"
        @click="chatSelected(callsign)"
      >
       <!-- Fixme Dirty hack for ensuring we have a value set for chatSelected... -->
       <span style="display: none;">{{ key === 0 && void chatSelected(callsign) }}</span>
       <!-- End of hack -->


        <div class="row">
          <div class="col-9 text-truncate">
            <strong>{{ callsign }}</strong>
            <br>
            <small> {{details.body}} </small>

          </div>
          <div class="col-3">
          <small> {{getDateTime(details.timestamp)}} </small>
            <button
              class="btn btn-sm btn-outline-secondary ms-2 border-0"
              data-bs-target="#deleteChatModal"
              data-bs-toggle="modal"
              @click="chatSelected(callsign)"
            >
              <i class="bi bi-three-dots-vertical"></i>
            </button>
          </div>
        </div>
      </a>
    </template>
  </div>
</template>
