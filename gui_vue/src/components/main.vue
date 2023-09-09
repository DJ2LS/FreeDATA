<script setup lang="ts">

import {saveSettingsToFile} from '../js/settingsHandler'

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useStateStore } from '../store/stateStore.js';
const state = useStateStore(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);


import main_audio from './main_audio.vue'
import main_rig_control from './main_rig_control.vue'
import main_my_station from './main_my_station.vue'
import main_updater from './main_updater.vue'
import settings_view from './settings.vue'
import main_active_rig_control from './main_active_rig_control.vue'
import main_footer_navbar from './main_footer_navbar.vue'





import {startTNC, stopTNC} from '../js/daemon.js'

function startStopTNC(){


switch (state.tnc_running_state) {
  case 'stopped':
        startTNC()

    break;
  case 'running':
      stopTNC()

    break;
  default:

}


}





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
    <div class="row ">
        <div class="col-sm-auto bg-body-tertiary border-end">
            <div class="d-flex flex-sm-column flex-row flex-nowrap align-items-center sticky-top">

                  <div class="list-group" id="list-tab" role="tablist" style="margin-top: 100px">
                    <a class="list-group-item list-group-item-action active" id="list-tnc-list" data-bs-toggle="list" href="#list-tnc" role="tab" aria-controls="list-tnc"><i class="bi bi-house-door-fill h3"></i></a>
                    <a class="list-group-item list-group-item-action" id="list-messages-list" data-bs-toggle="list" href="#list-messages" role="tab" aria-controls="list-messages"><i class="bi bi-chat-text h3"></i></a>

                    <a class="list-group-item list-group-item-action" id="list-mesh-list" data-bs-toggle="list" href="#list-mesh" role="tab" aria-controls="list-mesh"><i class="bi bi-rocket h3"></i></a>
                    <a class="list-group-item list-group-item-action mt-2 border" id="list-info-list" data-bs-toggle="list" href="#list-info" role="tab" aria-controls="list-info"><i class="bi bi-info h3"></i></a>

                    <a class="list-group-item list-group-item-action" id="list-logger-list" data-bs-toggle="list" href="#list-logger" role="tab" aria-controls="list-logger"><i class="bi bi-activity h3"></i></a>

                    <a class="list-group-item list-group-item-action rounded-bottom" id="list-settings-list" data-bs-toggle="list" href="#list-settings" role="tab" aria-controls="list-settings"><i class="bi bi-gear-wide-connected h3"></i></a>


                    <a class="btn border btn-outline-danger list-group-item mt-5" id="stop_transmission_connection" data-bs-toggle="tooltip" data-bs-trigger="hover" data-bs-html="false" title="Abort session and stop transmissions"><i class="bi bi-sign-stop-fill h3"></i></a>




                  </div>


            </div>
        </div>
        <div class="col-sm min-vh-100 m-0 p-0">
            <!-- content -->




          <div class="tab-content" id="nav-tabContent">
      <div class="tab-pane fade show active" id="list-tnc" role="tabpanel" aria-labelledby="list-tnc-list">


    <!-- SECONDARY NAVBAR -->
    <nav class="navbar bg-body-tertiary border-bottom">
      <div style="margin-left: 100px">

      </div>

      <div>{{state.tnc_running_state}}

        <div class="btn-group" role="group">
          <button
            type="button"
            id="startTNC"
            class="btn btn-sm btn-outline-success"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            data-bs-html="false"
            title="Start the TNC. Please set your audio and radio settings first!"
            @click="startStopTNC()"
          >
            <i class="bi bi-play-fill"></i>
            <span class="ms-2">Start tnc</span>
          </button>
          <button
            type="button"
            id="stopTNC"
            class="btn btn-sm btn-outline-danger"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            data-bs-html="false"
            title="Stop the TNC."
            @click="startStopTNC()"
          >
            <i class="bi bi-stop-fill"></i>
            <span class="ms-2">Stop tnc</span>
          </button>
        </div>
        <button
          type="button"
          id="openHelpModalStartStopTNC"
          data-bs-toggle="modal"
          data-bs-target="#startStopTNCHelpModal"
          class="btn me-5 p-0 border-0"
        >
          <i class="bi bi-question-circle" style="font-size: 1rem"></i>
        </button>

      </div>

      <!--
	<div class="btn-toolbar" role="toolbar">

