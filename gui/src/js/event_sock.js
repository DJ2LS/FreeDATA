import {
  eventDispatcher,
  stateDispatcher,
  connectionFailed,
} from "../js/eventHandler.js";
import { addDataToWaterfall } from "../js/waterfallHandler.js";

// ----------------- init pinia stores -------------
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useSettingsStore } from "../store/settingsStore.js";
const settings = useSettingsStore(pinia);

function connect(endpoint, dispatcher) {
  let socket = new WebSocket(
    "ws://" + settings.modem_host + ":" + settings.modem_port + "/" + endpoint,
  );

  // handle opening
  socket.addEventListener("open", function (event) {
    console.log("Connected to the WebSocket server: " + endpoint);
  });

  // handle data
  socket.addEventListener("message", function (event) {
    dispatcher(event.data);
  });

  // handle errors
  socket.addEventListener("error", function (event) {
    console.error("WebSocket error:", event);
    connectionFailed(endpoint, event);
  });

  // handle closing and reconnect
  socket.addEventListener("close", function (event) {
    console.log("WebSocket connection closed:", event.code);

    // Reconnect handler
    if (!event.wasClean) {
      setTimeout(() => {
        console.log("Reconnecting to websocket");
        connect(endpoint, dispatcher);
      }, 1000);
    }
  });
}

// Initial connection attempts to endpoints
connect("states", stateDispatcher);
connect("events", eventDispatcher);
connect("fft", addDataToWaterfall);
