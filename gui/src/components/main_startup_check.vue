<script setup lang="ts">

import { Modal } from 'bootstrap'
import { onMounted } from 'vue'

import main_rig_control from "./main_rig_control.vue";
import main_audio from "./main_audio.vue";
import infoScreen_updater from "./infoScreen_updater.vue";

// start modemCheck modal once on startup
onMounted(() => {
    new Modal('#modemCheck', {}).show()
})





</script>

<template>
  <div
    class="modal fade"
    id="modemCheck"
    data-bs-backdrop="static"
    data-bs-keyboard="false"
    tabindex="-1"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Modem check</h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">





          <div class="accordion" id="startupCheckAccordion">
            <!-- Version Section -->
            <div class="accordion-item">
              <h2 class="accordion-header">
                <button
                  class="accordion-button collapsed"
                  type="button"
                  data-bs-target="#versionCheckCollapse"
                  data-bs-toggle="collapse"
                >
                  Version <span class="badge ms-2 bg-warning">Update needed</span>
                </button>
              </h2>
              <div id="versionCheckCollapse" class="accordion-collapse collapse">
                <div class="accordion-body">
                  <infoScreen_updater />
                </div>
              </div>
            </div>
            <!-- Network Section -->
            <div class="accordion-item">
              <h2 class="accordion-header">
                <button
                  class="accordion-button collapsed"
                  type="button"
                  data-bs-target="#networkStatusCollapse"
                  data-bs-toggle="collapse"
                >
                  Network <span class="badge ms-2 bg-success">Connected</span>
                </button>
              </h2>
              <div id="networkStatusCollapse" class="accordion-collapse collapse">
                <div class="accordion-body">
                  Placeholder content for this accordion, which is intended to
                  demonstrate the <code>.accordion-flush</code> class. This is
                  the first item's accordion body.
                </div>
              </div>
            </div>
            <!-- Modem Section -->
            <div class="accordion-item">
              <h2 class="accordion-header">
                <button
                  class="accordion-button collapsed"
                  type="button"
                  data-bs-target="#modemStatusCollapse"
                  data-bs-toggle="collapse"
                >
                  Modem <span class="badge ms-2 bg-success">Running</span>
                </button>
              </h2>
              <div id="modemStatusCollapse" class="accordion-collapse collapse">
                <div class="accordion-body">
                  <main_audio />
                </div>
              </div>
            </div>
            <!-- Radio Control Section -->
            <div class="accordion-item">
              <h2 class="accordion-header">
                <button
                  class="accordion-button collapsed"
                  type="button"
                  data-bs-target="#radioControlCollapse"
                  data-bs-toggle="collapse"
                >
                  Radio control
                  <span class="badge ms-2 bg-danger">Disconnected</span>
                </button>
              </h2>
              <div id="radioControlCollapse" class="accordion-collapse collapse">
                <div class="accordion-body">
                  <main_rig_control />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
            Continue
          </button>
        </div>
      </div>
    </div>
  </div>
</template>