<span data-bs-placement="bottom"  data-bs-toggle="tooltip" data-bs-trigger="hover" data-bs-html="false"
			title="View the received files. This is currently under development!">


	   <button class="btn btn-sm btn-primary me-2" data-bs-toggle="offcanvas" data-bs-target="#receivedFilesSidebar" id="openReceivedFiles" type="button" > <strong>Files </strong>
	   <i class="bi bi-file-earmark-arrow-up-fill" style="font-size: 1rem; color: white;"></i>
	   <i class="bi bi-file-earmark-arrow-down-fill" style="font-size: 1rem; color: white;"></i>
	   </button>
	   </span> <span data-bs-placement="bottom"  data-bs-toggle="tooltip" data-bs-trigger="hover" data-bs-html="false" title="Send files through HF. This is currently under development!">
	   <button class="btn btn-sm btn-primary me-2" id="openDataModule" data-bs-toggle="offcanvas" data-bs-target="#transmitFileSidebar" type="button" style="display: None;"> <strong>TX File </strong>
	   <i class="bi bi-file-earmark-arrow-up-fill" style="font-size: 1rem; color: white;"></i>
	   </button>

		</span> <span data-bs-placement="bottom"  data-bs-toggle="tooltip" data-bs-trigger="hover" data-bs-html="true"
			title="Settings and Info">

		</span>
	</div>
	 -->
    </nav>

    <div id="blurdiv" style="-webkit-filter: blur(0px); filter: blur(0px)">
      <!--beginn of blur div -->
      <!-------------------------------- MAIN AREA ---------------->

      <!------------------------------------------------------------------------------------------>
      <div class="container p-3">
        <div class="row collapse multi-collapse show mt-4" id="collapseFirstRow">
          <div class="col">
              <main_audio/>
          </div>
          <div class="col">
            <main_rig_control/>
          </div>
        </div>
        <div
          class="row collapse multi-collapse show mt-4"
          id="collapseSecondRow"
        >
          <div class="col">
            <main_my_station/>
          </div>
          <div class="col">
          <main_updater/>
        </div>
        </div>

      </div>
      <div class="container">
        <div class="row collapse multi-collapse" id="collapseThirdRow">


         <main_active_rig_control/>



          <div class="col-5">
            <div class="card mb-1">
              <div class="card-header p-1">
                <div class="container">

                  <div class="row">
                    <div class="col-1">
                      <i class="bi bi-volume-up" style="font-size: 1.2rem"></i>
                    </div>
                    <div class="col-5">
                      <strong class="fs-5">Audio level</strong>
                    </div>
                    <div class="col-5">
                      <button
                        type="button"
                        id="audioModalButton"
                        data-bs-toggle="modal"
                        data-bs-target="#audioModal"
                        class="btn btn-sm btn-outline-secondary"
                      >
                        Tune
                      </button>
                      <button
                        type="button"
                        id="startStopRecording"
                        class="btn btn-sm btn-outline-danger"
                      >
                        Record audio
                      </button>
                    </div>
                    <div class="col-1 text-end">
                      <button
                        type="button"
                        id="openHelpModalAudioLevel"
                        data-bs-toggle="modal"
                        data-bs-target="#audioLevelHelpModal"
                        class="btn m-0 p-0 border-0"
                      >
                        <i
                          class="bi bi-question-circle"
                          style="font-size: 1rem"
                        ></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card-body p-2">
                <div class="container">
                  <div class="row">
                    <div class="col-sm">
                      <div class="progress mb-0" style="height: 22px">
                        <div
                          class="progress-bar progress-bar-striped bg-primary force-gpu"
                          id="noise_level"
                          role="progressbar"
                          style="width: {{state.s_meter_strength_percent}}%;"
                          aria-valuenow="{{state.s_meter_strength_percent}}"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <p
                          class="justify-content-center d-flex position-absolute w-100"
                          id="noise_level_value"
                        >
                          S-Meter: {{state.s_meter_strength_raw}} dB
                        </p>
                      </div>
                      <div class="progress mb-0" style="height: 8px">
                        <div
                          class="progress-bar progress-bar-striped bg-warning"
                          role="progressbar"
                          style="width: 1%"
                          aria-valuenow="1"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <div
                          class="progress-bar bg-success"
                          role="progressbar"
                          style="width: 89%"
                          aria-valuenow="50"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <div
                          class="progress-bar progress-bar-striped bg-warning"
                          role="progressbar"
                          style="width: 20%"
                          aria-valuenow="20"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <div
                          class="progress-bar progress-bar-striped bg-danger"
                          role="progressbar"
                          style="width: 29%"
                          aria-valuenow="29"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                      </div>
                    </div>
                    <div class="col-sm">
                      <div class="progress mb-0" style="height: 22px">
                        <div
                          class="progress-bar progress-bar-striped bg-primary force-gpu"
                          id="dbfs_level"
                          role="progressbar"
                          style="width: 0%"
                          aria-valuenow="0"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <p
                          class="justify-content-center d-flex position-absolute w-100"
                          id="dbfs_level_value"
                        >
                          dBFS (Audio Level)
                        </p>
                      </div>
                      <div class="progress mb-0" style="height: 8px">
                        <div
                          class="progress-bar progress-bar-striped bg-warning"
                          role="progressbar"
                          style="width: 1%"
                          aria-valuenow="1"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <div
                          class="progress-bar bg-success"
                          role="progressbar"
                          style="width: 89%"
                          aria-valuenow="50"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <div
                          class="progress-bar progress-bar-striped bg-warning"
                          role="progressbar"
                          style="width: 20%"
                          aria-valuenow="20"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                        <div
                          class="progress-bar progress-bar-striped bg-danger"
                          role="progressbar"
                          style="width: 29%"
                          aria-valuenow="29"
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col">
            <div class="card mb-1">
              <div class="card-header p-1">
                <div class="container">
                  <div class="row">
                    <div class="col-1">
                      <i class="bi bi-broadcast" style="font-size: 1.2rem"></i>
                    </div>
                    <div class="col-10">
                      <strong class="fs-5">Broadcasts</strong>
                    </div>
                    <div class="col-1 text-end">
                      <button
                        type="button"
                        id="openHelpModalBroadcasts"
                        data-bs-toggle="modal"
                        data-bs-target="#broadcastsHelpModal"
                        class="btn m-0 p-0 border-0"
                      >
                        <i
                          class="bi bi-question-circle"
                          style="font-size: 1rem"
                        ></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card-body p-2">
                <div class="row">
                  <div class="col-md-auto">
                    <div class="input-group input-group-sm mb-0">
                      <input
                        type="text"
                        class="form-control"
                        style="max-width: 6rem; text-transform: uppercase"
                        placeholder="DXcall"
                        pattern="[A-Z]*"
                        id="dxCall"
                        maxlength="11"
                        aria-label="Input group"
                        aria-describedby="btnGroupAddon"
                      />
                      <button
                        class="btn btn-sm btn-outline-secondary ms-1"
                        id="sendPing"
                        type="button"
                        data-bs-placement="bottom"
                        data-bs-toggle="tooltip"
                        data-bs-trigger="hover"
                        data-bs-html="false"
                        title="Send a ping request to a remote station"
                      >
                        Ping
                      </button>
                      <!-- disabled because it's causing confusion TODO: remove entire code some day
                      <button
                        class="btn btn-sm btn-outline-success ms-1"
                        id="openARQSession"
                        type="button"
                        data-bs-placement="bottom"
                        data-bs-toggle="tooltip"
                        data-bs-trigger="hover"
                        data-bs-html="false"
                        title="connect to a remote station"
                      >
                        <i
                          class="bi bi-arrows-angle-contract"
                          style="font-size: 0.8rem"
                        ></i>
                      </button>
                      <button
                        class="btn btn-sm btn-outline-danger"
                        id="closeARQSession"
                        type="button"
                        data-bs-placement="bottom"
                        data-bs-toggle="tooltip"
                        data-bs-trigger="hover"
                        data-bs-html="false"
                        title="disconnect from a remote station"
                      >

                        <i
                          class="bi bi-arrows-angle-expand"
                          style="font-size: 0.8rem"
                        ></i>
                      </button>
                      -->

                      <button
                        class="btn btn-sm btn-outline-secondary ms-1"
                        id="sendCQ"
                        type="button"
                        title="Send a CQ to the world"
                      >
                        Call CQ
                      </button>

                      <button
                        type="button"
                        id="startBeacon"
                        class="btn btn-sm btn-outline-secondary ms-1"
                        title="Toggle beacon mode. The interval can be set in settings. While sending a beacon, you can receive ping requests and open a datachannel. If a datachannel is opened, the beacon pauses."
                      >
                        <i class="bi bi-soundwave"></i> Toggle beacon
                      </button>
                    </div>
                  </div>
                </div>
                <!-- end of row-->
              </div>
            </div>
          </div>
        </div>
        <div class="row collapse multi-collapse mt-3" id="collapseFourthRow">
          <div class="col-5">
            <div class="card mb-1">
              <div class="card-header p-1">
                <div class="container">
                  <div class="row">
                    <div class="col-11">
                      <div
                        class="btn-group btn-group-sm"
                        role="group"
                        aria-label="waterfall-scatter-switch toggle button group"
                      >
                        <input
                          type="radio"
                          class="btn-check"
                          name="waterfall-scatter-switch"
                          id="waterfall-scatter-switch1"
                          autocomplete="off"
                          checked
                        />
                        <label
                          class="btn btn-sm btn-outline-secondary"
                          for="waterfall-scatter-switch1"
                          ><strong><i class="bi bi-water"></i></strong>
                        </label>
                        <input
                          type="radio"
                          class="btn-check"
                          name="waterfall-scatter-switch"
                          id="waterfall-scatter-switch2"
                          autocomplete="off"
                        />
                        <label
                          class="btn btn-sm btn-outline-secondary"
                          for="waterfall-scatter-switch2"
                          ><strong><i class="bi bi-border-outer"></i></strong>
                        </label>
                        <input
                          type="radio"
                          class="btn-check"
                          name="waterfall-scatter-switch"
                          id="waterfall-scatter-switch3"
                          autocomplete="off"
                        />
                        <label
                          class="btn btn-sm btn-outline-secondary"
                          for="waterfall-scatter-switch3"
                          ><strong><i class="bi bi-graph-up-arrow"></i></strong>
                        </label>
                      </div>
                      <div
                        class="btn-group"
                        role="group"
                        aria-label="Busy indicators"
                      >
                        <button
                          class="btn btn-sm btn-secondary"
                          id="channel_busy"
                          type="button"
                          data-bs-placement="top"
                          data-bs-toggle="tooltip"
                          data-bs-trigger="hover"
                          data-bs-html="true"
                          title="Channel busy state: <strong class='text-success'>not busy</strong> / <strong class='text-danger'>busy </strong>"
                        >
                          busy
                        </button>
                        <button
                          class="btn btn-sm btn-outline-secondary"
                          id="c2_busy"
                          type="button"
                          data-bs-placement="top"
                          data-bs-toggle="tooltip"
                          data-bs-trigger="hover"
                          data-bs-html="true"
                          title="Recieving data: illuminates <strong class='text-success'>green</strong> if receiving codec2 data"
                        >
                          signal
                        </button>
                      </div>
                    </div>

                    <div class="col-1 text-end">
                      <button
                        type="button"
                        id="openHelpModalWaterfall"
                        data-bs-toggle="modal"
                        data-bs-target="#waterfallHelpModal"
                        class="btn m-0 p-0 border-0"
                      >
                        <i
                          class="bi bi-question-circle"
                          style="font-size: 1rem"
                        ></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card-body p-1" style="height: 200px">
                <!--278px-->
                <canvas
                  id="waterfall"
                  style="position: relative; z-index: 2"
                  class="force-gpu"
                ></canvas>
                <canvas
                  id="scatter"
                  style="position: relative; z-index: 1"
                  class="force-gpu"
                ></canvas>
                <canvas
                  id="chart"
                  style="position: relative; z-index: 1"
                  class="force-gpu"
                ></canvas>
              </div>
            </div>
          </div>
          <div class="col">
            <div class="card mb-1" style="height: 240px">
              <!--325px-->
              <div class="card-header p-1">
                <div class="container">
                  <div class="row">
                    <div class="col-auto">
                      <i
                        class="bi bi-list-columns-reverse"
                        style="font-size: 1.2rem"
                      ></i>
                    </div>
                    <div class="col-10">
                      <strong class="fs-5">Heard stations</strong>
                    </div>
                    <div class="col-1 text-end">
                      <button
                        type="button"
                        id="openHelpModalHeardStations"
                        data-bs-toggle="modal"
                        data-bs-target="#heardStationsHelpModal"
                        class="btn m-0 p-0 border-0"
                      >
                        <i
                          class="bi bi-question-circle"
                          style="font-size: 1rem"
                        ></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card-body p-0" style="overflow-y: overlay">
                <div class="table-responsive">
                  <!-- START OF TABLE FOR HEARD STATIONS -->
                  <table class="table table-sm" id="tblHeardStationList">
                    <thead>
                      <tr>
                        <th scope="col" id="thTime">
                          <i id="hslSort" class="bi bi-sort-up"></i>Time
                        </th>
                        <th scope="col" id="thFreq">Frequency</th>
                        <th>&nbsp;</th>
                        <th scope="col" id="thDxcall">DXCall</th>
                        <th scope="col" id="thDxgrid">DXGrid</th>
                        <th scope="col" id="thDist">Distance</th>
                        <th scope="col" id="thType">Type</th>
                        <th scope="col" id="thSnr">SNR (rx/dx)</th>
                        <!--<th scope="col">Off</th>-->
                      </tr>
                    </thead>
                    <tbody id="heardstations"></tbody>
                  </table>
                </div>
                <!-- END OF HEARD STATIONS TABLE -->
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>









      </div>

      <div class="tab-pane fade" id="list-mesh" role="tabpanel" aria-labelledby="list-mesh-list">
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

            <div class="tab-content" id="nav-tabContent-Mesh">
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
          <button id="transmit_mesh_ping" type="button" class="btn btn-primary">
            mesh ping
          </button>
        </div>
      </div>
    </div>

