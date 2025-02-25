import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import i18n from './js/i18n'

import { Chart, Filler } from "chart.js";
import { getRemote, settingsStore as settings } from "./store/settingsStore";
import { initConnections } from "./js/event_sock.js";
import { getModemState } from "./js/api";

// Register the Filler plugin globally
Chart.register(Filler);

// Create the Vue app
const app = createApp(App);

// use i18n
app.use(i18n)

// Create and use Pinia store
const pinia = createPinia();
app.use(pinia);

// Mount the app
app.mount("#app");

// Initialize settings and connections
getRemote().then(() => {
  initConnections();
  getModemState();
  //console.log(settings.local)
  //console.log(settings.local.language)

  //let language = JSON.parse(settings.local.getItem("language")) || 'en';
  i18n.global.locale = settings.local.language;

});
