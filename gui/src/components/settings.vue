<script setup lang="ts">
import settings_gui from "./settings_gui.vue";
import settings_chat from "./settings_chat.vue";
import settings_hamlib from "./settings_hamlib.vue";
import settings_modem from "./settings_modem.vue";
import settings_web from "./settings_web.vue";
import settings_exp from "./settings_exp.vue";
</script>
<template>
  <div
    class="tab-pane fade"
    id="list-settings"
    role="tabpanel"
    aria-labelledby="list-settings-list"
  >
    <div class="container">
      <div class="badge text-bg-warning m-1">
      <h5>
        <i class="bi bi-exclamation-triangle"></i> Please restart the modem
        after changing settings <i class="bi bi-exclamation-triangle"></i>
      </h5>
      </div>


      <div class="card text-center">
  <div class="card-header">

      <!-- SETTINGS Nav tabs -->
      <ul class="nav nav-tabs card-header-tabs" id="myTab" role="tablist">
        <li class="nav-item" role="presentation">
          <button
            class="nav-link active"
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
            id="hamlib-tab"
            data-bs-toggle="tab"
            data-bs-target="#hamlib"
            type="button"
            role="tab"
            aria-controls="profile"
            aria-selected="false"
          >
            Hamlib
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
      </ul>

  </div>
  <div class="card-body">


      <!-- SETTINGS Nav Tab panes -->
      <div class="tab-content">
        <!-- GUI tab contents-->
        <div
          class="tab-pane active"
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
          id="hamlib"
          role="tabpanel"
          aria-labelledby="hamlib-tab"
          tabindex="0"
        >
          <settings_hamlib />
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
      </div>





  </div>
</div>



    </div>
  </div>
</template>
