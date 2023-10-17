<script setup lang="ts">
import { saveSettingsToFile } from "../js/settingsHandler";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

import main_modals from "./main_modals.vue";
import main_top_navbar from "./main_top_navbar.vue";
import main_audio from "./main_audio.vue";
import main_rig_control from "./main_rig_control.vue";
import main_my_station from "./main_my_station.vue";
import main_updater from "./main_updater.vue";
import settings_view from "./settings.vue";
import main_active_rig_control from "./main_active_rig_control.vue";
import main_footer_navbar from "./main_footer_navbar.vue";

import main_active_stats from "./main_active_stats.vue";
import main_active_broadcasts from "./main_active_broadcasts.vue";
import main_active_heard_stations from "./main_active_heard_stations.vue";
import main_active_audio_level from "./main_active_audio_level.vue";

import chat from "./chat.vue";

import { stopTransmission } from "../js/sock.js";

const version = import.meta.env.PACKAGE_VERSION;

function stopAllTransmissions() {
  console.log("stopping transmissions");
  stopTransmission();
}
function openWebExternal(url) {
  open(url); 
}

</script>

<template>
      <!-------------------------------- INFO TOASTS ---------------->
      <div
        aria-live="polite"
        aria-atomic="true"
        class="position-relative"
        style="z-index: 500"
      >
        <div
          class="toast-container position-absolute top-0 end-0 p-3"
          id="mainToastContainer"
        ></div>
      </div>

      <div class="container-fluid">
        <div class="row">
          <div class="col-sm-auto bg-body-secondary border-end">
            <div
              class="d-flex flex-sm-column flex-row flex-nowrap align-items-center sticky-top"
            >
              <div
                class="list-group bg-body-secondary"
                id="main-list-tab"
                role="tablist"
                style="margin-top: 100px"
              >
                <a
                  class="list-group-item list-group-item-action active"
                  id="list-tnc-list"
                  data-bs-toggle="list"
                  href="#list-tnc"
                  role="tab"
                  aria-controls="list-tnc"
                  ><i class="bi bi-house-door-fill h3"></i
                ></a>
                <a
                  class="list-group-item list-group-item-action"
                  id="list-chat-list"
                  data-bs-toggle="list"
                  href="#list-chat"
                  role="tab"
                  aria-controls="list-chat"
                  ><i class="bi bi-chat-text h3"></i
                ></a>

                <a
                  class="list-group-item list-group-item-action d-none"
                  id="list-mesh-list"
                  data-bs-toggle="list"
                  href="#list-mesh"
                  role="tab"
                  aria-controls="list-mesh"
                  ><i class="bi bi-rocket h3"></i
                ></a>

                <a
                  class="list-group-item list-group-item-action mt-2 border"
                  id="list-info-list"
                  data-bs-toggle="list"
                  href="#list-info"
                  role="tab"
                  aria-controls="list-info"
                  ><i class="bi bi-info h3"></i
                ></a>

                <a
                  class="list-group-item list-group-item-action d-none"
                  id="list-logger-list"
                  data-bs-toggle="list"
                  href="#list-logger"
                  role="tab"
                  aria-controls="list-logger"
                  ><i class="bi bi-activity h3"></i
                ></a>

                <a
                  class="list-group-item list-group-item-action rounded-bottom"
                  id="list-settings-list"
                  data-bs-toggle="list"
                  href="#list-settings"
                  role="tab"
                  aria-controls="list-settings"
                  ><i class="bi bi-gear-wide-connected h3"></i
                ></a>

                <a
                  class="btn border btn-outline-danger list-group-item mt-5"
                  id="stop_transmission_connection"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="false"
                  @click="stopAllTransmissions()"
                  title="Abort session and stop transmissions"
                  ><i class="bi bi-sign-stop-fill h3"></i
                ></a>
              </div>
            </div>
          </div>
          <div class="col-sm min-vh-100 m-0 p-0">
            <!-- content -->

            <div class="tab-content" id="nav-tabContent-settings">
              <div
                class="tab-pane fade show active"
                id="list-tnc"
                role="tabpanel"
                aria-labelledby="list-tnc-list"
              >
                <!-- TOP NAVBAR -->
                <main_top_navbar />

                <div
                  id="blurdiv"
                  style="-webkit-filter: blur(0px); filter: blur(0px); height: 100vh"
                >
                  <!--beginn of blur div -->
                  <!-------------------------------- MAIN AREA ---------------->

                  <!------------------------------------------------------------------------------------------>
                  <div class="container p-3">
                    <div
                      class="row collapse multi-collapse show mt-4"
                      id="collapseFirstRow"
                    >
                      <div class="col">
                        <main_audio />
                      </div>
                      <div class="col">
                        <main_rig_control />
                      </div>
                    </div>
                    <div
                      class="row collapse multi-collapse show mt-4"
                      id="collapseSecondRow"
                    >
                      <div class="col">
                        <main_my_station />
                      </div>
                      <div class="col">
                        <main_updater />
                      </div>
                    </div>
                  </div>
                  <div class="container">
                    <div
                      class="row collapse multi-collapse"
                      id="collapseThirdRow"
                    >
                      <main_active_rig_control />

                      <div class="col-5">
                        <main_active_audio_level />
                      </div>
                      <div class="col">
                        <main_active_broadcasts />
                      </div>
                    </div>
                    <div
                      class="row collapse multi-collapse mt-3"
                      id="collapseFourthRow"
                    >
                      <div class="col-5">
                        <main_active_stats />
                      </div>
                      <div class="col">
                        <main_active_heard_stations />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div
                class="tab-pane fade d-none"
                id="list-mesh"
                role="tabpanel"
                aria-labelledby="list-mesh-list"
              >
                <div class="container">
                  <nav>
                    <div
                      class="nav nav-tabs"
                      id="nav-tab-mesh"
                      role="tablist-mesh"
                    >
                      <button
                        class="nav-link active"
                        id="nav-route-tab"
                        data-bs-toggle="tab"
                        data-bs-target="#nav-route"
                        type="button"
                        role="tab"
                        aria-controls="nav-route"
                        aria-selected="true"
                      >
                        Routes
                      </button>
                      <button
                        class="nav-link"
                        id="nav-signaling-tab"
                        data-bs-toggle="tab"
                        data-bs-target="#nav-signaling"
                        type="button"
                        role="tab"
                        aria-controls="nav-signaling"
                        aria-selected="false"
                      >
                        Signaling
                      </button>
                      <button
                        class="nav-link"
                        id="nav-actions-tab"
                        data-bs-toggle="tab"
                        data-bs-target="#nav-actions"
                        type="button"
                        role="tab"
                        aria-controls="nav-actions"
                        aria-selected="false"
                      >
                        Actions
                      </button>
                    </div>
                  </nav>

                  <div class="tab-content d-none" id="nav-tabContent-Mesh">
                    <div
                      class="tab-pane fade show active vw-100 vh-90 overflow-auto"
                      id="nav-route"
                      role="tabpanel"
                      aria-labelledby="nav-route-tab"
                    >
                      <div class="container-fluid">
                        <div
                          class="table-responsive overflow-auto"
                          style="max-width: 99vw; max-height: 99vh"
                        >
                          <table class="table table-hover table-sm">
                            <thead>
                              <tr>
                                <th scope="col">Timestamp</th>
                                <th scope="col">DXCall</th>
                                <th scope="col">Router</th>
                                <th scope="col">Hops</th>
                                <th scope="col">Score</th>
                                <th scope="col">SNR</th>
                              </tr>
                            </thead>
                            <tbody id="mesh-table"></tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                    <div
                      class="tab-pane fade"
                      id="nav-signaling"
                      role="tabpanel"
                      aria-labelledby="nav-signaling-tab"
                    >
                      <div class="container-fluid">
                        <div
                          class="table-responsive overflow-auto"
                          style="max-width: 99vw; max-height: 99vh"
                        >
                          <table class="table table-hover table-sm">
                            <thead>
                              <tr>
                                <th scope="col">Timestamp</th>
                                <th scope="col">Destination</th>
                                <th scope="col">Origin</th>
                                <th scope="col">Frametype</th>
                                <th scope="col">Payload</th>
                                <th scope="col">Attempt</th>
                                <th scope="col">Status</th>
                              </tr>
                            </thead>
                            <tbody id="mesh-signalling-table"></tbody>
                          </table>
                        </div>
                      </div>
                    </div>

                    <div
                      class="tab-pane fade"
                      id="nav-actions"
                      role="tabpanel-mesh"
                      aria-labelledby="nav-actions-tab"
                    >
                      <div class="input-group mt-1">
                        <input
                          type="text"
                          class="form-control"
                          style="max-width: 6rem; text-transform: uppercase"
                          placeholder="DXcall"
                          pattern="[A-Z]*"
                          id="dxCallMesh"
                          maxlength="11"
                          aria-label="Input group"
                          aria-describedby="btnGroupAddon"
                        />
                        <button
                          id="transmit_mesh_ping"
                          type="button"
                          class="btn btn-primary"
                        >
                          mesh ping
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div
                class="tab-pane fade"
                id="list-info"
                role="tabpanel"
                aria-labelledby="list-info-list"
              >
                <h1 class="modal-title fs-5" id="aboutModalLabel">
                  FreeDATA - {{ version }}
                </h1>