</div>

      </div>
      <div class="tab-pane fade" id="list-info" role="tabpanel" aria-labelledby="list-info-list">




        <h1 class="modal-title fs-5" id="aboutModalLabel">FreeDATA -  <span id="aboutVersion"></span></h1>

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
                    >Website</button>
                  </div>
                  <div class="btn-group">
                    <button
                      class="btn btn-secondary bi bi-github me-2"
                      id="ghUrl"
                      data-bs-toggle="tooltip"
                      data-bs-trigger="hover"
                      title="Github"
                      role="button"
                    >Github</button>
                  </div>
                  <div class="btn-group">
                    <button
                      class="btn btn-secondary bi bi-wikipedia me-2"
                      id="wikiUrl"
                      data-bs-toggle="tooltip"
                      data-bs-trigger="hover"
                      title="Wiki"
                      role="button"
                    >Wiki</button>
                  </div>
                  <div class="btn-group">
                    <button
                      class="btn btn-secondary bi bi-discord"
                      id="discordUrl"
                      data-bs-toggle="tooltip"
                      data-bs-trigger="hover"
                      title="Discord"
                      role="button"
                    >Discord</button>
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
      <div class="tab-pane fade" id="list-messages" role="tabpanel" aria-labelledby="list-messages-list">

    <div class="container-fluid m-0 p-0">


                <!------ chat navbar ---------------------------------------------------------------------->

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
                <i class="bi bi-pencil-square" style="font-size: 1.2rem"></i>
              </button>

              <button
                type="button"
                id="userModalButton"
                data-bs-toggle="modal"
                data-bs-target="#userModal"
                class="btn btn-sm btn-primary ms-2"
                title="My station info"
              >
                <i class="bi bi-person" style="font-size: 1.2rem"></i>
              </button>
              <button
                type="button"
                id="sharedFolderButton"
                data-bs-toggle="modal"
                data-bs-target="#sharedFolderModal"
                class="btn btn-sm btn-primary"
                title="My shared folder"
              >
                <i class="bi bi-files" style="font-size: 1.2rem"></i>
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
                <i class="bi bi-person" style="font-size: 1.2rem"></i>
              </button>

              <button
                type="button"
                id="sharedFolderDXButton"
                data-bs-toggle="modal"
                data-bs-target="#sharedFolderModalDX"
                class="btn btn-sm btn-outline-secondary me-2"
                title="Request remote station's shared files"
              >
                <i class="bi bi-files" style="font-size: 1.2rem"></i>
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
                    <label class="form-check-label" for="chkMessage">
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

                    <label class="form-check-label" for="chkNewMessage">
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
                    <label class="form-check-label" for="chkPingAck">
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
                    <label class="form-check-label" for="chkBeacon">
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
                    <label class="form-check-label" for="chkRequest">
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
                    <label class="form-check-label" for="chkResponse">
                      Responses
                    </label>
                  </div>
                </div>
                <button type="button" class="btn btn-primary" id="btnFilter">
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
              <ul class="dropdown-menu" aria-labelledby="chatSettingsDropDown">
                <li>
                  <a
                    class="dropdown-item bg-danger text-white"
                    id="delete_selected_chat"
                    href="#"
                    ><i class="bi bi-person-x" style="font-size: 1rem"></i>
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


      <div class="row h-100 ms-1 mt-1 me-1">
        <div class="col-4">
          <!------Chats area ---------------------------------------------------------------------->
          <div class="container-fluid m-0 p-0">
            <!--<div class="input-group bottom-0 m-0 w-100">
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
                <i class="bi bi-pencil-square" style="font-size: 1.2rem"></i>
              </button>

              <button
                type="button"
                id="userModalButton"
                data-bs-toggle="modal"
                data-bs-target="#userModal"
                class="btn btn-sm btn-primary ms-2"
                title="My station info"
              >
                <i class="bi bi-person" style="font-size: 1.2rem"></i>
              </button>
              <button
                type="button"
                id="sharedFolderButton"
                data-bs-toggle="modal"
                data-bs-target="#sharedFolderModal"
                class="btn btn-sm btn-primary"
                title="My shared folder"
              >
                <i class="bi bi-files" style="font-size: 1.2rem"></i>
              </button>
            </div>-->
          </div>
          <div class="overflow-auto vh-100">
            <div
              class="list-group overflow-auto"
              id="list-tab-chat"
              role="tablist"
              style="height: calc(100vh - 70px)"
            ></div>
          </div>
        </div>
        <div class="col-8 border-start vh-100 p-0">



                   <div
      class="position-absolute container bottom-0 end-0 mb-5"
      style="z-index: 100; display: none"
      id="emojipickercontainer"
    >
      <emoji-picker
        locale="en"
        class="position-absolute bottom-0 end-0 p-1 mb-2"
        data-source="../node_modules/emoji-picker-element-data/en/emojibase/data.json"
      ></emoji-picker>
    </div>


          <!------messages area ---------------------------------------------------------------------->
          <div
            class="container overflow-auto"
            id="message-container"
            style="height: calc(100% - 200px)"
          >





            <div class="tab-content" id="nav-tabContent-Chat"></div>
            <!--<div class="container position-absolute bottom-0">-->
          </div>
          <!-- </div>-->
          <div class="container-fluid mt-2 p-0">
            <input
              type="checkbox"
              id="expand_textarea"
              class="btn-check"
              autocomplete="off"
            />
            <label
              class="btn d-flex justify-content-center"
              id="expand_textarea_label"
              for="expand_textarea"
              ><i
                id="expand_textarea_button"
                class="bi bi-chevron-compact-up"
              ></i
            ></label>

            <div class="input-group bottom-0 ms-2">
              <!--<input class="form-control" maxlength="8" style="max-width: 6rem; text-transform:uppercase; display:none" id="chatModuleDxCall" placeholder="DX CALL"></input>-->
              <!--<button class="btn btn-sm btn-primary me-2" id="emojipickerbutton" type="button">-->
              <div class="input-group-text">
                <i
                  id="emojipickerbutton"
                  class="bi bi-emoji-smile p-0"
                  style="font-size: 1rem"
                ></i>
              </div>

              <textarea
                class="form-control"
                rows="1"
                id="chatModuleMessage"
                placeholder="Message - Send with [Enter]"
              ></textarea>

              <div class="input-group-text me-3">
                <i
                  class="bi bi-paperclip"
                  style="font-size: 1rem"
                  id="selectFilesButton"
                ></i>

                <button
                  class="btn btn-sm btn-secondary d-none invisible"
                  id="sendMessage"
                  type="button"
                >
                  <i class="bi bi-send" style="font-size: 1.2rem"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- user modal -->

    <div
      class="modal fade"
      id="userModal"
      tabindex="-1"
      aria-labelledby="userModalLabel"
      aria-hidden="true"
    >
      <div class="modal-dialog" style="max-width: 600px">
        <div class="modal-content">
          <div class="card mb-1 border-0">
            <div class="row g-0">
              <div class="col-md-4">
                <div class="row position-relative p-0 m-0">
                  <div class="col p-0 m-0">
                    <img
                      src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgZmlsbD0iY3VycmVudENvbG9yIiBjbGFzcz0iYmkgYmktcGVyc29uLWJvdW5kaW5nLWJveCIgdmlld0JveD0iMCAwIDE2IDE2Ij4KICA8cGF0aCBkPSJNMS41IDFhLjUuNSAwIDAgMC0uNS41djNhLjUuNSAwIDAgMS0xIDB2LTNBMS41IDEuNSAwIDAgMSAxLjUgMGgzYS41LjUgMCAwIDEgMCAxaC0zek0xMSAuNWEuNS41IDAgMCAxIC41LS41aDNBMS41IDEuNSAwIDAgMSAxNiAxLjV2M2EuNS41IDAgMCAxLTEgMHYtM2EuNS41IDAgMCAwLS41LS41aC0zYS41LjUgMCAwIDEtLjUtLjV6TS41IDExYS41LjUgMCAwIDEgLjUuNXYzYS41LjUgMCAwIDAgLjUuNWgzYS41LjUgMCAwIDEgMCAxaC0zQTEuNSAxLjUgMCAwIDEgMCAxNC41di0zYS41LjUgMCAwIDEgLjUtLjV6bTE1IDBhLjUuNSAwIDAgMSAuNS41djNhMS41IDEuNSAwIDAgMS0xLjUgMS41aC0zYS41LjUgMCAwIDEgMC0xaDNhLjUuNSAwIDAgMCAuNS0uNXYtM2EuNS41IDAgMCAxIC41LS41eiIvPgogIDxwYXRoIGQ9Ik0zIDE0cy0xIDAtMS0xIDEtNCA2LTQgNiAzIDYgNC0xIDEtMSAxSDN6bTgtOWEzIDMgMCAxIDEtNiAwIDMgMyAwIDAgMSA2IDB6Ii8+Cjwvc3ZnPg=="
                      class="img-fluid rounded-start w-100"
                      alt="..."
                      id="user_info_image"
                    />
                  </div>
                  <div
                    class="col position-absolute image-overlay text-white justify-content-center align-items-center d-flex align-middle h-100 opacity-0"
                    id="userImageSelector"
                  >
                    <i class="bi bi-upload" style="font-size: 2.2rem"></i>
                  </div>
                </div>
              </div>
              <div class="col-md-8">
                <div class="card-body">
                  <div class="input-group input-group-sm mb-1">
                    <span class="input-group-text"
                      ><i class="bi bi-pass"></i
                    ></span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Callsign"
                      id="user_info_callsign"
                      aria-label="Call"
                      aria-describedby="basic-addon1"
                    />
                    <span class="input-group-text"
                      ><i class="bi bi-person-vcard"></i
                    ></span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="name"
                      id="user_info_name"
                      aria-label="Name"
                      aria-describedby="basic-addon1"
                    />
                    <span class="input-group-text"
                      ><i class="bi bi-sunrise"></i
                    ></span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="age"
                      id="user_info_age"
                      aria-label="age"
                      aria-describedby="basic-addon1"
                    />
                  </div>

                  <div class="input-group input-group-sm mb-1">
                    <span class="input-group-text"
                      ><i class="bi bi-house"></i
                    ></span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Location"
                      id="user_info_location"
                      aria-label="Name"
                      aria-describedby="basic-addon1"
                    />
                    <span class="input-group-text"
                      ><i class="bi bi-pin-map"></i
                    ></span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Grid"
                      id="user_info_gridsquare"
                      aria-label="Name"
                      aria-describedby="basic-addon1"
                    />
                  </div>

                  <div class="input-group input-group-sm mb-1">
                    <span class="input-group-text"
                      ><i class="bi bi-projector"></i
                    ></span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Radio"
                      id="user_info_radio"
                      aria-label="Name"
                      aria-describedby="basic-addon1"
                    />

                    <span class="input-group-text"
                      ><i class="bi bi-broadcast-pin"></i
                    ></span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Antenna"
                      id="user_info_antenna"
                      aria-label="Name"
                      aria-describedby="basic-addon1"
                    />
                  </div>

                  <div class="input-group input-group-sm mb-1">
                    <span class="input-group-text"
                      ><i class="bi bi-envelope"></i
                    ></span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Email"
                      id="user_info_email"
                      aria-label="Name"
                      aria-describedby="basic-addon1"
                    />

                    <span class="input-group-text"
                      ><i class="bi bi-globe"></i
                    ></span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Website"
                      id="user_info_website"
                      aria-label="Name"
                      aria-describedby="basic-addon1"
                    />
                  </div>
                  <div class="input-group input-group-sm mb-1">
                    <span class="input-group-text"
                      ><i class="bi bi-info-circle"></i
                    ></span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="Comments"
                      id="user_info_comments"
                      aria-label="Comments"
                      aria-describedby="basic-addon1"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <button
            type="button"
            class="btn btn-primary"
            data-bs-dismiss="modal"
            aria-label="Close"
            id="userInfoSave"
          >
            Save & Close
          </button>
        </div>
      </div>
    </div>
    <!-- dx user modal -->
    <div
      class="modal fade"
      id="userModalDX"
      tabindex="-1"
      aria-labelledby="userModalDXLabel"
      aria-hidden="true"
    >
      <div class="modal-dialog" style="max-width: 600px">
        <div class="modal-content">
          <div class="card mb-1 border-0">
            <div class="row g-0">
              <div class="col-md-4">
                <img
                  src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgZmlsbD0iY3VycmVudENvbG9yIiBjbGFzcz0iYmkgYmktcGVyc29uLWJvdW5kaW5nLWJveCIgdmlld0JveD0iMCAwIDE2IDE2Ij4KICA8cGF0aCBkPSJNMS41IDFhLjUuNSAwIDAgMC0uNS41djNhLjUuNSAwIDAgMS0xIDB2LTNBMS41IDEuNSAwIDAgMSAxLjUgMGgzYS41LjUgMCAwIDEgMCAxaC0zek0xMSAuNWEuNS41IDAgMCAxIC41LS41aDNBMS41IDEuNSAwIDAgMSAxNiAxLjV2M2EuNS41IDAgMCAxLTEgMHYtM2EuNS41IDAgMCAwLS41LS41aC0zYS41LjUgMCAwIDEtLjUtLjV6TS41IDExYS41LjUgMCAwIDEgLjUuNXYzYS41LjUgMCAwIDAgLjUuNWgzYS41LjUgMCAwIDEgMCAxaC0zQTEuNSAxLjUgMCAwIDEgMCAxNC41di0zYS41LjUgMCAwIDEgLjUtLjV6bTE1IDBhLjUuNSAwIDAgMSAuNS41djNhMS41IDEuNSAwIDAgMS0xLjUgMS41aC0zYS41LjUgMCAwIDEgMC0xaDNhLjUuNSAwIDAgMCAuNS0uNXYtM2EuNS41IDAgMCAxIC41LS41eiIvPgogIDxwYXRoIGQ9Ik0zIDE0cy0xIDAtMS0xIDEtNCA2LTQgNiAzIDYgNC0xIDEtMSAxSDN6bTgtOWEzIDMgMCAxIDEtNiAwIDMgMyAwIDAgMSA2IDB6Ii8+Cjwvc3ZnPg=="
                  class="img-fluid rounded-start w-100"
                  alt="..."
                  id="dx_user_info_image"
                />
              </div>
              <div class="col-md-8">
                <div class="card-body">
                  <h5>
                    <span
                      class="badge bg-secondary"
                      id="dx_user_info_callsign"
                    ></span>
                    -
                    <span
                      class="badge bg-secondary"
                      id="dx_user_info_name"
                    ></span>
                    <span
                      class="badge bg-secondary"
                      id="dx_user_info_age"
                    ></span>
                  </h5>

                  <ul class="card-text list-unstyled">
                    <li>
                      <strong class="col"><i class="bi bi-house"></i> </strong
                      ><span id="dx_user_info_location"></span> (<span
                        id="dx_user_info_gridsquare"
                      ></span
                      >)
                    </li>
                    <li>
                      <strong class="col"
                        ><i class="bi bi-envelope"></i> </strong
                      ><span id="dx_user_info_email"></span>
                    </li>
                    <li>
                      <strong class="col"><i class="bi bi-globe"></i> </strong
                      ><span id="dx_user_info_website"></span>
                    </li>
                    <li>
                      <strong class="col"
                        ><i class="bi bi-broadcast-pin"></i> </strong
                      ><span id="dx_user_info_antenna"></span>
                    </li>
                    <li>
                      <strong class="col"
                        ><i class="bi bi-projector"></i> </strong
                      ><span id="dx_user_info_radio"></span>
                    </li>
                    <li>
                      <strong class="col"
                        ><i class="bi bi-info-circle"></i> </strong
                      ><span id="dx_user_info_comments"></span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div class="input-group input-group-sm m-0 p-0">
            <button
              type="button"
              class="btn btn-warning w-75"
              aria-label="Request"
              id="requestUserInfo"
            >
              Request user data (about 20kBytes!)
            </button>

            <button
              type="button"
              class="btn btn-primary w-25"
              data-bs-dismiss="modal"
              aria-label="Close"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- user shared folder -->
    <div
      class="modal fade"
      id="sharedFolderModal"
      tabindex="-1"
      aria-labelledby="sharedFolderModalLabel"
      aria-hidden="true"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title fs-5" id="sharedFolderModalLabel">
              My Shared folder
              <button
                type="button"
                class="btn btn-primary"
                id="openSharedFilesFolder"
              >
                <i class="bi bi-archive"></i>
              </button>
            </h1>

            <button
              type="button"
              class="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>

          <div class="modal-body">
            <div class="container-fluid p-0">
              <div class="center mb-1">
                <div class="badge text-bg-info">
                  <i class="bi bi-info"></i> Change folder in settings!
                </div>
              </div>
              <div class="table-responsive">
                <!-- START OF TABLE FOR SHARED FOLDER -->
                <table
                  class="table table-sm table-hover table-bordered align-middle"
                >
                  <thead>
                    <tr>
                      <th scope="col">#</th>
                      <th scope="col">Name</th>
                      <th scope="col">Type</th>
                      <th scope="col">Size</th>
                    </tr>
                  </thead>
                  <tbody id="sharedFolderTable"></tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- HELP MODAL -->
    <div
      class="modal fade"
      data-bs-backdrop="static"
      tabindex="-1"
      id="chatHelpModal"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Chat Help</h5>
            <button
              type="button"
              class="btn btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="card mb-3">
              <div class="card-body">
                <p class="card-text">
                  Welcome to the chat window. Heard stations are listed in the
                  list on the left. Clicking on a station will show messages
                  sent and/or received from the selected station. Additional
                  help is available on various extra features below.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <button type="button" class="btn btn-sm btn-primary ms-2">
                  <i class="bi bi-person" style="font-size: 1.2rem"></i>
                </button>
                <p class="card-text">
                  Set your station information and picture. This information can
                  be requested by a remote station and can be enabled/disabled
                  via settings.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-secondary ms-2"
                >
                  <i class="bi bi-person" style="font-size: 1.2rem"></i>
                </button>
                <p class="card-text">
                  Request the selected station's information.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-secondary ms-2"
                >
                  <i class="bi bi-files" style="font-size: 1.2rem"></i>
                </button>
                <p class="card-text">
                  Request the selected station's shared file(s) list. Clicking
                  <button type="button" class="btn btn-sm btn-primary ms-2">
                    <i class="bi bi-files" style="font-size: 1.2rem"></i>
                  </button>
                  will allow you to preview your shared files. Shared file can
                  be enabled/disabled in settings.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <button
                  type="button"
                  class="btn btn-small btn-outline-primary dropdown-toggle me-2"
                >
                  <i class="bi bi-funnel-fill"></i>
                </button>
                <p class="card-text">
                  The filter button allows you to show or hide certain types of
                  messages. A lot of data is logged and this allows you to
                  modify what is shown. By default sent and received messages
                  and ping acknowlegements are displayed.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- dx user shared folder -->
    <div
      class="modal fade"
      id="sharedFolderModalDX"
      tabindex="-1"
      aria-labelledby="sharedFolderModalDXLabel"
      aria-hidden="true"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title fs-5" id="sharedFolderModalDXLabel">
              Shared folder
            </h1>
            <button
              type="button"
              class="btn btn-primary m-2"
              aria-label="Request"
              id="requestSharedFolderList"
            >
              <i class="bi bi-arrow-repeat"></i>
            </button>

            <button
              type="button"
              class="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="container-fluid">
              <div class="table-responsive">
                <!-- START OF TABLE FOR SHARED FOLDER DX -->
                <table
                  class="table table-sm table-hover table-bordered align-middle"
                >
                  <thead>
                    <tr>
                      <th scope="col">#</th>
                      <th scope="col">Name</th>
                      <th scope="col">Type</th>
                      <th scope="col">Size</th>
                    </tr>
                  </thead>
                  <tbody id="sharedFolderTableDX"></tbody>
                </table>
              </div>
            </div>
            <div class="modal-footer">
              <div class="input-group input-group-sm m-0 p-0"></div>
            </div>
          </div>
        </div>
      </div>
    </div>



      </div>
      <div class="tab-pane fade" id="list-logger" role="tabpanel" aria-labelledby="list-logger-list">
        <div class="container">
              <nav class="navbar fixed-top bg-body-tertiary border-bottom" style="margin-left: 87px">
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
        <label class="btn btn-outline-primary" for="enable_filter_debug"
          >debug</label
        >

        <input
          type="checkbox"
          class="btn-check"
          id="enable_filter_warning"
          autocomplete="off"
        />
        <label class="btn btn-outline-warning" for="enable_filter_warning"
          >warning</label
        >

        <input
          type="checkbox"
          class="btn-check"
          id="enable_filter_error"
          autocomplete="off"
        />
        <label class="btn btn-outline-danger" for="enable_filter_error"
          >error</label
        >
      </div>
    </nav >

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



    <settings_view/>





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
                  <div class="card-header p-1"><strong>DX Station</strong></div>
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
                          <span class="input-group-text" id="dataModalPingDB"
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
                  <div class="card-header p-1"><strong>Mode</strong></div>
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
     <main_footer_navbar/>
    </div>



                            </div>
    </div>
