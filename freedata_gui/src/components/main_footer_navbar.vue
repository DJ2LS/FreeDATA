<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);
</script>

<template>
        <nav
          class="navbar navbar-expand-xl bg-body-tertiary border-top p-2"
        >
          <div class="col">
            <div class="btn-toolbar" role="toolbar">
              <div class="btn-group btn-group-sm me-1" role="group">
                <button
                  class="btn btn-sm btn-secondary me-1"
                  v-bind:class="{
                    'btn-danger': state.ptt_state == true,
                    'btn-secondary': state.ptt_state == false,
                  }"
                  id="ptt_state"
                  type="button"
                  style="pointer-events: auto"
                  disabled
                  data-bs-toggle="tooltip"
                  data-bs-placement="top"
                  data-bs-title="PTT trigger state"
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
                  v-bind:class="{
                    'btn-danger': state.busy_state === true,
                    'btn-secondary': state.busy_state === false,
                  }"
                  data-bs-title="Modem state"
                  disabled
                  style="pointer-events: auto"
                >
                  <i class="bi bi-cpu" style="font-size: 0.8rem"></i>
                </button>
                <!--
          <button
            class="btn btn-sm btn-secondary me-1"
            id="arq_session"
            type="button"
            data-bs-placement="top"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            data-bs-html="true"
            v-bind:class="{
              'btn-secondary': state.arq_session_state === 'disconnected',
              'btn-warning': state.arq_session_state === 'connected',
            }"
            disabled
            style="pointer-events: auto"
            data-bs-title="Session state"
          >
            <i class="bi bi-arrow-left-right" style="font-size: 0.8rem"></i>
          </button>
          -->
                <!--
          <button
            class="btn btn-sm btn-secondary me-1"
            id="arq_state"
            type="button"
            data-bs-placement="top"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            data-bs-title="Data channel state"
            v-bind:class="{
              'btn-secondary': state.arq_state === 'False',
              'btn-warning': state.arq_state === 'True',
            }"
            disabled
            style="pointer-events: auto"
          >
            <i class="bi bi-file-earmark-binary" style="font-size: 0.8rem"></i>
          </button>
          -->
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
                <!--
          <button
            class="btn btn-sm btn-secondary disabled me-3"
            type="button"
            data-bs-placement="top"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            data-bs-html="true"
            v-bind:class="{
              'btn-warning': state.channel_busy === true,
              'btn-secondary': state.channel_busy === false,
            }"
            style="pointer-events: auto"
            data-bs-title="Channel busy"
          >
            <i class="bi bi-hourglass"></i>
          </button>
            -->
              </div>

              <div class="btn-group btn-group-sm me-1" role="group">
                <button
                  class="btn btn-sm btn-secondary me-4 disabled"
                  type="button"
                  data-bs-placement="top"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-title="What's the frequency, Kenneth?"
                  style="pointer-events: auto"
                >
                  {{ state.frequency / 1000 }} kHz
                </button>
              </div>

              <div class="btn-group btn-group-sm me-1" role="group">
                <button
                  class="btn btn-sm btn-secondary me-0"
                  type="button"
                  title="Speed level"
                >
                  <i class="bi bi-speedometer2" style="font-size: 1rem"></i>
                </button>

                <button
                  class="btn btn-sm btn-secondary me-4 disabled"
                  type="button"
                  data-bs-placement="top"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="true"
                  data-bs-titel="speed level"
                >
                  <i
                    class="bi"
                    style="font-size: 1rem"
                    v-bind:class="{
                      'bi-reception-0': state.speed_level == 0,
                      'bi-reception-1': state.speed_level == 1,
                      'bi-reception-2': state.speed_level == 2,
                      'bi-reception-3': state.speed_level == 3,
                      'bi-reception-4': state.speed_level == 4,
                    }"
                  ></i>
                </button>
              </div>
              <div class="btn-group btn-group-sm me-1" role="group">
                <button
                  class="btn btn-sm btn-secondary me-0"
                  type="button"
                  title="Bytes transfered"
                >
                  <i
                    class="bi bi-file-earmark-binary"
                    style="font-size: 1rem"
                  ></i>
                </button>

                <button
                  class="btn btn-sm btn-secondary me-4 disabled"
                  type="button"
                  data-bs-placement="top"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="true"
                  data-bs-title="total bytes of transmission"
                >
                  {{ state.arq_total_bytes }}
                </button>
              </div>
              <div class="btn-group btn-group-sm me-1" role="group">
                <button
                  class="btn btn-sm btn-secondary me-0"
                  type="button"
                  data-bs-placement="top"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="true"
                  data-bs-title="Current or last connected with station"
                >
                  <i
                    class="bi bi-file-earmark-binary"
                    style="font-size: 1rem"
                  ></i>
                </button>

                <button
                  class="btn btn-sm btn-secondary disabled me-1"
                  type="button"
                  data-bs-placement="top"
                  data-bs-toggle="tooltip"
                  data-bs-trigger="hover"
                  data-bs-html="true"
                  data-bs-title="the dxcallsign of the connected station"
                >
                  {{ state.dxcallsign }}
                </button>
              </div>
            </div>
          </div>
          <div class="col-lg-4">
            <div style="margin-right: 2px">
              <div
                class="progress w-100"
                style="height: 20px; min-width: 200px"
              >
                <div
                  class="progress-bar progress-bar-striped bg-primary force-gpu"
                  id="transmission_progress"
                  role="progressbar"
                  :style="{ width: state.arq_transmission_percent + '%' }"
                  aria-valuenow="0"
                  aria-valuemin="0"
                  aria-valuemax="100"
                ></div>
                <p
                  class="justify-content-center m-0 d-flex position-absolute w-100 text-dark"
                >
                  Message Progress
                </p>
              </div>

              <div
                hidden
                class="progress mb-0 rounded-0 rounded-bottom"
                style="height: 10px"
              >
                <div
                  class="progress-bar progress-bar-striped bg-warning"
                  id="transmission_timeleft"
                  role="progressbar"
                  :style="{
                    width: state.arq_seconds_until_timeout_percent + '%',
                  }"
                  aria-valuenow="0"
                  aria-valuemin="0"
                  aria-valuemax="100"
                >
                  <p
                    class="justify-content-center m-0 d-flex position-absolute w-100 text-dark"
                  >
                    timeout in {{ state.arq_seconds_until_timeout }}s
                  </p>
                </div>
              </div>
            </div>
          </div>
        </nav>

</template>
