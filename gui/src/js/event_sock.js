import { eventDispatcher } from "../js/eventHandler.js";
import { addDataToWaterfall } from "../js/waterfallHandler.js";

function connect(endpoint, dispatcher) {
  let socket = new WebSocket("ws://localhost:5000/" + endpoint);

  // handle opening
  socket.addEventListener("open", function (event) {
    console.log("Connected to the WebSocket server: " + endpoint);
    retries = 0; // Reset the retries back to 0 since the connection was successful
  });

  // handle data
  socket.addEventListener("message", function (event) {
    dispatcher(event.data);
  });

  // handle errors
  socket.addEventListener("error", function (event) {
    console.error("WebSocket error:", event);
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
connect("events", eventDispatcher);
connect("fft", addDataToWaterfall);
