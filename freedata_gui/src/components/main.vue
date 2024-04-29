<script setup lang="ts">
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import main_modals from "./main_modals.vue";
import main_top_navbar from "./main_top_navbar.vue";
import settings_view from "./settings.vue";
import main_footer_navbar from "./main_footer_navbar.vue";
import main_left_navbar from "./main_left_navbar.vue";
import mesh from "./mesh.vue";
import chat from "./chat.vue";
import Dynamic_components from "./dynamic_components.vue";

import { getFreedataMessages } from "../js/api";
import { getRemote } from "../store/settingsStore.js";
import { loadAllData } from "../js/eventHandler";
</script>

<template>
  <div aria-live="polite" aria-atomic="true" class="position-relative z-3">
    <div
      class="toast-container position-absolute top-0 end-0 p-3"
      id="mainToastContainer"
    ></div>
  </div>

  <div class="container-fluid">
    <div class="row">
      <!-- Collapsible Left Navbar -->
      <div class="col-auto p-0 bg-body-secondary border-end">
        <div class="flex-shrink-0 p-3">
          <div
            class="collapse collapse-horizontal show"
            id="collapseLeftNavbar"
          >
            <main_left_navbar />
          </div>
        </div>
      </div>

      <!-- Main Content -->
      <div class="col min-vh-100 m-0 p-0">
        <div class="tab-content" id="nav-tabContent-settings">
          <!-- Tab Panes -->
          <div
            class="tab-pane fade"
            id="list-home"
            role="tabpanel"
            aria-labelledby="list-home-list"
          ></div>
          <div
            class="tab-pane fade d-none"
            id="list-mesh"
            role="tabpanel"
            aria-labelledby="list-mesh-list"
          >
            <mesh />
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
          <settings_view />
          <main_footer_navbar />
        </div>

        <!-- Footer Area -->
        <div class="container">
          <!--<main_footer_navbar />-->
        </div>
      </div>
    </div>
  </div>

  <main_modals />
</template>
