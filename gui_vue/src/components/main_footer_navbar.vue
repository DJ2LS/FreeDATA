<script setup lang="ts">

import {saveSettingsToFile} from '../js/settingsHandler'

import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useSettingsStore } from '../store/settingsStore.js';
const settings = useSettingsStore(pinia);


</script>

<template>
 <nav
        class="navbar fixed-bottom navbar-expand-xl bg-body-tertiary border-top p-2"
        style="margin-left: 87px"
      >

        <div class="col-sm-2">
          <div class="btn-toolbar" role="toolbar" style="margin-left: 2px">
            <div class="btn-group btn-group-sm me-1" role="group">
              <button
                class="btn btn-sm btn-secondary me-1"
                id="ptt_state"
                type="button"
                data-bs-placement="top"
                data-bs-toggle="tooltip"
                data-bs-trigger="hover"
                data-bs-html="true"
                title="PTT state:<strong class='text-success'>RECEIVING</strong> / <strong class='text-danger'>TRANSMITTING</strong>"
              >
                <i class="bi bi-broadcast-pin" style="font-size: 0.8rem"></i>
              </button>

              <button
                class="btn btn-sm btn-secondary me-1"
                id="busy_state"
                type="button"
                data-bs-placement="top"
                data-bs-toggle="tooltip"
                data-bs-trigger="hover"
                data-bs-html="true"
                title="TNC busy state: <strong class='text-success'>IDLE</strong> / <strong class='text-danger'>BUSY</strong>"
              >
                <i class="bi bi-cpu" style="font-size: 0.8rem"></i>
              </button>

              <button
                class="btn btn-sm btn-secondary me-1"
                id="arq_session"
                type="button"
                data-bs-placement="top"
                data-bs-toggle="tooltip"
                data-bs-trigger="hover"
                data-bs-html="true"
                title="ARQ SESSION state: <strong class='text-warning'>OPEN</strong>"
              >
                <i class="bi bi-arrow-left-right" style="font-size: 0.8rem"></i>
              </button>

              <button
                class="btn btn-sm btn-secondary me-1"
                id="arq_state"
                type="button"
                data-bs-placement="top"
                data-bs-toggle="tooltip"
                data-bs-trigger="hover"
                data-bs-html="true"
                title="DATA-CHANNEL state: <strong class='text-warning'>OPEN</strong>"
              >
                <i
                  class="bi bi-file-earmark-binary"
                  style="font-size: 0.8rem"
                ></i>
              </button>
<!--
              <button
                class="btn btn-sm btn-secondary me-1"
                id="rigctld_state"
                type="button"
                data-bs-placement="top"
                data-bs-toggle="tooltip"
                data-bs-trigger="hover"
                data-bs-html="true"
                title="rigctld state: <strong class='text-success'>CONNECTED</strong> / <strong class='text-secondary'>UNKNOWN</strong>"
              >
                <i class="bi bi-usb-symbol" style="font-size: 0.8rem"></i>
              </button>
-->
            </div>
          </div>
        </div>
        <div class="col-sm-3">
          <div class="input-group input-group-sm">
            <div class="btn-group dropup me-1">
              <button
                type="button"
                class="btn btn-sm btn-secondary dropdown-toggle"
                data-bs-toggle="dropdown"
                aria-expanded="false"
                id="frequency"
              >
                ---
              </button>
              <form class="dropdown-menu p-2">
                <div class="input-group input-group-sm">
                  <input
                    type="text"
                    class="form-control"
                    style="max-width: 6rem"
                    placeholder="7053000"
                    pattern="[0-9]*"
                    id="newFrequency"
                    maxlength="11"
                    aria-label="Input group"
                    aria-describedby="btnGroupAddon"
                  />
                  <span class="input-group-text">Hz</span>
                  <button
                    class="btn btn-sm btn-success"
                    id="saveFrequency"
                    type="button"
                    data-bs-placement="bottom"
                    data-bs-toggle="tooltip"
                    data-bs-trigger="hover"
                    data-bs-html="false"
                    title="save frequency"
                  >
                    <i class="bi bi-check-lg" style="font-size: 0.8rem"></i>
                  </button>
                </div>
              </form>
            </div>
