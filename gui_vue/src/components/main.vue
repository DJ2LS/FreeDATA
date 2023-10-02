<script setup lang="ts">

import {saveSettingsToFile} from '../js/settingsHandler'

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);

import main_modals from './main_modals.vue'
import main_top_navbar from './main_top_navbar.vue'
import main_audio from './main_audio.vue'
import main_rig_control from './main_rig_control.vue'
import main_my_station from './main_my_station.vue'
import main_updater from './main_updater.vue'
import settings_view from './settings.vue'
import main_active_rig_control from './main_active_rig_control.vue'
import main_footer_navbar from './main_footer_navbar.vue'

import main_active_stats from './main_active_stats.vue'
import main_active_broadcasts from './main_active_broadcasts.vue'
import main_active_heard_stations from './main_active_heard_stations.vue'
import main_active_audio_level from './main_active_audio_level.vue'

import chat from './chat.vue'









function changeGuiDesign(design) {
  if (
    design != "default" &&
    design != "default_light" &&
    design != "default_dark" &&
    design != "default_auto"
  ) {
    var theme_path =
      "../node_modules/bootswatch/dist/" + design + "/bootstrap.min.css";
    document.getElementById("theme_selector").value = design;
    document.getElementById("bootstrap_theme").href = escape(theme_path);
  } else if (design == "default" || design == "default_light") {
    var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
    document.getElementById("theme_selector").value = "default_light";
    document.getElementById("bootstrap_theme").href = escape(theme_path);

    document.documentElement.setAttribute("data-bs-theme", "light");
  } else if (design == "default_dark") {
    var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
    document.getElementById("theme_selector").value = "default_dark";
    document.getElementById("bootstrap_theme").href = escape(theme_path);

    document.querySelector("html").setAttribute("data-bs-theme", "dark");
  } else if (design == "default_auto") {
    var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
    document.getElementById("theme_selector").value = "default_auto";
    document.getElementById("bootstrap_theme").href = escape(theme_path);

    // https://stackoverflow.com/a/57795495
    // check if dark mode or light mode used in OS
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      // dark mode
      document.documentElement.setAttribute("data-bs-theme", "dark");
    } else {
      document.documentElement.setAttribute("data-bs-theme", "light");
    }

    // also register event listener for automatic change
    window
      .matchMedia("(prefers-color-scheme: dark)")
      .addEventListener("change", (event) => {
        let newColorScheme = event.matches ? "dark" : "light";
        if (newColorScheme == "dark") {
          document.documentElement.setAttribute("data-bs-theme", "dark");
        } else {
          document.documentElement.setAttribute("data-bs-theme", "light");
        }
      });
  } else {
    var theme_path = "../node_modules/bootstrap/dist/css/bootstrap.min.css";
    document.getElementById("theme_selector").value = "default_light";
    document.getElementById("bootstrap_theme").href = escape(theme_path);

    document.documentElement.setAttribute("data-bs-theme", "light");
  }

  //update path to css file
  document.getElementById("bootstrap_theme").href = escape(theme_path);
}
</script>

