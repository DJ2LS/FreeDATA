import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";

import { Chart, Filler } from "chart.js";
import { getRemote } from "./store/settingsStore";
import { initConnections } from "./js/event_sock.js";
import { getModemState } from "./js/api";

// Register the Filler plugin globally
Chart.register(Filler);

// Create the Vue app
const app = createApp(App);

// Create and use Pinia store
const pinia = createPinia();
app.use(pinia);

// Mount the app
app.mount("#app");

// Initialize settings and connections
getRemote().then(() => {
  initConnections();
  getModemState();
});
