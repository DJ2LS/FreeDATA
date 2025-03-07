import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import i18next from "./js/i18n";
import I18NextVue from "i18next-vue";

import { Chart, Filler } from "chart.js";
import { getRemote, settingsStore as settings } from "./store/settingsStore";
import { initConnections } from "./js/event_sock.js";
import { getModemState } from "./js/api";

// Register the Filler plugin globally
Chart.register(Filler);

// Create the Vue app
const app = createApp(App);

app.use(I18NextVue, { i18next });

// Create and use the Pinia store
const pinia = createPinia();
app.use(pinia);

// Mount the app
app.mount("#app");

// Initialize settings and connections
getRemote().then(() => {
  initConnections();
  getModemState();
  // Update the i18next language based on the stored settings
  i18next.changeLanguage(settings.local.language);
});
