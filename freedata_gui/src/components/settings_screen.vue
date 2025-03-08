
<template>

    <div class="container-fluid p-2" style="height: calc(-48px + 100vh);">
      <div class="card text-center h-100">
        <div class="card-header">
          <!-- SETTINGS Nav tabs -->
          <ul class="nav nav-tabs card-header-tabs" role="tablist">
            <li class="nav-item" role="presentation">
              <button
                class="nav-link active show"
                id="station-tab"
                data-bs-toggle="tab"
                data-bs-target="#station"
                type="button"
                role="tab"
                aria-controls="station"
                aria-selected="true"
              >
                {{ $t('settings.tabstation') }}
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
                aria-controls="gui"
                aria-selected="false"
              >
                {{ $t('settings.tabgui') }}
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
                aria-controls="chat"
                aria-selected="false"
              >
                {{ $t('settings.tabchat') }}
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
                aria-controls="rigcontrol"
                aria-selected="false"
              >
                {{ $t('settings.tabradiocontrol') }}
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
                aria-controls="modem"
                aria-selected="false"
              >
                {{ $t('settings.tabmodem') }}
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
                aria-controls="web"
                aria-selected="false"
              >
                {{ $t('settings.tabweb') }}
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
                aria-controls="experiments"
                aria-selected="false"
              >
                {{ $t('settings.tabexperimental') }}
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button
                class="nav-link"
                id="links-tab"
                data-bs-toggle="tab"
                data-bs-target="#url"
                type="button"
                role="tab"
                aria-controls="url"
                aria-selected="false"
              >
                 {{ $t('settings.tablinks') }}
              </button>
            </li>
          </ul>
        </div>
        <div class="card-body p-2 overflow-auto" style="flex: 1 1 auto;">
          <!-- SETTINGS Nav Tab panes -->
          <div class="tab-content">
            <!-- Station tab contents-->
            <div
              class="tab-pane fade show active"
              id="station"
              role="tabpanel"
              aria-labelledby="station-tab"
              tabindex="0"
            >
              <settings_station />
            </div>

            <!-- GUI tab contents-->
            <div
              class="tab-pane fade"
              id="gui"
              role="tabpanel"
              aria-labelledby="gui-tab"
              tabindex="0"
            >
              <settings_gui />
            </div>

            <div
              class="tab-pane fade"
              id="chat"
              role="tabpanel"
              aria-labelledby="chat-tab"
              tabindex="0"
            >
              <settings_chat />
            </div>

            <div
              class="tab-pane fade"
              id="rigcontrol"
              role="tabpanel"
              aria-labelledby="rigcontrol-tab"
              tabindex="0"
            >
              <settings_rigcontrol />
            </div>

            <div
              class="tab-pane fade"
              id="modem"
              role="tabpanel"
              aria-labelledby="modem-tab"
              tabindex="0"
            >
              <settings_modem />
            </div>
            <div
              class="tab-pane fade"
              id="web"
              role="tabpanel"
              aria-labelledby="web-tab"
              tabindex="0"
            >
              <settings_web />
            </div>
            <div
              class="tab-pane fade"
              id="experiments"
              role="tabpanel"
              aria-labelledby="experiments-tab"
              tabindex="0"
            >
              <settings_exp />
            </div>
            <div
              class="tab-pane fade"
              id="url"
              role="tabpanel"
              aria-labelledby="url-tab"
              tabindex="0"
            >
              <settings_url />
            </div>
          </div>
        </div>
      </div>
    </div>
</template>
<script>
import settings_station from "./settings_station.vue";
import settings_gui from "./settings_gui.vue";
import settings_chat from "./settings_chat.vue";
import settings_rigcontrol from "./settings_rigcontrol.vue";
import settings_modem from "./settings_modem.vue";
import settings_web from "./settings_web.vue";
import settings_exp from "./settings_exp.vue";
import settings_url from "./settings_url.vue";



export default {
  components: {
    settings_station,
    settings_gui,
    settings_chat,
    settings_rigcontrol,
    settings_modem,
    settings_web,
    settings_exp,
    settings_url
  },
};



</script>