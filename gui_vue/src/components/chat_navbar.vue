<script setup lang="ts">


import {saveSettingsToFile} from '../js/settingsHandler';

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);

import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);


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
                            >
                              <i
                                class="bi bi-pencil-square"
                                style="font-size: 1.2rem"
                              ></i>
                            </button>

                            <button
                              type="button"
                              id="userModalButton"
                              data-bs-toggle="modal"
                              data-bs-target="#userModal"
                              class="btn btn-sm btn-primary ms-2"
                              title="My station info"
                            >
                              <i
                                class="bi bi-person"
                                style="font-size: 1.2rem"
                              ></i>
                            </button>
                            <button
                              type="button"
                              id="sharedFolderButton"
                              data-bs-toggle="modal"
                              data-bs-target="#sharedFolderModal"
                              class="btn btn-sm btn-primary"
                              title="My shared folder"
                            >
                              <i
                                class="bi bi-files"
                                style="font-size: 1.2rem"
                              ></i>
                            </button>
                          </div>
                        </div>
                        <div class="col-7 ms-2 p-0">
                          <div class="input-group bottom-0">
                            <button
                              class="btn btn-sm btn-outline-secondary me"
                              id="ping"
                              type="button"
                              data-bs-toggle="tooltip"
                              data-bs-trigger="hover"
                              data-bs-html="false"
                              title="Ping remote station"
                            >
                              Ping
                            </button>

                            <button
                              type="button"
                              id="userModalDXButton"
                              data-bs-toggle="modal"
                              data-bs-target="#userModalDX"
                              class="btn btn-sm btn-outline-secondary"
                              title="Request remote station's information"
                            >
                              <i
                                class="bi bi-person"
                                style="font-size: 1.2rem"
                              ></i>
                            </button>

                            <button
                              type="button"
                              id="sharedFolderDXButton"
                              data-bs-toggle="modal"
                              data-bs-target="#sharedFolderModalDX"
                              class="btn btn-sm btn-outline-secondary me-2"
                              title="Request remote station's shared files"
                            >
                              <i
                                class="bi bi-files"
                                style="font-size: 1.2rem"
                              ></i>
                            </button>

                            <button
                              type="button"
                              class="btn btn-small btn-outline-primary dropdown-toggle me-2"
                              data-bs-toggle="dropdown"
                              aria-expanded="false"
                              data-bs-auto-close="outside"
                              data-bs-trigger="hover"
                              data-bs-html="false"
                              title="Message filter"
                            >
                              <i class="bi bi-funnel-fill"></i>
                            </button>
                            <form class="dropdown-menu p-4" id="frmFilter">
                              <div class="mb-1">
                                <div class="form-check">
                                  <input
                                    checked="true"
                                    type="checkbox"
                                    class="form-check-input"
                                    id="chkMessage"
                                  />
                                  <label
                                    class="form-check-label"
                                    for="chkMessage"
                                  >
                                    All Messages
                                  </label>
                                </div>
                              </div>
                              <div class="mb-1">
                                <div class="form-check">
                                  <input
                                    checked="false"
                                    type="checkbox"
                                    class="form-check-input"
                                    id="chkNewMessage"
                                  />

                                  <label
                                    class="form-check-label"
                                    for="chkNewMessage"
                                  >
                                    Unread Messages
                                  </label>
                                </div>
                              </div>
                              <div class="mb-1">
                                <div class="form-check">
                                  <input
                                    type="checkbox"
                                    class="form-check-input"
                                    id="chkPing"
                                  />
                                  <label class="form-check-label" for="chkPing">
                                    Pings
                                  </label>
                                </div>
                              </div>
                              <div class="mb-1">
                                <div class="form-check">
                                  <input
                                    checked="true"
                                    type="checkbox"
                                    class="form-check-input"
                                    id="chkPingAck"
                                  />
                                  <label
                                    class="form-check-label"
                                    for="chkPingAck"
                                  >
                                    Ping-Acks
                                  </label>
                                </div>
                              </div>
                              <div class="mb-1">
                                <div class="form-check">
                                  <input
                                    type="checkbox"
                                    class="form-check-input"
                                    id="chkBeacon"
                                  />
                                  <label
                                    class="form-check-label"
                                    for="chkBeacon"
                                  >
                                    Beacons
                                  </label>
                                </div>
                              </div>
                              <div class="mb-1">
                                <div class="form-check">
                                  <input
                                    type="checkbox"
                                    class="form-check-input"
                                    id="chkRequest"
                                  />
                                  <label
                                    class="form-check-label"
                                    for="chkRequest"
                                  >
                                    Requests
                                  </label>
                                </div>
                              </div>
                              <div class="mb-1">
                                <div class="form-check">
                                  <input
                                    type="checkbox"
                                    class="form-check-input"
                                    id="chkResponse"
                                  />
                                  <label
                                    class="form-check-label"
                                    for="chkResponse"
                                  >
                                    Responses
                                  </label>
                                </div>
                              </div>
                              <button
                                type="button"
                                class="btn btn-primary"
                                id="btnFilter"
                              >
                                Refresh
                              </button>
                            </form>

                            <button
                              id="chatSettingsDropDown"
                              type="button"
                              class="btn btn-outline-secondary dropdown-toggle"
                              data-bs-toggle="dropdown"
                              aria-expanded="false"
                              title="More options...."
                            >
                              <i class="bi bi-three-dots-vertical"></i>
                            </button>
                            <ul
                              class="dropdown-menu"
                              aria-labelledby="chatSettingsDropDown"
                            >
                              <li>
                                <a
                                  class="dropdown-item bg-danger text-white"
                                  id="delete_selected_chat"
                                  href="#"
                                  ><i
                                    class="bi bi-person-x"
                                    style="font-size: 1rem"
                                  ></i>
                                  Delete chat</a
                                >
                              </li>
                              <div class="dropdown-divider"></div>
                              <li>
                                <button
                                  class="dropdown-item"
                                  id="openHelpModalchat"
                                  data-bs-toggle="modal"
                                  data-bs-target="#chatHelpModal"
                                >
                                  <i
                                    class="bi bi-question-circle"
                                    style="font-size: 1rem"
                                  ></i>
                                  Help
                                </button>
                              </li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  </nav>
</template>
