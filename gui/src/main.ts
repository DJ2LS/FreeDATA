import { createApp } from "vue";
import { createPinia } from "pinia";
import { loadSettings } from "./js/settingsHandler";
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
const tooltipList = [...tooltipTriggerList].map(
  (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl),
);

loadSettings();

//import './js/settingsHandler.js'
import "./js/daemon";
import "./js/sock.js";
//import './js/settingsHandler.js'
