<script setup lang="ts">
import settings_station from "./settings_station.vue";
import settings_gui from "./settings_gui.vue";
import settings_chat from "./settings_chat.vue";
import settings_rigcontrol from "./settings_rigcontrol.vue";
import settings_modem from "./settings_modem.vue";
import settings_web from "./settings_web.vue";
import settings_exp from "./settings_exp.vue";
import settings_earl from "./settings_url.vue";

</script>
<template>
  <div
    class="tab-pane fade"
    id="list-settings"
    role="tabpanel"
    aria-labelledby="list-settings-list"
  >
    <div class="container">
      <div class="card text-center">
        <div class="card-header">
          <!-- SETTINGS Nav tabs -->
          <ul class="nav nav-tabs card-header-tabs" id="myTab" role="tablist">
            <li class="nav-item" role="presentation">
              <button
                class="nav-link active"
                id="station-tab"
                data-bs-toggle="tab"
                data-bs-target="#station"
                type="button"
                role="tab"
                aria-controls="home"
                aria-selected="true"
              >
                Station
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button
                class="nav-link"
                id="gui-tab"
                data-bs-toggle="tab"
                data-bs-target="#gui"
                type="button"
                role="tab"
                aria-controls="home"
                aria-selected="true"
              >
                GUI
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button
                class="nav-link"
                id="chat-tab"
                data-bs-toggle="tab"
                data-bs-target="#chat"
                type="button"
                role="tab"
                aria-controls="home"
                aria-selected="true"
              >
                Chat
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button
                class="nav-link"
                id="rigcontrol-tab"
                data-bs-toggle="tab"
                data-bs-target="#rigcontrol"
                type="button"
                role="tab"
                aria-controls="profile"
                aria-selected="false"
              >
                Rig Control
              </button>
            </li>

            <li class="nav-item" role="presentation">
              <button
                class="nav-link"
                id="modem-tab"
                data-bs-toggle="tab"
                data-bs-target="#modem"
                type="button"
                role="tab"
                aria-controls="profile"
                aria-selected="false"
              >
                Modem
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button
                class="nav-link"
                id="web-tab"
                data-bs-toggle="tab"
                data-bs-target="#web"
                type="button"
                role="tab"
                aria-controls="messages"
                aria-selected="false"
              >
                Web
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button
                class="nav-link"
                id="experiments-tab"
                data-bs-toggle="tab"
                data-bs-target="#experiments"
                type="button"
                role="tab"
                aria-controls="settings"
                aria-selected="false"
              >
                Exp
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button
                class="nav-link"
                id="experiments-tab"
                data-bs-toggle="tab"
                data-bs-target="#url"
                type="button"
                role="tab"
                aria-controls="settings"
                aria-selected="false"
              >
                Links
              </button>
            </li>
          </ul>
        </div>
        <div
          class="card-body overflow-auto"
          style="height: calc(100vh - 105px)"
        >
          <!-- SETTINGS Nav Tab panes -->

          <!-- Station tab contents-->
          <div class="tab-content">
            <div
              class="tab-pane active"
              id="station"
              role="tabpanel"
              aria-labelledby="station-tab"
              tabindex="0"
            >
              <settings_station />
            </div>

            <!-- GUI tab contents-->
            <div
              class="tab-pane"
              id="gui"
              role="tabpanel"
              aria-labelledby="gui-tab"
              tabindex="0"
            >
              <settings_gui />
            </div>

            <div
              class="tab-pane"
              id="chat"
              role="tabpanel"
              aria-labelledby="chat-tab"
              tabindex="0"
            >
              <settings_chat />
            </div>

            <div
              class="tab-pane"
              id="rigcontrol"
              role="tabpanel"
              aria-labelledby="rigcontrol-tab"
              tabindex="0"
            >
              <settings_rigcontrol />
            </div>

            <div
              class="tab-pane"
              id="modem"
              role="tabpanel"
              aria-labelledby="modem-tab"
              tabindex="0"
            >
              <settings_modem />
            </div>
            <div
              class="tab-pane"
              id="web"
              role="tabpanel"
              aria-labelledby="web-tab"
              tabindex="0"
            >
              <settings_web />
            </div>
            <div
              class="tab-pane"
              id="experiments"
              role="tabpanel"
              aria-labelledby="experiments-tab"
              tabindex="0"
            >
              <settings_exp />
            </div>
            <div
              class="tab-pane"
              id="url"
              role="tabpanel"
              aria-labelledby="url-tab"
              tabindex="0"
            >
              <settings_earl />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
