<script setup>
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
import { useStateStore } from '../store/stateStore.js';

import { useIsMobile } from '../js/mobile_devices.js';
const { isMobile } = useIsMobile(992);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);

// Set the active Pinia store
setActivePinia(pinia);

// Create an instance of the store
const state = useStateStore(pinia);
</script>

<template>
  <nav
    :class="[
      'navbar bg-body-secondary border-top sticky-bottom border-1 p-2',
      (isMobile && chat.selectedCallsign) ? 'col-12' : 'col-12',
      'col-lg-auto'
    ]"
  >
    <div class="col-lg-8 col-md-9 col-sm-10 col-xs-11 col-8">
      <div
        class="btn-toolbar"
        role="toolbar"
      >
        <div
          class="btn-group btn-group-sm me-1"
          role="group"
        >
          <button
            id="ptt_state"
            class="btn btn-sm btn-secondary me-1"
            :class="{
              'btn-danger': state.ptt_state,
              'btn-secondary': !state.ptt_state,
            }"
            type="button"
            style="pointer-events: auto"
            disabled
            data-bs-toggle="tooltip"
            data-bs-placement="top"
            :data-bs-title="$t('navbar.pttstate_help')"
          >
            <i
              class="bi bi-broadcast-pin"
              style="font-size: 0.8rem"
            />
          </button>
          <button
            id="busy_state"
            class="btn btn-sm btn-secondary me-1"
            type="button"
            data-bs-placement="top"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            data-bs-html="true"
            :class="{
              'btn-danger': state.busy_state,
              'btn-secondary': !state.busy_state,
            }"
            :data-bs-title="$t('navbar.modemstate_help')"
            disabled
            style="pointer-events: auto"
          >
            <i
              class="bi bi-cpu"
              style="font-size: 0.8rem"
            />
          </button>
        </div>

        <div
          class="btn-group btn-group-sm me-1 d-none d-lg-inline-block"
          role="group"
        >
          <button
            class="btn btn-sm btn-secondary me-4 disabled"
            type="button"
            data-bs-placement="top"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            :data-bs-title="$t('navbar.frequency_help')"
            style="pointer-events: auto"
          >
            {{ state.frequency / 1000 }} kHz
          </button>
        </div>

        <div
          class="btn-group btn-group-sm me-1 d-none d-lg-inline-block"
          role="group"
        >
          <button
            class="btn btn-sm btn-secondary me-0"
            type="button"
            :title="$t('navbar.speedlevel_help')"
          >
            <i class="bi bi-speedometer2" />
          </button>

          <button
            class="btn btn-sm btn-secondary me-4 disabled"
            type="button"
            data-bs-placement="top"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            data-bs-html="true"
            :data-bs-title="$t('navbar.speedlevel_help')"
          >
            <i
              class="bi"
              :class="{
                'bi-reception-0': state.speed_level === 0,
                'bi-reception-1': state.speed_level === 1,
                'bi-reception-2': state.speed_level === 2,
                'bi-reception-3': state.speed_level === 3,
                'bi-reception-4': state.speed_level === 4,
              }"
            />
          </button>
        </div>

        <div
          class="btn-group btn-group-sm me-1 d-none d-lg-inline-block"
          role="group"
        >
          <button
            class="btn btn-sm btn-secondary me-0"
            type="button"
            :title="$t('navbar.bytestransferred')"
          >
            <i class="bi bi-file-earmark-binary" />
          </button>

          <button
            class="btn btn-sm btn-secondary me-4 disabled"
            type="button"
            data-bs-placement="top"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            data-bs-html="true"
            :data-bs-title="$t('navbar.totalbytes_help')"
          >
            {{ state.arq_total_bytes }}
          </button>
        </div>

        <div
          class="btn-group btn-group-sm me-1"
          role="group"
        >
          <button
            class="btn btn-sm btn-secondary me-0"
            type="button"
            data-bs-placement="top"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            data-bs-html="true"
            :data-bs-title="$t('navbar.connectedstation_help')"
          >
            <i class="bi bi-file-earmark-binary" />
          </button>

          <button
            class="btn btn-sm btn-secondary disabled"
            type="button"
            data-bs-placement="top"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            data-bs-html="true"
            data-bs-title="the dxcallsign of the connected station"
          >
            <span v-if="state.arq_is_receiving">{{ $t('navbar.from') }}</span>
            <span v-else>{{ $t('navbar.to') }}</span>
          </button>

          <button
            class="btn btn-sm btn-secondary disabled me-1"
            type="button"
            data-bs-placement="top"
            data-bs-toggle="tooltip"
            data-bs-trigger="hover"
            data-bs-html="true"
            :data-bs-title="state.dxcallsign || '-----'"
          >
            {{ state.dxcallsign || '-----' }}
          </button>
        </div>
      </div>
    </div>

    <div class="col-lg-4 col-md-3 col-sm-2 col-xs-1 col-1">
      <div
        class="progress w-100 bg-secondary me-2"
        style="height: 30px;"
      >
        <div
          id="transmission_progress"
          class="progress-bar progress-bar-striped bg-primary force-gpu"
          role="progressbar"
          :style="{ width: state.arq_transmission_percent + '%' }"
          aria-valuenow="0"
          aria-valuemin="0"
          aria-valuemax="100"
        />
        <p
          v-if="!isMobile"
          class="justify-content-center m-0 d-flex position-absolute w-100 mt-1 text-light"
        >
          {{ state.arq_transmission_percent }}% [ {{ state.arq_bytes_per_minute || '---' }}
          bpm / {{ state.arq_bits_per_second || '--' }}
          bps ]
        </p>

        <p
          v-if="isMobile"
          class="justify-content-center m-0 d-flex position-absolute w-100 mt-1 text-light"
        >
          {{ state.arq_transmission_percent }}%
        </p>
      </div>

      <!-- TODO: This code block can be removed I think, DJ2LS -->
      <div
        hidden
        class="progress mb-0 rounded-0 rounded-bottom"
        style="height: 10px;"
      >
        <div
          id="transmission_timeleft"
          class="progress-bar progress-bar-striped bg-warning"
          role="progressbar"
          :style="{ width: state.arq_seconds_until_timeout_percent + '%' }"
          aria-valuenow="0"
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <p class="justify-content-center m-0 d-flex position-absolute w-100 text-dark">
            timeout in {{ state.arq_seconds_until_timeout }}s
          </p>
        </div>
      </div>
    </div>
  </nav>
</template>
