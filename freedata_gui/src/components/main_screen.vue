<template>
  <main_modals />

  <div aria-live="polite" aria-atomic="true" class="position-relative z-3">
    <div
      class="toast-container position-absolute top-0 end-0 p-3"
      id="mainToastContainer"
    ></div>
  </div>

  <div class="container-fluid d-flex flex-column min-vh-100">
    <div class="row flex-nowrap flex-grow-1">
      <!-- Collapsible Left Navbar -->
      <div class="col-auto p-0 bg-body-secondary border-end d-flex flex-column">
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
      <div class="col m-0 p-0 d-flex flex-column">
        <div class="flex-grow-1 d-flex flex-column overflow-auto">
          <div class="tab-content flex-grow-1">
            <!-- Tab Panes -->
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
              id="list-settings"
              role="tabpanel"
              aria-labelledby="list-settings-list"
            >
              <settings_view />
            </div>
          </div>
        </div>
        <!-- Footer Area -->
        <main_footer_navbar />
      </div>
    </div>
  </div>
</template>

<script>
import { setActivePinia } from 'pinia';
import pinia from '../store/index';

import main_modals from './main_modals.vue';
import settings_view from './settings_screen.vue';
import main_footer_navbar from './main_footer_navbar.vue';
import main_left_navbar from './main_left_navbar.vue';
import chat from './chat_screen.vue';
import Dynamic_components from './dynamic_components.vue';

// Set the active Pinia store
setActivePinia(pinia);

export default {
  components: {
    main_modals,
    settings_view,
    main_footer_navbar,
    main_left_navbar,
    chat,
    Dynamic_components,
  },
};
</script>
