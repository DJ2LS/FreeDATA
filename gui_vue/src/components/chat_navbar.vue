<script setup lang="ts">


import {saveSettingsToFile} from '../js/settingsHandler';

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);

import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);


function newChat(obj){

        let callsign = document.getElementById("chatModuleNewDxCall").value
        callsign = callsign.toUpperCase()
            chat.callsign_list.add(callsign)


}

</script>

<template>
<nav class="navbar bg-body-tertiary border-bottom">
                    <div class="container">
                      <div class="row w-100">
                        <div class="col-4 p-0 me-2">
                          <div class="input-group bottom-0 m-0">
                            <input
                              class="form-control w-50"
                              maxlength="9"
                              style="text-transform: uppercase"
                              id="chatModuleNewDxCall"
                              placeholder="DX CALL"
                            />
                            <button
                              class="btn btn-sm btn-success"
                              id="createNewChatButton"
                              type="button"
                              title="Start a new chat (enter dx call sign first)"
                              @click="newChat()"
                            >
                              new chat
                              <i
                                class="bi bi-pencil-square"
                                style="font-size: 1.2rem"
                              ></i>
                            </button>


                          </div>
                        </div>
                        <div class="col-7 ms-2 p-0">

                        <!-- right side of chat nav bar-->


                        </div>
                      </div>
                    </div>
                  </nav>
</template>
