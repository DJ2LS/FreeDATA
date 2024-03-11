<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import main_modals from "./main_modals.vue";
import main_top_navbar from "./main_top_navbar.vue";
import settings_view from "./settings.vue";
import main_footer_navbar from "./main_footer_navbar.vue";

import chat from "./chat.vue";
import main_modem_healthcheck from "./main_modem_healthcheck.vue";
import Dynamic_components from "./dynamic_components.vue";

import { getFreedataMessages } from "../js/api";
import { getRemote } from "../store/settingsStore.js";
import { loadAllData } from "../js/eventHandler";
</script>

<template>
  <!-------------------------------- INFO TOASTS ---------------->
  <div aria-live="polite" aria-atomic="true" class="position-relative z-3">
    <div
      class="toast-container position-absolute top-0 end-0 p-3"
      id="mainToastContainer"
    ></div>
  </div>

  <div class="container-fluid">
    <div class="row">
      <div class="col-1 p-0 bg-body-secondary border-end">
        <div
          class="d-flex flex-sm-column flex-row flex-nowrap align-items-center sticky-top"
        >
          <div
            class="list-group bg-body-secondary"
            id="main-list-tab"
            role="tablist"
            style="margin-top: 100px"
            @click="loadAllData"
          >
            <main_modem_healthcheck />

            <a
              class="list-group-item list-group-item-dark list-group-item-action border-0 rounded-3 mb-2 active"
              id="list-grid-list"
              data-bs-toggle="list"
              href="#list-grid"
              role="tab"
              aria-controls="list-grid"
              title="Grid"
              ><i class="bi bi-grid h3"></i
            ></a>

            <a
              class="list-group-item list-group-item-dark list-group-item-action border-0 rounded-3 mb-2"
              id="list-chat-list"
              data-bs-toggle="list"
              href="#list-chat"
              role="tab"
              aria-controls="list-chat"
              title="Chat"
              @click="getFreedataMessages"
              ><i class="bi bi-chat-text h3"></i
            ></a>

            <a
              class="list-group-item list-group-item-dark list-group-item-action d-none border-0 rounded-3 mb-2"
              id="list-mesh-list"
              data-bs-toggle="list"
              href="#list-mesh"
              role="tab"
              aria-controls="list-mesh"
              ><i class="bi bi-rocket h3"></i
            ></a>

            <a
              class="list-group-item list-group-item-dark list-group-item-action d-none border-0 rounded-3 mb-2"
              id="list-logger-list"
              data-bs-toggle="list"
              href="#list-logger"
              role="tab"
              aria-controls="list-logger"
              ><i class="bi bi-activity h3"></i
            ></a>
            <a
              class="list-group-item list-group-item-dark list-group-item-action border-0 rounded-3 mb-2"
              id="list-settings-list"
              data-bs-toggle="list"
              href="#list-settings"
              role="tab"
              aria-controls="list-settings"
              title="Settings"
              @click="loadAllData"
              ><i class="bi bi-gear-wide-connected h3"></i
            ></a>
          </div>
        </div>
      </div>
      <div class="col-11 min-vh-100 m-0 p-0">
        <!-- content -->

        <!-- TODO: Remove the top navbar entirely if not needed
        <main_top_navbar />
      -->

        <div class="tab-content" id="nav-tabContent-settings">
          <div
            class="tab-pane fade"
            id="list-home"
            role="tabpanel"
            aria-labelledby="list-home-list"
          >
            <!-- TOP NAVBAR -->
            <div
              id="blurdiv"
              style="
                -webkit-filter: blur(0px);
                filter: blur(0px);
                height: 100vh;
              "
            >
              <!--beginn of blur div -->
              <!-------------------------------- MAIN AREA ---------------->

              <!------------------------------------------------------------------------------------------>
              <div class="container">
                <div class="row">
                  <div class="col-5">
                    <main_active_rig_control />
                  </div>
                  <div class="col-4">
                    <main_active_broadcasts />
                  </div>
                  <div class="col-3">
                    <main_active_audio_level />
                  </div>
                </div>
                <div class="row">
                  <div class="col-7">
                    <main_active_heard_stations />
                  </div>
                  <div class="col-5">
                    <main_active_stats />
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
                <div class="nav nav-tabs" id="nav-tab-mesh" role="tablist-mesh">
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
            class="tab-pane fade show active"
            id="list-grid"
            role="tabpanel"
            aria-labelledby="list-grid-list"
          >
            <Dynamic_components />
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
                  <label class="btn btn-outline-info" for="enable_filter_info"
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