<!--
            <div class="btn-group dropup me-1">
              <button
                type="button"
                class="btn btn-sm btn-secondary dropdown-toggle"
                data-bs-toggle="dropdown"
                aria-expanded="false"
                id="mode"
              >
                ---
              </button>


              <form class="dropdown-menu p-2">
                <button
                  type="button"
                  class="btn btn-sm btn-secondary"
                  data-bs-placement="bottom"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="false"
                  title="set FM"
                  id="saveModeFM"
                >
                  FM
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-secondary"
                  data-bs-placement="bottom"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="false"
                  title="set AM"
                  id="saveModeAM"
                >
                  AM
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-secondary"
                  data-bs-placement="bottom"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="false"
                  title="set LSB"
                  id="saveModeLSB"
                >
                  LSB
                </button>
                <hr />
                <button
                  type="button"
                  class="btn btn-sm btn-secondary"
                  data-bs-placement="bottom"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="false"
                  title="set USB"
                  id="saveModeUSB"
                >
                  USB
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-secondary"
                  data-bs-placement="bottom"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="false"
                  title="set PKTUSB"
                  id="saveModePKTUSB"
                >
                  PKTUSB
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-secondary"
                  data-bs-placement="bottom"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="false"
                  title="set DIGU"
                  id="saveModeDIGU"
                >
                  DIGU
                </button>

                <button
                  type="button"
                  class="btn btn-sm btn-secondary"
                  data-bs-placement="bottom"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="false"
                  title="set DIGL"
                  id="saveModeDIGL"
                >
                  DIGL
                </button>
              </form>
            </div>
-->

<!--
            <div class="btn-group dropup">
              <button
                type="button"
                class="btn btn-sm btn-secondary dropdown-toggle"
                data-bs-toggle="dropdown"
                aria-expanded="false"
                id="bandwidth"
              >
                ---
              </button>
              <form class="dropdown-menu p-2">
                <div class="input-group input-group-sm">...soon...</div>
              </form>
            </div>
            -->
          </div>
        </div>
        <div class="col-sm-3">
          <div class="input-group input-group-sm">
            <span class="input-group-text">
              <i class="bi bi-speedometer2" style="font-size: 1rem"></i>
            </span>
            <span
              class="input-group-text"
              data-bs-placement="bottom"
              data-bs-toggle="tooltip"
              data-bs-trigger="hover"
              data-bs-html="false"
              title="actual speed level"
            >
              <i
                id="speed_level"
                class="bi bi-reception-0"
                style="font-size: 1rem"
              ></i>
            </span>
            <span class="input-group-text">
              <i class="bi bi-file-earmark-binary" style="font-size: 1rem"></i>
            </span>
            <span
              class="input-group-text"
              id="total_bytes"
              data-bs-placement="bottom"
              data-bs-toggle="tooltip"
              data-bs-trigger="hover"
              data-bs-html="false"
              title="total bytes processed"
              >---</span
            >
            <span
              class="input-group-text"
              data-bs-toggle="tooltip"
              data-bs-trigger="hover"
              title="Indicates if a session is active"
              ><span class="bi bi-chat-fill" id="spnConnectedWith"></span
            ></span>
            <span
              class="input-group-text"
              id="txtConnectedWith"
              data-bs-toggle="tooltip"
              data-bs-trigger="hover"
              title="Connected with"
              >------</span
            >
          </div>
        </div>
        <div class="col-lg-4">
          <div style="margin-right: 2px">
            <div class="progress w-100" style="height: 30px; min-width: 200px">
              <div
                class="progress-bar progress-bar-striped bg-primary force-gpu"
                id="transmission_progress"
                role="progressbar"
                style="width: 0%"
                aria-valuenow="0"
                aria-valuemin="0"
                aria-valuemax="100"
              ></div>
              <!--<p class="justify-content-center d-flex position-absolute w-100">PROGRESS</p>-->
              <p
                class="justify-content-center mt-2 d-flex position-absolute w-100"
                id="transmission_timeleft"
              >
                ---
              </p>
            </div>
          </div>
        </div>
      </nav>


</template>