<h4 class="fs-5">
                  tnc version - {{ state.tnc_version }}
                </h4>



                <div class="container-fluid">
                  <div class="row mt-2">
                    <div
                      class="btn-toolbar mx-auto"
                      role="toolbar"
                      aria-label="Toolbar with button groups"
                    >
                      <div class="btn-group">
                        <button
                          class="btn btn-sm bi bi-geo-alt btn-secondary me-2"
                          id="openExplorer"
                          type="button"
                          data-bs-placement="bottom"
                          @click="openWebExternal('https://explorer.freedata.app')"
                        >
                          Explorer map
                        </button>
                      </div>
                      <div class="btn-group">
                        <button
                          class="btn btn-sm btn-secondary me-2 bi bi-graph-up"
                          id="btnStats"
                          type="button"
                          data-bs-placement="bottom"
                          @click="openWebExternal('https://statistics.freedata.app/')"
                        >
                          Statistics
                        </button>
                      </div>
                      <div class="btn-group">
                        <button
                          class="btn btn-secondary bi bi-bookmarks me-2"
                          id="fdWww"
                          data-bs-toggle="tooltip"
                          data-bs-trigger="hover"
                          title="FreeDATA website"
                          role="button"
                          @click="openWebExternal('https://freedata.app')"
                        >
                          Website
                        </button>
                      </div>
                      <div class="btn-group">
                        <button
                          class="btn btn-secondary bi bi-github me-2"
                          id="ghUrl"
                          data-bs-toggle="tooltip"
                          data-bs-trigger="hover"
                          title="Github"
                          role="button"
                          @click="openWebExternal('https://github.com/dj2ls/freedata')"
                        >
                          Github
                        </button>
                      </div>
                      <div class="btn-group">
                        <button
                          class="btn btn-secondary bi bi-wikipedia me-2"
                          id="wikiUrl"
                          data-bs-toggle="tooltip"
                          data-bs-trigger="hover"
                          title="Wiki"
                          role="button"
                          @click="openWebExternal('https://wiki.freedata.app')"
                        >
                          Wiki
                        </button>
                      </div>
                      <div class="btn-group">
                        <button
                          class="btn btn-secondary bi bi-discord"
                          id="discordUrl"
                          data-bs-toggle="tooltip"
                          data-bs-trigger="hover"
                          title="Discord"
                          role="button"
                          @click="openWebExternal('https://discord.freedata.app')"
                        >
                          Discord
                        </button>
                      </div>
                    </div>
                  </div>
                  <div class="row mt-5">
                    <h6>Special thanks to</h6>
                    <hr />
                  </div>
                  <div class="row">
                    <div class="col-4" id="divContrib"></div>
                    <div class="col-4" id="divContrib2"></div>
                    <div class="col-4" id="divContrib3"></div>
                  </div>
                </div>
              </div>
              <div
                class="tab-pane fade"
                id="list-chat"
                role="tabpanel"
                aria-labelledby="list-chat-list"
              >
                <chat />
              </div>
              <div
                class="tab-pane fade"
                id="list-logger"
                role="tabpanel"
                aria-labelledby="list-logger-list"
              >
                <div class="container">
                  <nav
                    class="navbar fixed-top bg-body-tertiary border-bottom"
                    style="margin-left: 87px"
                  >
                    <div class="container-fluid">
                      <input
                        type="checkbox"
                        class="btn-check"
                        id="enable_filter_info"
                        autocomplete="off"
                        checked
                      />
                      <label
                        class="btn btn-outline-info"
                        for="enable_filter_info"
                        >info</label
                      >

                      <input
                        type="checkbox"
                        class="btn-check"
                        id="enable_filter_debug"
                        autocomplete="off"
                      />
                      <label
                        class="btn btn-outline-primary"
                        for="enable_filter_debug"
                        >debug</label
                      >

                      <input
                        type="checkbox"
                        class="btn-check"
                        id="enable_filter_warning"
                        autocomplete="off"
                      />
                      <label
                        class="btn btn-outline-warning"
                        for="enable_filter_warning"
                        >warning</label
                      >

                      <input
                        type="checkbox"
                        class="btn-check"
                        id="enable_filter_error"
                        autocomplete="off"
                      />
                      <label
                        class="btn btn-outline-danger"
                        for="enable_filter_error"
                        >error</label
                      >
                    </div>
                  </nav>

                  <div class="container-fluid mt-5">
                    <div class="tableFixHead">
                      <table class="table table-hover">
                        <thead>
                          <tr>
                            <th scope="col">Timestamp</th>
                            <th scope="col">Type</th>
                            <th scope="col">Area</th>
                            <th scope="col">Log entry</th>
                          </tr>
                        </thead>
                        <tbody id="log">
                          <!--
                     <tr>
                       <th scope="row">1</th>
                       <td>Mark</td>
                       <td>Otto</td>
                       <td>@mdo</td>
                     </tr>
                         -->
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <settings_view />

            <!---------------------------------------------------------------------- FOOTER AREA ------------------------------------------------------------>

            <div class="container">
              <main_footer_navbar />
            </div>
          </div>
        </div>
      </div>

      <main_modals />
</template>