</div>







    <!-- HELP MODALS AUDIO -->
    <div
      class="modal fade"
      data-bs-backdrop="static"
      tabindex="-1"
      id="audioHelpModal"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Help</h5>
            <button
              type="button"
              class="btn btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="card mb-3">
              <div class="card-body">
                <div class="input-group input-group-sm mb-1">
                  <span class="input-group-text">
                    <i class="bi bi-mic-fill" style="font-size: 1rem"></i>
                  </span>
                  <select
                    class="form-select form-select-sm"
                    aria-label=".form-select-sm"
                    disabled
                  >
                    <!-- 					 					<option selected value="3011">USB Interface</option>-->
                  </select>
                </div>
                <p class="card-text">
                  Select your audio device for transmitting. It
                  <strong>must</strong> be using a sample rate of
                  <strong>48000Hz</strong>
                </p>
              </div>
            </div>

            <div class="card">
              <div class="card-body">
                <div class="input-group input-group-sm">
                  <span class="input-group-text">
                    <i class="bi bi-volume-up" style="font-size: 1rem"></i>
                  </span>
                  <select
                    class="form-select form-select-sm"
                    aria-label=".form-select-sm"
                    disabled
                  ></select>
                </div>
                <p class="card-text">
                  Select your audio device for receiving. It
                  <strong>must</strong> be using a sample rate of
                  <strong>48000Hz</strong>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- HELP MODALS RIGCONTROL -->
    <div
      class="modal fade"
      data-bs-backdrop="static"
      tabindex="-1"
      id="rigcontrolHelpModal"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Help</h5>
            <button
              type="button"
              class="btn btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">Rig Control</h5>
                <p class="card-text">
                  This section is where you configure rig control method (none
                  (VOX) or hamlib) for both GUI and TNC. For the best experience
                  hamlib control is recommended.
                </p>
              </div>
            </div>

            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">None/Vox</h5>
                <p class="card-text">
                  Select "None/Vox" if you want to use Vox for triggering PTT.
                  No connection to rigctld will be established. No frequency
                  information is availble.
                </p>
              </div>
            </div>

            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">Hamlib</h5>
                <p class="card-text">
                  Select "Hamlib" if you want to have more control over your
                  radio. Define your hamlib settings in settings, and click the
                  start button to start rigctld. You may use the 'PTT test'
                  button to ensure rig control is working.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- HELP MODALS STATION -->
    <div
      class="modal fade"
      data-bs-backdrop="static"
      tabindex="-1"
      id="stationHelpModal"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Help</h5>
            <button
              type="button"
              class="btn btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-info" role="alert">
              These settings will be saved automatically when changing.
            </div>

            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  <div
                    class="input-group input-group-sm mb-0"
                    data-bs-placement="bottom"
                    data-bs-toggle="tooltip"
                    data-bs-trigger="hover"
                    data-bs-html="false"
                    title="Enter your callsign and save it"
                  >
                    <span class="input-group-text">
                      <i
                        class="bi bi-person-bounding-box"
                        style="font-size: 1rem"
                      ></i>
                    </span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="callsign"
                      pattern="[A-Z]*"
                      maxlength="8"
                      style="max-width: 8rem"
                      aria-label="Input group"
                      aria-describedby="btnGroupAddon"
                      disabled
                    />
                    <select
                      class="form-select form-select-sm"
                      aria-label=".form-select-sm"
                      style="max-width: 6rem"
                      disabled
                    >
                      <option selected value="SSID">SSID</option>
                    </select>
                  </div>
                </h5>
                <p class="card-text">
                  Enter your callsign and SSID. Your callsign can have a maximum
                  length of 7 characters
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  <div
                    class="input-group input-group-sm mb-0"
                    data-bs-placement="bottom"
                    data-bs-toggle="tooltip"
                    data-bs-trigger="hover"
                    data-bs-html="false"
                    title="Enter your gridsquare and save it"
                  >
                    <span class="input-group-text">
                      <i class="bi bi-house-fill" style="font-size: 1rem"></i>
                    </span>
                    <input
                      type="text"
                      class="form-control mr-1"
                      style="max-width: 6rem"
                      placeholder="locator"
                      maxlength="6"
                      aria-label="Input group"
                      aria-describedby="btnGroupAddon"
                      disabled
                    />
                  </div>
                </h5>
                <p class="card-text">
                  Enter your position as a 4 or 6 digit grid square, also known
                  as a maidenhead locator. Six digits are recommended.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- HELP MODALS UPDATER -->
    <div
      class="modal fade"
      data-bs-backdrop="static"
      tabindex="-1"
      id="updaterHelpModal"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Help</h5>
            <button
              type="button"
              class="btn btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">Auto-Updater</h5>
                <p class="card-text">
                  The auto updater loads the latest version from Github and
                  installs it automatically. You can select the update channel
                  in settings. Once an update has been downlaoded, you need to
                  confirm the auto-installation and restart.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">Alpha</h5>
                <p class="card-text">
                  Alpha releases are more frequent and contain the latest
                  features, but are likely to be unstable and introduce bugs.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">Beta</h5>
                <p class="card-text">
                  Beta releases are more stable than Alpha releases. They are a
                  good tradeoff between latest features and stability. They will
                  be updated less often. A beta release has not been released
                  yet.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">Stable</h5>
                <p class="card-text">
                  Stable releases are the most stable versions with no known
                  major issues. A stable release has not been released yet.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- HELP MODALS LOCAL REMOTE -->
    <div
      class="modal fade"
      data-bs-backdrop="static"
      tabindex="-1"
      id="localRemoteHelpModal"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Help</h5>
            <button
              type="button"
              class="btn btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  <div
                    class="btn-group btn-group-sm me-2"
                    role="group"
                    aria-label="local-remote-switch toggle button group"
                    data-bs-placement="bottom"
                    data-bs-toggle="tooltip"
                    data-bs-trigger="hover"
                    data-bs-html="true"
                    title="Select a local or a remote location of your TNC daemon. Normally local is the preferred option."
                  >
                    <input
                      type="radio"
                      class="btn-check"
                      name="local-remote-switch"
                      autocomplete="off"
                      checked
                      disabled
                    />
                    <label
                      class="btn btn-sm btn-outline-secondary"
                      for="local-remote-switch1"
                    >
                      <i class="bi bi-pc-display-horizontal"></i>
                      <span class="ms-2 me-2">Local tnc</span>
                    </label>
                    <input
                      type="radio"
                      class="btn-check"
                      name="local-remote-switch"
                      autocomplete="off"
                      disabled
                    />
                    <label
                      class="btn btn-sm btn-outline-secondary"
                      for="local-remote-switch2"
                    >
                      <i class="bi bi-ethernet"></i>
                      <span class="ms-2 me-2">Remote tnc</span>
                    </label>
                  </div>
                </h5>
                <p class="card-text">
                  Local / Remote switch. If the TNC is running on the same
                  computer as the GUI, select local. Otherwise choose remote and
                  enter the IP/Port of where the TNC is running.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  <div class="input-group input-group-sm me-2">
                    <span class="input-group-text">tnc ip</span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="ip address"
                      value="192.168.178.163"
                      maxlength="17"
                      style="width: 8rem"
                      aria-label="Username"
                      aria-describedby="basic-addon1"
                      disabled
                    />
                    <span class="input-group-text">:</span>
                    <input
                      type="text"
                      class="form-control"
                      placeholder="port"
                      value="3000"
                      maxlength="5"
                      max="65534"
                      min="1025"
                      style="width: 4rem"
                      aria-label="Username"
                      aria-describedby="basic-addon1"
                      disabled
                    />
                    <button
                      class="btn btn-sm btn-danger"
                      type="button"
                      disabled
                    >
                      <i class="bi bi-diagram-3" style="font-size: 1rem"></i>
                    </button>
                  </div>
                </h5>
                <p class="card-text">
                  Remote IP of TNC. Port is port of daemon. The tnc port will
                  automatically adjusted. ( daemon port - 1 )
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- HELP MODALS START STOP TNC -->
    <div
      class="modal fade"
      data-bs-backdrop="static"
      tabindex="-1"
      id="startStopTNCHelpModal"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Help</h5>
            <button
              type="button"
              class="btn btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  <div class="btn-group" role="group">
                    <button
                      type="button"
                      class="btn btn-sm btn-outline-success"
                      data-bs-toggle="tooltip"
                      data-bs-trigger="hover"
                      data-bs-html="false"
                      title="Start the TNC. Please set your audio and radio settings first!"
                      disabled
                    >
                      <i class="bi bi-play-fill"></i>
                      <span class="ms-2">Start tnc</span>
                    </button>
                    <button
                      type="button"
                      class="btn btn-sm btn-outline-danger"
                      data-bs-toggle="tooltip"
                      data-bs-trigger="hover"
                      data-bs-html="false"
                      title="Stop the TNC."
                      disabled
                    >
                      <i class="bi bi-stop-fill"></i>
                      <span class="ms-2">Stop tnc</span>
                    </button>
                  </div>
                </h5>
                <p class="card-text">
                  Start or stop the TNC service. The TNC daemon must be running
                  and will work whether the TNC is local or remote.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- HELP MODALS AUDIO LEVEL -->
    <div
      class="modal fade"
      data-bs-backdrop="static"
      tabindex="-1"
      id="audioLevelHelpModal"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Help</h5>
            <button
              type="button"
              class="btn btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  <div class="progress mb-0" style="height: 22px">
                    <div
                      class="progress-bar progress-bar-striped bg-primary force-gpu"
                      role="progressbar"
                      style="width: 5%"
                      aria-valuenow="5"
                      aria-valuemin="0"
                      aria-valuemax="100"
                    ></div>
                    <p
                      class="justify-content-center d-flex position-absolute w-100"
                    >
                      -38 dBFS (Audio Level)
                    </p>
                  </div>
                  <div class="progress mb-0" style="height: 8px">
                    <div
                      class="progress-bar progress-bar-striped bg-warning"
                      role="progressbar"
                      style="width: 1%"
                      aria-valuenow="1"
                      aria-valuemin="0"
                      aria-valuemax="100"
                    ></div>
                    <div
                      class="progress-bar bg-success"
                      role="progressbar"
                      style="width: 89%"
                      aria-valuenow="50"
                      aria-valuemin="0"
                      aria-valuemax="100"
                    ></div>
                    <div
                      class="progress-bar progress-bar-striped bg-warning"
                      role="progressbar"
                      style="width: 20%"
                      aria-valuenow="20"
                      aria-valuemin="0"
                      aria-valuemax="100"
                    ></div>
                    <div
                      class="progress-bar progress-bar-striped bg-danger"
                      role="progressbar"
                      style="width: 29%"
                      aria-valuenow="29"
                      aria-valuemin="0"
                      aria-valuemax="100"
                    ></div>
                  </div>
                </h5>
                <p class="card-text">
                  Represents the level of audio from transceiver. Excessively
                  high levels will affect decoding performance negatively.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  <div class="progress mb-0" style="height: 22px">
                    <div
                      class="progress-bar progress-bar-striped bg-primary force-gpu"
                      role="progressbar"
                      style="width: 30%"
                      aria-valuenow="0"
                      aria-valuemin="0"
                      aria-valuemax="100"
                    ></div>
                    <p
                      class="justify-content-center d-flex position-absolute w-100"
                      id="noise_level_value"
                    >
                      -24 S-Meter (dBm)
                    </p>
                  </div>
                  <div class="progress mb-0" style="height: 8px">
                    <div
                      class="progress-bar progress-bar-striped bg-warning"
                      role="progressbar"
                      style="width: 1%"
                      aria-valuenow="1"
                      aria-valuemin="0"
                      aria-valuemax="100"
                    ></div>
                    <div
                      class="progress-bar bg-success"
                      role="progressbar"
                      style="width: 89%"
                      aria-valuenow="50"
                      aria-valuemin="0"
                      aria-valuemax="100"
                    ></div>
                    <div
                      class="progress-bar progress-bar-striped bg-warning"
                      role="progressbar"
                      style="width: 20%"
                      aria-valuenow="20"
                      aria-valuemin="0"
                      aria-valuemax="100"
                    ></div>
                    <div
                      class="progress-bar progress-bar-striped bg-danger"
                      role="progressbar"
                      style="width: 29%"
                      aria-valuenow="29"
                      aria-valuemin="0"
                      aria-valuemax="100"
                    ></div>
                  </div>
                </h5>
                <p class="card-text">
                  Represents noise level of the channel from the transceiver.
                  Requires hamlib rig control.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-secondary"
                  >
                    Tune
                  </button>
                </h5>
                <p class="card-text">
                  Adjust volume level of outgoing audio to transceiver. For best
                  results lower the level so that a minimum amount of ALC is
                  used. Can be used in combination with rig's mic/input gain for
                  furthrer refinement.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  <button type="button" class="btn btn-sm btn-outline-danger">
                    Record audio
                  </button>
                </h5>
                <p class="card-text">Create a recording of current channel</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- HELP MODALS BROADCASTS -->
    <div
      class="modal fade"
      data-bs-backdrop="static"
      tabindex="-1"
      id="broadcastsHelpModal"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Help</h5>
            <button
              type="button"
              class="btn btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="card mb-3">
              <div class="card-body">
                <button
                  class="btn btn-sm btn-outline-secondary ms-1"
                  type="button"
                  disabled
                >
                  Ping
                </button>
                <p class="card-text">
                  Send a ping to a remote station by entering a callsign and
                  optional SSID (-0 will be used if not specified.)
                  Alternatively click on a station in the heard station list to
                  populate the call sign field. If the remote station decodes
                  the ping it will transmit a reply. If able to decode the
                  reply, a signal report will be listed in the heard station
                  list.
                </p>
              </div>
            </div>

            <div class="card mb-3">
              <div class="card-body">
                <button
                  class="btn btn-sm btn-outline-secondary"
                  type="button"
                  disabled
                >
                  Call CQ
                </button>
                <p class="card-text">Sending out a CQ CQ CQ to the world.</p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-secondary"
                  disabled
                >
                  <i class="bi bi-soundwave"></i>Toggle beacon
                </button>
                <p class="card-text">
                  Sends a periodic broadcast (duration is definable in settings)
                  that announces you are available. Check explorer to see other
                  active stations that may have decoded your beacon.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- HELP MODALS WATERFALL -->
    <div
      class="modal fade"
      data-bs-backdrop="static"
      tabindex="-1"
      id="waterfallHelpModal"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Help</h5>
            <button
              type="button"
              class="btn btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  Waterfall
                  <input
                    type="radio"
                    class="btn-check"
                    name="waterfall-scatter-switch"
                    autocomplete="off"
                    checked
                  />
                  <label
                    class="btn btn-sm btn-outline-secondary"
                    for="waterfall-scatter-switch1"
                    ><strong><i class="bi bi-water"></i></strong>
                  </label>
                </h5>
                <p class="card-text">
                  Displays a waterfall for activity of current channel.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  Busy Indicator

                  <button class="btn btn-sm btn-success" type="button">
                    busy
                  </button>
                </h5>
                <p class="card-text">
                  Green when channel is open and changes to red to indicate
                  there is activity on the channel.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  Signal Indicator
                  <button class="btn btn-sm btn-success" type="button">
                    signal
                  </button>
                </h5>
                <p class="card-text">
                  Changes to green when Codec2 data is detected on channel.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  Constellation Plot
                  <input type="radio" class="btn-check" autocomplete="off" />
                  <label class="btn btn-sm btn-outline-secondary"
                    ><strong><i class="bi bi-border-outer"></i></strong>
                  </label>
                </h5>
                <p class="card-text">
                  Displays a plot of last decoded message. A constellation plot
                  is a simple way to represent signal quality.
                </p>
              </div>
            </div>
            <div class="card mb-3">
              <div class="card-body">
                <h5 class="card-title">
                  Speed Chart

                  <input type="radio" class="btn-check" autocomplete="off" />
                  <label class="btn btn-sm btn-outline-secondary"
                    ><strong><i class="bi bi-graph-up-arrow"></i></strong>
                  </label>
                </h5>
                <p class="card-text">
                  Shows history of SNR and bit rate of messages.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- HELP MODALS HEARD STATIONS -->
    <div
      class="modal fade"
      data-bs-backdrop="static"
      tabindex="-1"
      id="heardStationsHelpModal"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Station List Help</h5>
            <button
              type="button"
              class="btn btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="card mb-3">
              <div class="card-body">
                <p class="card-text">
                  Stations that you've been able to decode will be listed here.
                  Details such as time, frequency, message type, call sign,
                  location and SNR will be listed. Existing entries are updated
                  if they already exist and more detailed history can be viewed
                  in chat window for each station.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AUDIO MODAL -->
    <div
      class="modal fade"
      data-bs-backdrop="static"
      tabindex="-1"
      id="audioModal"
    >
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Audio tuning</h5>
            <button
              type="button"
              class="btn btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="input-group input-group-sm mb-1">
              <span class="input-group-text">Test-Frame</span>
              <button type="button" id="sendTestFrame" class="btn btn-danger">
                Transmit
              </button>
            </div>
            <div class="input-group input-group-sm mb-1">
              <span class="input-group-text">TX Level</span>
              <span class="input-group-text" id="audioLevelTXvalue">---</span>
              <span class="input-group-text w-75">
                <input
                  type="range"
                  class="form-range"
                  min="0"
                  max="250"
                  step="1"
                  id="audioLevelTX"
              /></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
 </html>
</template>


