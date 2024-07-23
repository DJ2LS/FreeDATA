import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import "./styles.css"; // Import global styles
//import * as bootstrap from "bootstrap";
import "bootstrap/dist/css/bootstrap.css";
import "bootstrap-icons/font/bootstrap-icons.css";
//import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import * as bootstrap from 'bootstrap/dist/js/bootstrap.esm.min.js'

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

// Initialize Bootstrap tooltips
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
[...tooltipTriggerList].map(
  (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl)
);

// Initialize settings and connections

getRemote().then(() => {
  initConnections();
  getModemState();
});
