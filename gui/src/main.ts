import { createApp } from "vue";
import { createPinia } from "pinia";
import "./styles.css";
import { Chart, Filler } from "chart.js";
// Register the Filler plugin globally
Chart.register(Filler);

// Import our custom CSS
//import './scss/styles.scss'

import App from "./App.vue";
const app = createApp(App);
//.mount('#app').$nextTick(() => postMessage({ payload: 'removeLoading' }, '*'))
const pinia = createPinia();
app.mount("#app");
app.use(pinia);

// Import all of Bootstrap's JS
//import * as bootstrap from 'bootstrap'

import * as bootstrap from "bootstrap";
import "bootstrap/dist/css/bootstrap.css";
import "bootstrap-icons/font/bootstrap-icons.css";
const tooltipTriggerList = document.querySelectorAll(
  '[data-bs-toggle="tooltip"]',
);
// @ts-expect-error
const tooltipList = [...tooltipTriggerList].map(
  (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl),
);

import { getRemote } from "./store/settingsStore";
import { initConnections } from "./js/event_sock.js";
import { getModemState } from "./js/api";
import { loadAudioDevices, loadSerialDevices } from "./js/deviceFormHelper.ts";


getRemote().then(() => {
  initConnections();
  loadAudioDevices();
  loadSerialDevices();
  getModemState();
});