<template>
  <html lang="en" data-bs-theme="light">
    <body>
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
                  style="-webkit-filter: blur(0px); filter: blur(0px)"
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

                  <div class="tab-content  d-none" id="nav-tabContent-Mesh">
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
                  FreeDATA - <span id="aboutVersion"></span>
                </h1>

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
                <chat/>



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

            <!------------------------------- RECEIVED FILES SIDEBAR ----------------------->
            <div
              class="offcanvas offcanvas-end"
              tabindex="-1"
              id="receivedFilesSidebar"
              aria-labelledby="receivedFilesSidebarLabel"
            >
              <div class="offcanvas-header p-2">
                <button
                  class="btn btn-sm btn-primary me-2"
                  id="openReceivedFilesFolder"
                  type="button"
                >
                  <i class="bi bi-folder2-open" style="font-size: 1rem"></i>
                </button>
                <h5 id="receivedFilesSidebarLabel">Filetransfer</h5>
                <button
                  type="button"
                  class="btn-close text-reset"
                  data-bs-dismiss="offcanvas"
                  aria-label="Close"
                ></button>
              </div>
              <div class="input-group input-group-sm p-1">
                <input type="file" class="form-control" id="dataModalFile" />
                <input
                  type="text"
                  class="form-control"
                  style="max-width: 6rem; text-transform: uppercase"
                  pattern="[A-Z]"
                  placeholder="DXcall"
                  id="dataModalDxCall"
                  maxlength="11"
                  aria-label="Input group"
                  aria-describedby="btnGroupAddon"
                />
                <button
                  type="button"
                  id="startTransmission"
                  data-bs-dismiss="offcanvas"
                  class="btn btn-success"
                >
                  Send
                </button>
              </div>
              <div class="offcanvas-body p-0">
                <!-- START OF TABLE FOR RECEIVED FILES-->
                <table class="table">
                  <thead>
                    <tr>
                      <th scope="col">Time</th>
                      <th scope="col">DXCall</th>
                      <!--<th scope="col">DXGrid</th>
                        <th scope="col">Distance</th>-->
                      <th scope="col">Filename</th>
                      <!--<th scope="col">SNR</th>-->
                    </tr>
                  </thead>
                  <tbody id="rx-data">
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
                <!-- END OF  RECEIVED FILES-->
              </div>
            </div>
            <!------------------------------- DATA SIDEBAR ----------------------->
            <div
              class="offcanvas offcanvas-end"
              tabindex="-1"
              id="transmitFileSidebar"
              aria-labelledby="transmitFileSidebarLabel"
            >
              <div class="offcanvas-header p-2">
                <h5 id="transmitFileSidebarLabel">Transmit Files</h5>
                <button
                  type="button"
                  class="btn-close text-reset"
                  data-bs-dismiss="offcanvas"
                  aria-label="Close"
                ></button>
              </div>
              <div class="offcanvas-body p-0">
                <!--<div id="transmitFileSidebar" class="sidebar shadow-lg rounded">-->
                <div class="container-fluid">
                  <div class="container mt-1">
                    <div class="row mb-1">
                      <div class="col">
                        <div class="card mb-0">
                          <div class="card-header p-1">
                            <strong>DX Station</strong>
                          </div>
                          <div class="card-body p-2">
                            <div class="row">
                              <div class="col-auto">
                                <!--
                                       <div class="input-group input-group-sm mb-0">

                                       	<input type="text" class="form-control" style="max-width: 6rem; text-transform:uppercase" pattern="[A-Z]" placeholder="DXcall" id="dataModalDxCall" maxlength="11" aria-label="Input group" aria-describedby="btnGroupAddon">
                                       </div>
                                       -->
                              </div>
                              <div class="col-auto">
                                <div class="input-group input-group-sm mb-0">
                                  <button
                                    class="btn btn-success"
                                    id="dataModalSendPing"
                                    type="button"
                                  >
                                    Ping
                                  </button>
                                  <span
                                    class="input-group-text text-secondary"
                                    id="dataModalPingACK"
                                    >ACK</span
                                  >
                                  <span
                                    class="input-group-text"
                                    id="dataModalPingDistance"
                                    >0000 km</span
                                  >
                                  <span
                                    class="input-group-text"
                                    id="dataModalPingDB"
                                    >0 dB</span
                                  >
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <!--col-->
                    </div>
                    <!--row-->
                    <div class="row mb-1">
                      <div class="col">
                        <div class="card mb-0">
                          <!--
                              <div class="card-header p-1"> <strong>Data</strong>
                              </div>
                              <div class="card-body p-2">
                              	<div class="input-group input-group-sm mb-0">
                              		<input type="file" class="form-control" id="dataModalFile">
                              		<label class="input-group-text" for="inputGroupFile02">kB</label>
                              	</div>
                              </div>
                              -->
                        </div>
                      </div>
                      <!--col-->
                    </div>
                    <!--row-->
                    <div class="row mb-1">
                      <div class="col">
                        <div class="card mb-0">
                          <div class="card-header p-1">
                            <strong>Mode</strong>
                          </div>
                          <div class="card-body p-2">
                            <div class="row">
                              <div class="col">
                                <div class="input-group input-group-sm">
                                  <span class="input-group-text">Mode</span>
                                  <select
                                    class="form-select form-select-sm"
                                    aria-label=".form-select-sm"
                                    id="datamode"
                                    disabled
                                  >
                                    <option selected value="255">AUTO</option>
                                    <!--<option value="232">HIGH SNR (DC1)</option>-->
                                    <!--<option value="231">MED SNR (DC3)</option>-->
                                    <!--<option value="230">LOW SNR (DC0)</option>-->
                                  </select>
                                </div>
                              </div>
                              <div class="col-auto">
                                <div class="input-group input-group-sm">
                                  <span class="input-group-text">Frames</span>
                                  <select
                                    class="form-select form-select-sm"
                                    aria-label=".form-select-sm"
                                    id="framesperburst"
                                    disabled
                                  >
                                    <option selected value="1">1</option>
                                  </select>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                        <!--col-->
                      </div>
                      <!--row-->
                    </div>
                    <div class="row mb-1">
                      <div class="col">
                        <!--
                           <button type="button" id="startTransmission" data-bs-dismiss="offcanvas" class="btn btn-success" style="width:100%">START TRANSMISSION</button>-->
                      </div>
                      <div class="col-md-auto">
                        <button
                          type="button"
                          id="stopTransmission"
                          class="btn btn-danger"
                          style="width: 100%"
                        >
                          STOP
                        </button>
                      </div>
                    </div>
                    <div class="row">
                      <div class="col"></div>
                    </div>
                    <!--row-->
                  </div>
                  <!--container-->
                  <!--</div>-->
                </div>
              </div>
            </div>
            <!--end of blur div -->
            <!---------------------------------------------------------------------- FOOTER AREA ------------------------------------------------------------>

            <div class="container">
              <main_footer_navbar />
            </div>
          </div>
        </div>
      </div>

      <main_modals />
    </body>
  </html>
</template>
