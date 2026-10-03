import { createApp } from "vue";
import App from "./App.vue";
import i18next from "./js/i18n";
import I18NextVue from "i18next-vue";

import { Chart, Filler } from "chart.js";
// Shared Pinia instance, also used by the modules in src/js
import pinia from "./store/index";
import { getRemote, settingsStore as settings } from "./store/settingsStore";
import { initConnections } from "./js/event_sock.js";
import { applyColorMode } from "./js/freedata.js";

// Register the Filler plugin globally
Chart.register(Filler);

// Create the Vue app
const app = createApp(App);

app.use(I18NextVue, { i18next });

// Use the shared Pinia store
app.use(pinia);

// Mount the app
app.mount("#app");

// Apply local (browser) settings right away, they do not depend on the server
// Update the i18next language based on the stored settings
i18next.changeLanguage(settings.local.language);

//Apply Color Mode to gui
applyColorMode(settings.local.colormode);

// Load the server config, then open the WebSockets. Opening the states
// socket triggers loadAllData(), which also fetches the modem state.
getRemote().finally(() => {
  initConnections();
});
