import {
  eventDispatcher,
  stateDispatcher,
  connectionFailed,
  loadAllData,
} from "../js/eventHandler.js";
import { addDataToWaterfall } from "../js/waterfallHandler.js";

// ----------------- init pinia stores -------------
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

function connect(endpoint, dispatcher) {
  const { protocol, hostname, port } = window.location;
  const wsProtocol = protocol === "https:" ? "wss:" : "ws:";
  const adjustedPort = port === '8080' ? '5000' : port;
  const socket = new WebSocket(
    `${wsProtocol}//${hostname}:${adjustedPort}/${endpoint}`
  );

  // handle opening
  socket.addEventListener("open", function () {
    console.log(`Connected to the WebSocket server: ${endpoint}`);
    // when connected again, initially load all data from server
    loadAllData();
  });

  // handle data
  socket.addEventListener("message", function (event) {
    dispatcher(event.data);
  });

  // handle errors
  socket.addEventListener("error", function (event) {
    connectionFailed(endpoint, event);
  });

  // handle closing and reconnect
  socket.addEventListener("close", function (event) {
    console.log(`WebSocket connection closed: ${event.code}`);

    // Reconnect handler
    setTimeout(() => {
      connect(endpoint, dispatcher);
    }, 1000);
  });
}

// Initial connection attempts to endpoints
export function initConnections() {
  connect("states", stateDispatcher);
  connect("events", eventDispatcher);
  connect("fft", addDataToWaterfall);
}
